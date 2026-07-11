#!/usr/bin/env python3
"""
Worker job-runner for the competitive-analysis web app.

Takes a job spec (the web form's answers), builds a headless prompt, and drives
the `competitive-analysis-decomposed` skill via `claude -p`. While the pipeline
runs, it watches the run directory's artifact files and writes a status.json the
frontend can poll.

This is the dev container-side worker. It assumes:
  - `claude` CLI is installed and authenticated (your internal CLI wrapper, if any)
  - internal MCP tools (internal-slack-search, internal-data-warehouse, google-docs) are reachable
  - it runs as root inside a sandboxed container  -> IS_SANDBOX=1 is required

Usage:
  # Run a job end-to-end (blocks until the pipeline finishes):
  python run_job.py --spec job.json [--workdir DIR] [--model MODEL]

  # Print the prompt that would be sent, without launching claude:
  python run_job.py --spec job.json --dry-run

  # Print current status of an existing run dir (artifact-derived) and exit:
  python run_job.py --status-only /path/to/reports/<slug>-<date>

Job spec (JSON) -- maps 1:1 to the web form fields:
  {
    "topic":       "consumer password managers",   # required
    "lens":        "Consumer / viewer-facing",      # optional, default consumer
    "reference_materials": "",                       # optional: pasted text / GDoc URL / file path
    "competitors": ["1Password", "Bitwarden"],       # list, or "suggest" to let the skill pick
    "dimensions":  ["Product features & feature parity", "Pricing & monetization models"],
    "depth":       "Quick scan",                     # Quick scan | Standard | Deep dive
    "publish_gdoc": false                            # publish 04-report.md to a Google Doc
  }
"""

import argparse
import datetime as dt
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

# Ordered pipeline artifacts. The "label" describes what is running while that
# artifact is still ABSENT (i.e. the stage that produces it). A run dir's current
# stage = the first artifact in this list that does not yet exist.
PIPELINE = [
    ("00-config.md",         "scoping",       10),
    ("01-research-notes.md", "researching",   30),
    ("02-verified.md",       "verifying",     55),
    ("03-synthesis.md",      "synthesizing",  75),
    ("04-report.md",         "writing",       92),
]
DEFAULT_MODEL = "claude-opus-4-8"


def slugify(text: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return s or "analysis"


def build_prompt(spec: dict, run_dir: Path) -> str:
    """Construct the headless prompt. This IS the contract between the form and
    the worker: every form field becomes a pre-supplied intake answer so the
    skill never needs to call AskUserQuestion (there is no human in headless)."""
    topic = spec["topic"]
    lens = spec.get("lens") or "Consumer / viewer-facing (end-user experience)"
    refs = (spec.get("reference_materials") or "").strip()
    depth = spec.get("depth") or "Quick scan"
    publish = bool(spec.get("publish_gdoc"))

    competitors = spec.get("competitors")
    if isinstance(competitors, list) and competitors:
        comp_line = ", ".join(competitors)
    else:
        comp_line = ("suggest -- run a discovery pass, pick the top 4-6 players "
                     "yourself, list them at the top of the report, and proceed "
                     "WITHOUT asking for confirmation (headless run)")

    dims = spec.get("dimensions")
    if isinstance(dims, list) and dims:
        dims_line = "; ".join(dims)
    else:
        dims_line = "all relevant dimensions (you choose, ranked by relevance to the topic)"

    refs_line = refs if refs else "none -- research from scratch"

    if publish:
        end_instr = ("After 04-report.md, publish it to a Google Doc via the "
                     "doc-format-review skill and print the shareable link.")
    else:
        end_instr = "STOP after writing 04-report.md. Do NOT publish to a Google Doc."

    return f"""Invoke the competitive-analysis-decomposed skill to run a competitive analysis. This is a NON-INTERACTIVE headless run: do NOT ask any clarifying questions and do NOT call AskUserQuestion. All intake answers are pre-supplied below -- treat them as the user's answers and proceed straight through the pipeline.

USE THIS EXACT RUN DIRECTORY (it already exists -- write all artifacts here, do not create a differently-named one):
{run_dir}

INTAKE ANSWERS (pre-supplied):
- Topic: {topic}
- Lens / perspective: {lens}
- Reference materials: {refs_line}
- Competitors: {comp_line}
- Dimensions: {dims_line}
- Depth: {depth}

RUN INSTRUCTIONS:
- Write 00-config.md into the run directory above, then proceed through the pipeline: competitive-research -> competitive-verify -> competitive-synthesis -> memo-writing.
- Honor the depth setting for query volume. For internal company sources (internal-slack-search, internal-data-warehouse), a quick check is fine; "nothing found" is an acceptable result -- do not belabor them if the topic is unlikely to appear internally.
- The verification gate is mandatory: 02-verified.md must exist (with verdict tags) before synthesis. Do not skip it.
- {end_instr}
- At the very end, print a one-line summary of which artifact files were created.
"""


def compute_status(run_dir: Path, *, finished: bool = False, exit_code=None,
                   error: str = None, result_meta: dict = None) -> dict:
    """Derive a status dict from which artifact files exist in the run dir."""
    present = {name: (run_dir / name).exists() for name, _, _ in PIPELINE}

    stage, pct = "starting", 5
    for name, label, p in PIPELINE:
        if not present[name]:
            stage, pct = label, p
            break
    else:
        stage, pct = "complete", 100

    state = "running"
    if error:
        state, stage = "error", stage
    elif finished:
        if present["04-report.md"]:
            state, stage, pct = "complete", "complete", 100
        else:
            # process ended but no report -> failure (e.g. silent root/sandbox exit)
            state = "error"
            error = error or "Pipeline ended before 04-report.md was written -- see run.log"

    status = {
        "state": state,                # running | complete | error
        "stage": stage,                # human label of current/last stage
        "percent": pct,
        "artifacts": present,
        "run_dir": str(run_dir),
        "updated_at": dt.datetime.now().isoformat(timespec="seconds"),
    }
    if exit_code is not None:
        status["exit_code"] = exit_code
    if error:
        status["error"] = error
    if result_meta:
        status["result"] = result_meta
    return status


def write_status(run_dir: Path, status: dict) -> None:
    tmp = run_dir / ".status.json.tmp"
    tmp.write_text(json.dumps(status, indent=2))
    tmp.replace(run_dir / "status.json")


def parse_result_meta(log_path: Path) -> dict:
    """Pull cost/turns/duration from the final stream-json result event, if present."""
    if not log_path.exists():
        return {}
    meta = {}
    try:
        for line in log_path.read_text(errors="replace").splitlines():
            line = line.strip()
            if '"type":"result"' in line or '"subtype":"success"' in line:
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue
                for k in ("total_cost_usd", "num_turns", "duration_ms", "is_error", "subtype"):
                    if k in obj:
                        meta[k] = obj[k]
    except OSError:
        pass
    return meta


def run(spec: dict, workdir: Path, model: str) -> int:
    topic = spec["topic"]
    today = dt.date.today().isoformat()
    run_dir = workdir / "reports" / f"{slugify(topic)}-{today}"
    run_dir.mkdir(parents=True, exist_ok=True)

    # Persist the job spec and the exact prompt for traceability.
    (run_dir / "job.json").write_text(json.dumps(spec, indent=2))
    prompt = build_prompt(spec, run_dir)
    (run_dir / "prompt.txt").write_text(prompt)

    log_path = run_dir / "run.log"
    write_status(run_dir, compute_status(run_dir))

    env = dict(os.environ)
    env["IS_SANDBOX"] = "1"  # REQUIRED: claude refuses bypassPermissions as root without this

    cmd = [
        "claude", "-p", prompt,
        "--permission-mode", "bypassPermissions",
        "--output-format", "stream-json",
        "--verbose",
        "--model", model,
    ]

    print(f"[worker] run_dir = {run_dir}", file=sys.stderr)
    print(f"[worker] launching: claude -p (model={model})", file=sys.stderr)
    with open(log_path, "w") as logf:
        proc = subprocess.Popen(cmd, cwd=str(workdir), env=env,
                                stdout=logf, stderr=subprocess.STDOUT)
        # Poll artifacts while the pipeline runs.
        while proc.poll() is None:
            write_status(run_dir, compute_status(run_dir))
            time.sleep(3)
        exit_code = proc.returncode

    result_meta = parse_result_meta(log_path)
    final = compute_status(run_dir, finished=True, exit_code=exit_code,
                           result_meta=result_meta)
    # Surface the known root/sandbox failure mode explicitly.
    if final["state"] == "error":
        try:
            tail = log_path.read_text(errors="replace")[-2000:]
            if "cannot be used with root" in tail:
                final["error"] = ("claude refused bypassPermissions as root -- "
                                  "set IS_SANDBOX=1 (worker should already do this)")
        except OSError:
            pass
    write_status(run_dir, final)

    print(f"[worker] done: state={final['state']} stage={final['stage']} "
          f"exit={exit_code}", file=sys.stderr)
    if result_meta:
        print(f"[worker] cost=${result_meta.get('total_cost_usd')} "
              f"turns={result_meta.get('num_turns')} "
              f"duration_ms={result_meta.get('duration_ms')}", file=sys.stderr)
    print(json.dumps(final, indent=2))
    return 0 if final["state"] == "complete" else 1


def main():
    ap = argparse.ArgumentParser(description="Competitive-analysis worker job-runner")
    ap.add_argument("--spec", help="path to job spec JSON")
    ap.add_argument("--workdir", default=".", help="base dir; runs go in <workdir>/reports/")
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--dry-run", action="store_true", help="print the prompt and exit")
    ap.add_argument("--status-only", metavar="RUN_DIR",
                    help="print artifact-derived status of an existing run dir and exit")
    args = ap.parse_args()

    if args.status_only:
        rd = Path(args.status_only).resolve()
        if not rd.exists():
            print(json.dumps({"state": "error", "error": "run dir not found"}))
            return 1
        print(json.dumps(compute_status(rd, finished=True), indent=2))
        return 0

    if not args.spec:
        ap.error("--spec is required unless --status-only is used")
    spec = json.loads(Path(args.spec).read_text())
    if not spec.get("topic"):
        ap.error("job spec must include a non-empty 'topic'")

    if args.dry_run:
        workdir = Path(args.workdir).resolve()
        today = dt.date.today().isoformat()
        run_dir = workdir / "reports" / f"{slugify(spec['topic'])}-{today}"
        print(build_prompt(spec, run_dir))
        return 0

    return run(spec, Path(args.workdir).resolve(), args.model)


if __name__ == "__main__":
    sys.exit(main())
