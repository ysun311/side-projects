---
name: competitive-analysis
description: Runs a structured competitive analysis on any topic. Asks clarifying questions, researches across all available sources, and produces a verified markdown report with optional Google Doc publish.
---

# Competitive Analysis Skill

## Overview

This skill produces a rigorous, citation-verified competitive analysis report. It asks step-by-step clarifying questions, runs parallel research across 5 source types, applies a mandatory trust/accuracy protocol, and saves a structured markdown report.

**Trust is the #1 priority.** Every claim must be traceable to a verified source. Hallucination prevention steps are mandatory, not optional.

---

## Tool Operational Notes (read before invoking)

These are friction points learned from prior runs. Apply them up-front to avoid re-discovering them mid-flow.

### AskUserQuestion
- The `questions` parameter must be a **JSON array** (object literal), not a string. If you pass `"[{...}]"` as a stringified JSON it will error with `InputValidationError: type expected as 'array' but provided as 'string'`. Always pass it as a real array.
- Avoid em-dashes or unescaped Unicode in option labels; if you see encoding errors, plain ASCII first.

### internal-slack-search / internal-wiki-search (your internal MCP tools)
- **`namespace` is required** (`"slack"` or `"manuals"` respectively). Omitting it errors with `'namespace' is a required property`.
- **Default `size` to 3–5 for broad queries.** Larger sizes (e.g., 10) on broad terms like "microdrama" can return >100K characters and overflow the context window — the result will be saved to a file and you'll need to grep it.
- If a result is too large, the runtime will tell you the file path. Use `grep -iE "term1|term2"` on that file rather than reading it whole.

### Reading PDFs
- The `Read` tool natively handles PDFs and returns page-by-page extracted text plus screenshots. For large reports (3+ PDFs in parallel), prefer reading in a single batch — it's fast.
- Page counts via `pdfinfo` sometimes return blank in this environment. Don't gate on page count — just `Read` the file.

### Google Docs (for GDoc references)
- WebFetch will fail on authenticated Google Docs (returns the sign-in page). Use the `google-docs` skill or call `python /root/.claude/skills/google-docs/scripts/read_doc.py <doc_id>` directly.
- For publishing reports, use `python /root/.claude/skills/google-docs/scripts/create_doc.py`. To update an existing doc in place (preserve URL), use `update_doc.py --id <doc_id> --file <md>`.

### Markdown patterns that break the google-docs converter — fix BEFORE publishing

**Root cause:** the converter computes text-range positions using **byte offsets where it needs character offsets**. Any multi-byte UTF-8 character before a bold span or link contributes (byte_count − 1) bytes of cumulative drift. By the bottom of a doc with many em-dashes, link-text and bold-span end-positions are off by ~3 characters per em-dash before them, producing rendered output like `**Bold sentenc**e` (bold-end shifted) or `[Link tex](url)t` (link-end shifted).

**Always run the fix script before publishing:**

```bash
python /root/.claude/skills/competitive-analysis/fix_md_for_gdoc.py SOURCE.md OUT.md
python /root/.claude/skills/google-docs/scripts/update_doc.py --id ID --file OUT.md
```

The script does the following transforms (in order):

1. **Strip multi-byte UTF-8 characters** — the root cause. `—` → `--`, `–` → `-`, `×` → `x`, `→` → `->`, `★` → `*`, and traffic-light emoji to `[G]/[Y]/[R]`. Eliminates the drift entirely.
2. **Strip `> blockquote` prefixes** — don't render as a box anyway.
3. **Convert `- **X:**` and `- **X.** Y` bullets** to `- **X** -- Y` (avoids bold-bleed on colon/period-ending bullets).
4. **Add `-- ` separator after `- **X** Y`** bullets that have no separator (avoids bold-bleed).
5. **Rewrite `- [Text](url) ...` bullets** to `- Text ([link](url)) ...` (avoids leading-`[` bullet bug).
6. **Convert `**X.** Y` standalone-paragraph leads** to `**X** -- Y` (avoids setext-H1 promotion).
7. **Replace `[Foo (Bar)](url)`** → `[Foo, Bar](url)` (parens inside link text).
8. **Inject blank line** between a bullet block and any following non-bullet paragraph.

**Always read back the published doc** with `read_doc.py` and spot-check the bottom sections (Sources, Next Steps), since drift accumulates downward. If anything still looks broken, find the multi-byte char that escaped the strip pass and add it to the script.

**Cosmetic trade-off:** the doc loses em-dash typography in favor of `--`. Acceptable until the converter is fixed upstream.

### Tool result size limits
- Any tool result over ~100K characters gets saved to a file with instructions to read in chunks. Plan around it: prefer narrower, more targeted queries.

---

## Step 1 — Ask Clarifying Questions (in sequence, one at a time)

Ask each question and wait for the user's answer before proceeding to the next. Every question has a skip option.

### Question 1: Topic
> "What space or product area are you analyzing? (e.g., podcasts, multi-view streaming, password sharing, ad-supported tiers)"

- Free text. No skip needed — this is required to proceed.

### Question 1b: Lens / Perspective
> "What angle are you analyzing from? This helps me focus the research on the right features and audience."

Present these options (adapt the list if the topic clearly implies a lens, e.g., "enterprise SaaS" → skip consumer options):
1. **Consumer / viewer-facing** — features and experience for end users watching or consuming content
2. **Creator / production tooling** — tools for people making or publishing content
3. **B2B / platform / enterprise** — capabilities sold to businesses or partners
4. **Infrastructure & underlying tech** — backend systems, architecture, APIs
5. **Business model & monetization** — pricing, revenue strategy, packaging
6. **Other** — describe your angle

- If user picks one: use it as the lens throughout the entire analysis — filter all research, competitor profiles, and the comparison matrix through that perspective.
- If user skips: default to **consumer / viewer-facing** and state that assumption at the top of the report.
- **This lens is the most important scoping decision in the skill. Apply it strictly.** If the lens is "consumer / viewer-facing," do not include creator tools, production workflows, or B2B features anywhere in the report — even if they're prominent in a competitor's marketing.

### Question 2: Reference Materials
> "Do you have any reference materials you'd like me to use? You can:"
> - **Paste text** — paste an outline, prior research, or notes directly here
> - **Share a Google Doc URL** — I'll fetch the full content
> - **Provide a file path** — if you have a PDF or file on your dev container (e.g., `/root/reports/deloitte-2025.pdf`), I'll read it
> - **Skip** — I'll research from scratch

- If the user provides a GDoc URL: use `WebFetch` to retrieve it, or the `google-docs` skill if WebFetch fails. Read the full content before proceeding.
- If the user provides a file path: use the `Read` tool to read the file (supports PDF natively).
- If the user pastes text: treat it as primary context — reference it explicitly in the report where relevant.
- If materials are provided: incorporate them into the analysis. Note in the report which sections were informed by user-supplied materials (labeled `[User-supplied]`).

### Question 3: Competitors
> "Do you have specific competitors in mind? List them, or say 'suggest some' and I'll research the space first."

- If the user provides names: use them as the competitor list.
- If the user says "suggest" or skips: run a **competitor discovery pass** (see below) and present a suggested list for the user to confirm, remove, or add to before proceeding.

**Competitor discovery pass:**
- WebSearch: "[topic] top competitors 2024 2025"
- WebSearch: "[topic] market landscape players"
- Review results and propose 4–6 competitors with a one-line rationale for each.
- Ask: "Does this list look right? Add, remove, or confirm."

### Question 4: Dimensions
> "Which angles do you want to focus on? I've ranked these by likely relevance to your topic — pick any, pick all, or type your own."

Present all 10 dimensions **ordered by relevance to the topic** (infer from the topic what matters most — e.g., for streaming: content strategy and discovery rank high; for B2B SaaS: pricing and integrations rank high):

1. Product features & feature parity
2. Pricing & monetization models
3. Market positioning & branding
4. Content strategy (editorial voice, originals vs. licensed, formats)
5. Discovery & user experience
6. Distribution & platform reach
7. Partnerships & ecosystem
8. Market share & growth signals
9. Strategic fit — how central is this to the company's overall strategy? (core, ancillary, add-on)
10. Geographic & international expansion
11. Other — type your own

- User can pick one, many, or all.
- If user skips / says "all": cover all 10.

### Question 5: Depth
> "How thorough should the research be?"
> - **Quick scan** — all 5 sources, light depth. 1–2 queries per competitor, top-line findings only. Best for a fast orientation.
> - **Standard** — all 5 sources, balanced depth. 3–5 queries per competitor. Good for most analyses.
> - **Deep dive** — all 5 sources, exhaustive. Full citation verification pass on every claim. Expect longer runtime.

---

## Step 2 — Research Phase

Run research **in parallel across all 5 source types** for each competitor. Do not wait for one source to finish before starting the next.

### Source 1: Web Search
- Search for each competitor separately.
- **Always include the lens in your queries.** If the lens is "consumer / viewer-facing," use terms like "user experience," "viewer features," "watch experience" — not "creator tools," "publisher dashboard," or "production workflow."
- Queries per competitor:
  - Quick scan: 1–2 (e.g., "[competitor] [topic] [lens] 2025", "[competitor] [lens] features")
  - Standard: 3–5 (add pricing, strategy, recent launches — all filtered through the lens)
  - Deep dive: 6+ (add earnings, analyst coverage, job postings as signals)
- **Use search results only to find URLs. Never use the search snippet as the data source.**
- Always prefer results from the most recent dates. Flag when only older sources are available.

### Source 2: Website Fetch
- Fetch the competitor's product/feature page(s) directly for current positioning.
- Look for: feature descriptions, pricing pages, "what's new" or blog pages.

### Source 3: internal-slack-search
- Query: "[topic] [competitor]" and "[topic] competitive"
- Surfaces past internal company discussions about this space.

### Source 4: internal-wiki-search
- Query: "[topic] competitive analysis" and "[competitor]"
- Surfaces internal frameworks, prior analyses, or strategy docs.

### Source 5: InternalDataWarehouse / Internal Data
- Query for any internal company metrics relevant to benchmarking (engagement, feature usage, etc.).
- Label anything found as `[Internal]` — never give it a false public citation.

---

## Step 3 — Trust & Accuracy Protocol (mandatory at every depth level)

Apply to every factual claim before writing it into the report.

### Rule 1 — Fetch verbatim before writing
For every stat or claim found via web search, WebFetch the actual source URL. Do not write the claim until you have the verbatim text in hand.

### Rule 2 — Classify every source inline
Tag every data point immediately after the claim:
- `[Platform-direct]` — press release, earnings call, official blog
- `[Trade pub]` — The Verge, Deadline, TechCrunch, SportsPro, etc.
- `[Analyst]` — Deloitte, Nielsen, Parks Associates, Omdia, etc.
- `[Internal]` — internal company PRD, strategy doc, competitive audit
- `[Inference/estimate]` — clearly labeled; never presented as data-backed fact

### Rule 3 — Inline citation, same sentence
Format: use a markdown hyperlink so the source is clickable directly on the fact:
`Peacock reported 25% of Olympic viewers used multiview ([NBCU, "Year of Peacock," 2024](https://...)).`
- The source label is the hyperlink text; the URL is the href
- Source type tag goes immediately after: `([Platform-direct](url))`, `([Trade pub](url))`, etc.
- Never defer citations to a sources section — every claim carries its own clickable link

### Rule 4 — Prioritize recency
Always use the most recently dated source available. When only older sources exist, flag: "as of [year] — no more recent data found."

### Rule 5 — Triple verification pass (mandatory, not optional)
After drafting each competitor profile, re-fetch every cited URL and run all 3 checks in sequence:

1. **Presence check**: "Does this article contain [specific claim]?"
2. **Verbatim check**: "Quote the exact sentence or passage that supports this claim."
3. **Accuracy check**: "Does the quoted sentence directly support the claim as written in the report — same number, same context, same meaning?"

All 3 must confirm. If any fail: find the real source, reword with correct attribution, or remove the claim entirely. No exceptions.

### Rule 6 — Data gap honesty
If a competitor doesn't publicly disclose a metric, say so explicitly: "No public data available." Use investment signals (feature expansion, hiring, press coverage) as proxy — and label them as proxy signals, not facts.

Every competitor profile ends with a **"What we couldn't verify"** note listing any gaps.

---

## Step 4 — Write the Report

Use this structure:

```
# Competitive Analysis: [Topic]
*Generated: [date] | Depth: [quick scan / standard / deep dive] | Lens: [chosen lens] | Competitors: [list]*
*Reference materials used: [list files/docs, or "none — researched from scratch"]*

## Executive Summary
2–4 sentences. Lead with the most important finding. What should a busy executive take away?

## Market Landscape
Brief overview of the space: size, dynamics, key trends. Who are the major players and how is the market structured?

## Competitor Profiles
[One section per competitor]

### [Competitor Name]
**Positioning**: How do they describe themselves and differentiate?
**Key features / recent moves**: What are they shipping or investing in?
**[Selected dimensions]**: Findings per dimension the user chose.
**What we couldn't verify**: Any gaps or undisclosed metrics.

## Feature / Dimension Comparison Matrix
A markdown table with competitors as columns and selected dimensions as rows.
Use: ✓ (has it), ~ (partial), ✗ (no), ? (unknown/unverified)

## Gaps & Opportunities
What is no one doing well? Where is there whitespace? What does this mean for your company?

## Sources
Full list of all cited URLs, grouped by competitor.
```

### Writing style rules (from prior session learnings):
- Takeaways: 2–3 sentences max, bold claim first, 1–2 specific data points.
- Don't over-qualify. Lead with the finding, support with evidence.
- One stat, one source — never blend two sources into one sentence.

### Optional style enhancements (reference: an internal competitive teardown you liked):
These patterns improve scannability and executive readability — apply where they fit the topic:

**Key Takeaways block at top**: A bold, prominent summary table before any analysis. Lead with the most important findings as bolded sentences, not bullet headers.

**Traffic light ratings in comparison tables**: Replace ✓/~/✗ with 🟢 Strong / 🟡 Mixed / 🔴 Weak for quicker scanning. Add a one-line rationale next to each rating.

**Standard competitor metadata fields** (add to each profile header):
- Strategic Importance: Core / Ancillary / Add-on (how central is this space to their overall business?)
- Investment Trajectory: Aggressive / Growing / Maintaining / Declining

**Feature tier framing** (useful when analyzing a specific product category):
- Tier 1 — Tablestakes: baseline features listeners expect; they won't credit you for having them but will leave without them
- Tier 2 — Value-Adds: appreciated but not decisive; build stickiness
- Tier 3 — Differentiators: what drives competitive advantage; what sets a player apart

**Consumer-need framing**: Instead of (or in addition to) a pure feature list, evaluate competitors against the key moments/jobs the user is trying to accomplish. Works especially well for consumer products. Example: "Effortless Discovery," "Just Hit Play," "Don't Miss a Drop."

**Market convergence/divergence section** (alternative to Gaps & Opportunities):
- "Where the market is converging" — what all players are doing the same
- "Where the market is diverging" — where strategic bets differ
- "Whitespace" — what no one is doing well

---

## Step 5 — Save the Report

Save to `./reports/[topic-slug]-[YYYY-MM-DD].md` relative to the user's current working directory.

Create the `reports/` directory if it doesn't exist.

Confirm the file path to the user after saving.

---

## Step 6 — Optional Google Doc Publish

After saving, ask:
> "Want me to publish this to a Google Doc for easy sharing?"

- If yes: use the `google-docs` skill to create a new doc, write the report content, and return a shareable link.
- If no: done.

---

## Important Reminders

- Never write a claim without a fetched, verified source.
- Never use a search snippet as a data source — only as a pointer to a URL.
- The triple verification pass is not optional cleanup. It runs on every claim, every time.
- If you're unsure whether a source supports a claim: remove the claim. Accuracy over completeness.
