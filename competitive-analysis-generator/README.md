# Competitive Analysis Generator

A [Claude Code](https://claude.com/product/claude-code) skill that automates competitive research and produces structured, citation-checked reports — plus a prototype web app that puts a form in front of it.

## What this is

Ask it about a market or product space, and it runs research across multiple sources, verifies every claim against its original source before including it, and writes a structured markdown report: executive summary, market landscape, per-competitor profiles, a feature/dimension comparison matrix, gaps and opportunities, and sources.

The core idea is a **mandatory triple-verification trust protocol**: every stat or claim is fetched verbatim from its source URL (never taken from a search snippet), classified by source type (platform-direct, trade press, analyst, inference/estimate, etc.), and inline-cited in the same sentence as the claim. Before the report ships, each cited claim is re-checked for presence, verbatim support, and accuracy — claims that fail are reworded or dropped, not left in on good faith.

## Layout

```
skills/
  competitive-analysis/            monolithic version — one skill, full pipeline
  competitive-analysis-decomposed/ orchestrator for the decomposed version
  competitive-research/            research stage: fetch-verbatim, classify, inline-cite
  competitive-verify/              triple-verification pass (the trust gate)
  competitive-synthesis/           findings, comparison matrix, convergence/divergence, gaps
  memo-writing/                    general-purpose voice/style polish (reusable beyond this project)
  doc-format-review/               general-purpose "publish markdown to a doc" QA pass

frontend/    Streamlit web-form prototype (intake form -> job bus -> poll for report)
worker/      headless-CLI worker that actually runs the pipeline and writes results back
prototype/   static HTML mockup of a richer intake UI (not wired up)
docs/        engineering retro from building the web-app prototype
sample-report/  one example report (consumer password managers), so you can see the output
```

## Two ways to run it

**1. As a Claude Code skill (the main artifact).** Copy the `skills/` subdirectories into your own `~/.claude/skills/` and invoke `/competitive-analysis` (monolithic) or `/competitive-analysis-decomposed` (staged pipeline with a hard verification gate) inside Claude Code. It asks a few clarifying questions — topic, competitors, dimensions, depth — and writes the report to `./reports/`.

The decomposed version enforces verification with a `PreToolUse` hook (`competitive-analysis-decomposed/hooks/verify_gate.py`) that physically blocks the synthesis stage from running until a real, verdict-tagged verification pass exists on disk. It fails open on anything it doesn't recognize.

**2. As a headless web app.** `frontend/` is a Streamlit form; `worker/` is a small daemon that polls an S3 "job bus," drives the skill via `claude -p` in headless mode, and writes results back for the frontend to poll. See `docs/webapp-build-retro.md` for the full build story, including the walls we hit (root-permission gotchas, deploy-target constraints, cross-account storage boundaries) and how we got through them. This is a prototype, not a hardened service — see the retro's "What's Left" section for the known gaps (an always-on worker host, a shared credentials/cost model).

To run the web app yourself you'll need to fill in `BUCKET` / `PREFIX` in `worker/bus.py` and `frontend/bus.py` with your own S3 location and have AWS credentials available to both the frontend's and the worker's runtime identity.

## Trust protocol, in short

1. Search finds URLs only — never used as the data source itself.
2. Every claim is fetched verbatim from its source before it's written down.
3. Every claim is tagged by source type inline.
4. Citations are inline, same sentence, never deferred to a footer.
5. Most recent source wins; older-only data is flagged as such.
6. A dedicated verification pass re-fetches every cited URL and checks presence, verbatim support, and accuracy — three separate checks, all three must pass.
7. Every competitor profile ends with a "what we couldn't verify" note rather than silently omitting gaps.

## Status

Built and used for real competitive research; the decomposed pipeline and its verification gate are tested but not yet run through a large volume of real-world reports. The web app prototype works end-to-end under a single identity; the multi-user, always-on version has one known open item (a cross-account storage permissions fix — see the retro).
