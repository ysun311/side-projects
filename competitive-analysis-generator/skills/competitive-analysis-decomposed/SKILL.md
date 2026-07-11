---
name: competitive-analysis-decomposed
description: Orchestrates a structured competitive analysis as a decomposed pipeline. Handles intake and scoping, then sequences research -> verify -> synthesis -> write -> publish across focused sub-skills, enforcing a mandatory verification gate. Use when the user wants a competitive analysis, market scan, or competitor teardown on any topic.
---

# Competitive Analysis (Decomposed Orchestrator)

## What this skill is

This is the **orchestrator** for a multi-stage competitive analysis. It does NOT do research, verification, synthesis, writing, or formatting itself. It scopes the work, then sequences five focused sub-skills, each of which reads and writes a known file in a per-run directory.

**Trust is the #1 priority.** The verification stage is a hard gate, not optional cleanup. See "The Gate" below.

This is a parallel re-architecture of the original monolithic `competitive-analysis` skill, which is preserved untouched as a rollback path. If this pipeline ever misbehaves, the user can fall back to `/competitive-analysis`.

## The pipeline and its artifact contract

Skills do not call each other deterministically — handoffs are model-mediated and can drop. To make the pipeline robust, **every stage reads a known input file and writes a known output file** in one run directory. You (the orchestrator) create the directory and own the config artifact; you invoke each sub-skill and verify its artifact exists before moving on.

```
./reports/<topic-slug>-<YYYY-MM-DD>/
  00-config.md          YOU write this           (scope of the whole run)
  01-research-notes.md  competitive-research      (sourced notes, not prose)
  02-verified.md        competitive-verify        (triple-verification results)  [HARD GATE]
  03-synthesis.md       competitive-synthesis     (structured analytical draft)
  04-report.md          memo-writing              (polished report in target voice)
  (GDoc link)           doc-format-review         (published + read-back checked)
```

After publish, also copy the final report to `./reports/<topic-slug>-<YYYY-MM-DD>.md` to preserve the existing flat convention.

## Step 1 — Intake (ask clarifying questions in sequence, one at a time)

Ask each question and wait for the answer before the next. Every question after Topic has a skip option.

**Operational note — AskUserQuestion:** the `questions` parameter must be a real JSON array, not a stringified one (a string errors with `type expected as 'array' but provided as 'string'`). Keep option labels plain ASCII — avoid em-dashes/Unicode in labels.

### Q1 — Topic (required)
"What space or product area are you analyzing?" (e.g., podcasts, multi-view streaming, microdrama, ad-supported tiers). Free text, no skip.

### Q1b — Lens / Perspective
"What angle are you analyzing from?" Present, adapting if the topic implies a lens:
1. Consumer / viewer-facing
2. Creator / production tooling
3. B2B / platform / enterprise
4. Infrastructure & underlying tech
5. Business model & monetization
6. Other — describe

If skipped, default to **consumer / viewer-facing** and state that assumption in `00-config.md`. **This is the most important scoping decision** — record it explicitly so every downstream stage filters through it. If the lens is consumer, creator/B2B/infra material must not appear in the report even if prominent in a competitor's marketing.

### Q2 — Reference materials
"Any reference materials I should use? Paste text, share a Google Doc URL, give a file path (PDF/file on dev container), or skip." Record what's provided in `00-config.md` so `competitive-research` knows to ingest them and label findings `[User-supplied]`.

### Q3 — Competitors
"Do you have specific competitors in mind? List them, or say 'suggest some'." If the user wants suggestions, note in `00-config.md` that `competitive-research` should run a discovery pass first and bring back a 4–6 name list for confirmation before deep research.

### Q4 — Dimensions
"Which angles to focus on? Pick any, all, or type your own." Present the 10, ordered by inferred relevance to the topic:
1. Product features & feature parity
2. Pricing & monetization models
3. Market positioning & branding
4. Content strategy
5. Discovery & user experience
6. Distribution & platform reach
7. Partnerships & ecosystem
8. Market share & growth signals
9. Strategic fit (core / ancillary / add-on)
10. Geographic & international expansion
11. Other — type your own

### Q5 — Depth
"How thorough?" — **Quick scan** (1–2 queries/competitor, top-line), **Standard** (3–5 queries/competitor), **Deep dive** (6+, exhaustive verification). All depths use all sources and the full trust protocol; they differ in query depth.

## Step 2 — Write 00-config.md and the active-run marker

Create the run directory `./reports/<topic-slug>-<YYYY-MM-DD>/` and write `00-config.md` capturing: topic, slug, date, lens (+ whether defaulted), reference materials (paths/URLs/pasted-text location), competitor list (or "discovery pass needed"), chosen dimensions, depth. This file is the single source of truth every sub-skill reads.

Then write the **active-run marker** so the verification hook knows exactly which run to guard:

```bash
echo "<absolute path to the run dir>" > ./reports/.active-run
```

(The hook also falls back to scanning `reports/*/` if the marker is missing, so this is belt-and-suspenders, not load-bearing.)

## Step 3 — Sequence the sub-skills

Invoke in order, confirming each artifact exists before the next:

1. **`competitive-research`** — reads `00-config.md`, writes `01-research-notes.md`. (If discovery pass was requested, it will return a competitor list for the user to confirm before going deep — relay that confirmation.)
2. **`competitive-verify`** — reads `01-research-notes.md`, writes `02-verified.md`.
3. **`competitive-synthesis`** — reads `02-verified.md`, writes `03-synthesis.md`.
4. **`memo-writing`** — reads `03-synthesis.md`, writes `04-report.md`.
5. **`doc-format-review`** (optional, ask first) — reads `04-report.md`, publishes to GDoc.

## The Gate (mandatory — and hook-enforced)

**Do not invoke `competitive-synthesis` until `02-verified.md` exists in the run directory.** If it is missing, invoke `competitive-verify` first. The synthesis, writing, and publish stages operate ONLY on verified claims.

This is enforced by a **PreToolUse hook** (`hooks/verify_gate.py`, registered in user `settings.json` on the `Skill` matcher), not just by this instruction. If `competitive-synthesis` is invoked while a run has `01-research-notes.md` but no `02-verified.md`, the harness **blocks the call** and returns a message telling you to run `competitive-verify` first. The gate is therefore not skippable even if this prose is ignored. The hook only ever blocks `competitive-synthesis`; `memo-writing` and `doc-format-review` are never gated.

## Step 4 — Save & deliver

After synthesis/writing, the report lives at `04-report.md`. Confirm the path to the user. Then ask: "Want me to publish this to a Google Doc for easy sharing?" If yes, invoke `doc-format-review`. Copy the final report to `./reports/<topic-slug>-<YYYY-MM-DD>.md`.

## Final deliverable expectations

- A verified markdown report where **every claim carries an inline citation that survived the triple-verification pass**.
- A "What we couldn't verify" note per competitor.
- The lens applied strictly throughout.
- Optional clean GDoc publish.

## Running stages standalone

Each sub-skill is independently invocable. A user can run `memo-writing` or `doc-format-review` on any file without the full pipeline. When run inside this pipeline, they use the run-directory artifacts above.
