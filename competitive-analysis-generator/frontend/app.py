"""
Competitive Analysis — web frontend (Posit Connect / Streamlit).

Collects the same answers the `/competitive-analysis-decomposed` skill asks
interactively, writes them to the S3 job bus, and polls for live progress + the
final report. The heavy agent run happens on the dev container worker (s3_poller.py),
NOT here — Posit Connect content cannot run the claude CLI.
"""
import datetime as dt
import re
import time
import uuid

import streamlit as st

import bus

LENSES = [
    "Consumer / viewer-facing",
    "Creator / production tooling",
    "B2B / platform / enterprise",
    "Infrastructure & underlying tech",
    "Business model & monetization",
]
DIMENSIONS = [
    "Product features & feature parity",
    "Pricing & monetization models",
    "Market positioning & branding",
    "Content strategy",
    "Discovery & user experience",
    "Distribution & platform reach",
    "Partnerships & ecosystem",
    "Market share & growth signals",
    "Strategic fit (core / ancillary / add-on)",
    "Geographic & international expansion",
]
DEPTHS = ["Quick scan", "Standard", "Deep dive"]

STAGE_LABELS = {
    "queued": "Queued", "starting": "Starting", "scoping": "Scoping",
    "researching": "Researching across sources", "verifying": "Verifying every claim",
    "synthesizing": "Synthesizing findings", "writing": "Writing the report",
    "complete": "Complete",
}

st.set_page_config(page_title="Competitive Analysis", page_icon="🔎", layout="centered")

# ---- brand theme (swap for your own) ----
st.markdown("""
<style>
:root { --brand-accent:#5B8DEF; --brand-bg:#0b0e14; --brand-card:#151a24; --brand-border:#2b3242; --brand-muted:#a9b2c3; }
.stApp { background:var(--brand-bg); color:#fff; }
header[data-testid="stHeader"] { background:transparent; }
#MainMenu, footer { visibility:hidden; }
h1,h2,h3,h4 { color:#fff; font-family:"Helvetica Neue",Arial,sans-serif; letter-spacing:-.5px; }

/* branded header */
.app-header { display:flex; align-items:center; gap:14px; padding:6px 0 2px; border-bottom:2px solid var(--brand-accent); margin-bottom:22px; }
.app-logo { background:var(--brand-accent); color:#fff; font-weight:800; font-size:26px; width:46px; height:46px;
           border-radius:8px; display:flex; align-items:center; justify-content:center; font-family:"Helvetica Neue",Arial,sans-serif; }
.app-title { font-size:22px; font-weight:700; color:#fff; line-height:1.1; }
.app-sub { font-size:11px; letter-spacing:2px; color:var(--brand-muted); text-transform:uppercase; margin-top:3px; }

/* cards / containers */
[data-testid="stForm"], div[data-testid="stExpander"] {
    background:var(--brand-card); border:1px solid var(--brand-border); border-radius:10px; padding:8px 18px; }

/* buttons -> brand red */
.stButton>button, .stDownloadButton>button, .stFormSubmitButton>button {
    background:var(--brand-accent); color:#fff; border:0; border-radius:6px; font-weight:700; }
.stButton>button:hover, .stDownloadButton>button:hover, .stFormSubmitButton>button:hover {
    background:#4574d6; color:#fff; }

/* text inputs ONLY — never the multiselect/selectbox internal combobox input
   (styling that one drops a stray box that overlaps the first chip) */
.stTextInput input, .stTextArea textarea {
    background:#1a1a1a !important; color:#fff !important; border:1px solid var(--brand-border) !important; }
.stMultiSelect input, [data-baseweb="select"] input {
    background:transparent !important; border:0 !important; box-shadow:none !important; }
.stMultiSelect [data-baseweb="tag"] { background:var(--brand-accent) !important; max-width:none !important; }
.stMultiSelect [data-baseweb="tag"] span { color:#fff !important; max-width:none !important;
    overflow:visible !important; text-overflow:clip !important; white-space:normal !important; }

/* progress bar already uses primaryColor (red); labels white */
.stProgress > div > div > div > div { background:var(--brand-accent); }
a { color:var(--brand-accent); }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="app-header">
  <div class="app-logo">CA</div>
  <div>
    <div class="app-title">Competitive Analysis Generator</div>
    <div class="app-sub">AI-Powered Competitive Research</div>
  </div>
</div>
""", unsafe_allow_html=True)
st.caption("Answer a few questions and get a verified, citation-checked competitive report.")


@st.cache_data(ttl=60)
def bus_reachable():
    """Verify this process's identity can reach the S3 job bus. On Posit Connect
    this confirms the content's AWS identity has access to the bus prefix."""
    try:
        bus.list_jobs()
        return True, None
    except Exception as e:  # surface loudly rather than failing silently on submit
        return False, str(e)


_ok, _err = bus_reachable()
print(f"[startup] bus reachable={_ok} err={_err}")  # shows in app logs
if not _ok:
    st.error(f"Cannot reach the job bus (`s3://{bus.BUCKET}/{bus.PREFIX}`). "
             f"This app's identity may lack S3 access.\n\n```\n{_err}\n```")
    st.stop()


def make_job_id(topic: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", topic.lower()).strip("-") or "analysis"
    return f"{dt.date.today().isoformat()}-{slug}-{uuid.uuid4().hex[:6]}"


# ---- intake form ----
if "job_id" not in st.session_state:
    with st.form("intake"):
        topic = st.text_input("Topic *", placeholder="e.g. microdrama apps, ad-supported tiers")
        lens = st.selectbox("Lens / perspective", LENSES, index=0)
        competitors_raw = st.text_input(
            "Competitors (comma-separated)",
            placeholder="leave blank to let the tool suggest them")
        dimensions = st.multiselect("Dimensions to focus on", DIMENSIONS,
                                    default=DIMENSIONS[:2])
        depth = st.radio("Depth", DEPTHS, index=0, horizontal=True,
                         help="Quick scan ~5 min / ~$2. Deep dive is much longer.")
        refs = st.text_area("Reference materials (optional)",
                            placeholder="paste notes, a Google Doc URL, or a file path")
        publish = st.checkbox("Publish result to a Google Doc")
        submitted = st.form_submit_button("Run analysis", type="primary")

    if submitted:
        if not topic.strip():
            st.error("Topic is required.")
            st.stop()
        competitors = [c.strip() for c in competitors_raw.split(",") if c.strip()] or "suggest"
        spec = {
            "topic": topic.strip(),
            "lens": lens,
            "reference_materials": refs.strip(),
            "competitors": competitors,
            "dimensions": dimensions or [],
            "depth": depth,
            "publish_gdoc": publish,
        }
        job_id = make_job_id(topic)
        bus.submit_job(job_id, spec)
        st.session_state.job_id = job_id
        st.rerun()

# ---- progress / result ----
else:
    job_id = st.session_state.job_id
    st.write(f"**Job:** `{job_id}`")
    status = bus.get_status(job_id) or {"state": "queued", "stage": "queued", "percent": 0}
    state = status.get("state")
    stage = status.get("stage", "")
    pct = status.get("percent", 0)

    if state == "complete":
        st.success("Analysis complete.")
        meta = status.get("result", {})
        if meta:
            st.caption(f"~${meta.get('total_cost_usd', '?'):.2f} · "
                       f"{meta.get('num_turns', '?')} turns · "
                       f"{round(meta.get('duration_ms', 0)/1000)}s")
        report = bus.get_report(job_id)
        if report:
            st.download_button("Download report (.md)", report,
                               file_name=f"{job_id}.md", mime="text/markdown")
            st.markdown(report)
        else:
            st.warning("Report not found in the bus yet — try refreshing.")
        if st.button("Start another analysis"):
            del st.session_state.job_id
            st.rerun()

    elif state == "error":
        st.error(f"Run failed at stage **{stage}**.")
        if status.get("error"):
            st.code(status["error"])
        if st.button("Try again"):
            del st.session_state.job_id
            st.rerun()

    else:
        st.progress(pct / 100, text=STAGE_LABELS.get(stage, stage))
        st.info("Working… verified competitive research takes a few minutes. "
                "This page refreshes automatically.")
        time.sleep(5)
        st.rerun()
