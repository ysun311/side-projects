---
name: competitive-research
description: Researches a competitive space across web search, website fetch, internal Slack (internal-slack-search), internal manuals (internal-wiki-search), and internal company data (a data-warehouse query tool). Fetches every claim verbatim from its source URL, classifies and inline-cites it, and outputs sourced research notes (not prose). Use as the research stage of a competitive analysis, or standalone to gather sourced findings on competitors.
---

# Competitive Research

## Role in the pipeline

This is the **research stage**. Input: `00-config.md` (scope written by the orchestrator). Output: `01-research-notes.md` — **sourced notes, not prose.** Do not write narrative analysis or recommendations here; that is synthesis's job. Your job is to gather claims, each one fetched verbatim, classified, and inline-cited, so the verify stage can check them and synthesis can build on them.

If invoked standalone (no `00-config.md`), ask the user for: topic, lens, competitors, dimensions, depth — then proceed the same way.

## Read the config first

Read `00-config.md`. Note the **lens** — it filters every query. If the lens is consumer/viewer-facing, use terms like "user experience," "viewer features," "watch experience" — never "creator tools," "publisher dashboard," "production workflow." If the config says a **discovery pass** is needed, run it first (below) and return a 4–6 competitor list with one-line rationales for the user to confirm before deep research.

**Competitor discovery pass:** WebSearch "[topic] top competitors 2025", "[topic] market landscape players". Propose 4–6 with rationale. Wait for confirmation.

## Research across all 5 sources (in parallel)

Run sources in parallel per competitor — don't wait for one to finish before starting the next.

### Source 1 — Web Search
- Search each competitor separately. **Always fold the lens into the query.**
- Queries per competitor by depth: Quick scan 1–2; Standard 3–5 (add pricing, strategy, recent launches); Deep dive 6+ (add earnings, analyst coverage, job postings as signals).
- **Use search results ONLY to find URLs. Never use the search snippet as the data source.**

### Source 2 — Website Fetch
- Fetch the competitor's product/feature/pricing/"what's new" pages directly for current positioning.

### Source 3 — internal-slack-search (internal company Slack)
- Query "[topic] [competitor]" and "[topic] competitive" to surface past internal discussion.
- **`namespace` is required** (`"slack"`). **Default `size` to 3–5** — large sizes on broad terms can return >100K chars and overflow context. If a result is saved to a file, `grep -iE "term1|term2"` it rather than reading whole.

### Source 4 — internal-wiki-search (internal manuals/docs)
- Query "[topic] competitive analysis" and "[competitor]" for internal frameworks or prior analyses.
- **`namespace` required** (`"manuals"`); same `size` 3–5 guidance.

### Source 5 — InternalDataWarehouse / Internal Data
- Query for internal company metrics relevant to benchmarking. Label anything found `[Internal]` — never give it a false public citation.

## Ingesting user-supplied reference materials
- **GDoc URL:** WebFetch fails on authenticated Google Docs (returns the sign-in page). Use the `google-docs` skill or `python /root/.claude/skills/google-docs/scripts/read_doc.py <doc_id>`.
- **File path / PDF:** use the `Read` tool — it handles PDFs natively (page text + screenshots). For several PDFs, read in one batch. Don't gate on `pdfinfo` page counts (often blank here) — just Read.
- **Pasted text:** treat as primary context. Label findings drawn from these `[User-supplied]`.

## Trust protocol — the parts that live in research

These are mandatory at every depth. (The triple-verification *pass* is a separate stage — `competitive-verify` — but everything below happens here, while sourcing.)

**Rule 1 — Fetch verbatim before writing.** For every stat or claim found via search, `WebFetch` the actual source URL and get the verbatim text in hand. Do not record a claim you have not fetched. Sourcing and fetching are inseparable.

**Rule 2 — Classify every source inline:**
- `[Platform-direct]` — press release, earnings call, official blog
- `[Trade pub]` — The Verge, Deadline, TechCrunch, SportsPro, etc.
- `[Analyst]` — Deloitte, Nielsen, Parks Associates, Omdia, etc.
- `[Internal]` — internal company PRD, strategy doc, competitive audit
- `[User-supplied]` — from materials the user provided
- `[Inference/estimate]` — clearly labeled; never dressed up as data-backed

**Rule 3 — Inline citation, same line as the claim.** Use a clickable markdown link: `Peacock reported 25% of Olympic viewers used multiview ([NBCU, "Year of Peacock," 2024](https://...))`. The label is the link text; the type tag goes right after: `([Trade pub](url))`. Never defer citations to a footer.

**Rule 4 — Prioritize recency.** Always use the most recently dated source. When only older sources exist, flag it: "as of [year] — no more recent data found."

**Rule 6 — Data-gap honesty.** If a competitor doesn't disclose a metric publicly, say "No public data available." Use investment signals (feature expansion, hiring, press) as proxy — labeled as proxy, not fact.

## Output format — 01-research-notes.md

Write notes, organized by competitor, each finding as its own line with the verbatim-backed claim + inline citation + source-type tag + the fetched URL. Include a per-competitor "Open / unverified" list of anything you couldn't fetch cleanly, so verify knows where to focus. Structure:

```
# Research Notes: <topic>  (lens: <lens> | depth: <depth>)

## <Competitor A>
- <claim> ([label](url)) [<type>]  — verbatim quote: "<exact fetched sentence>"
- <claim> ([label](url)) [<type>]  — verbatim quote: "..."
- Open/unverified: <anything that needs a fetch or that no source confirmed>

## <Competitor B>
...

## Cross-cutting / market-level notes
- ...
```

Do not interpret or rank. Hand clean, sourced, quote-backed notes to `competitive-verify`.
