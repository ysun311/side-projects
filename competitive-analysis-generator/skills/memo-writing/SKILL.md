---
name: memo-writing
description: Rewrites structured content into a concise, confident memo voice — executive-summary-first, high bold-density for scannability, calibrated hedging, strong verbs, disciplined punctuation. Reusable for any memo, synthesis, retrospective, PRD, exec summary, or strategy doc. Use when content needs to read like a sharp human wrote it, not like AI boilerplate.
---

# Memo Writing

## Role

This skill applies a polished memo **voice** to structured content. It is general-purpose — use it for any written deliverable, not just competitive analysis. In the competitive pipeline it reads `03-synthesis.md` and writes `04-report.md`; standalone, point it at any draft or input and produce a polished version.

**Division of labor:** the input owns *what is said and how it's structured*. This skill owns *how the prose reads*. Do not invent new facts, add claims, or drop citations — preserve every inline citation exactly. Tighten, restructure for clarity, and apply voice.

## The style guide is the source of truth

Read `assets/writing-style.md` (bundled alongside this SKILL.md) and apply it. It is the authoritative spec for voice. The points below are the spine; the bundled guide has the full detail and anti-patterns.

This bundled copy makes the skill self-contained and shareable. (If the user maintains a personal override at `/root/.claude/rules/writing-style.md`, that file already applies globally to their own work; the bundled copy is the portable default for teammates and the fallback.)

## Core spine (from the guide)

- **Every word earns its place.** If a sentence can be shorter, make it shorter. Cut any section that doesn't advance the argument, supply evidence, or solicit feedback. Length is earned, never defaulted.
- **Default opening:** a bordered Executive Summary box — proposal, 2–3 supporting bullets, the explicit ask, discussion questions. A senior reader who reads only this should know what you propose, why, and what you want. (Context-first openings are fine for research deep-dives and retrospectives.)
- **Pipe-prefixed section headers:** `# | Section Name`. The visual fingerprint.
- **Restate the ask** 2–3 times (exec summary, recommendation, next steps).
- **Voice:** "We," not "I." Calibrated confidence — state positions ("We believe X"), don't stack qualifiers. Diplomatic but direct; name problems without naming villains. Dry register — no cheerleading, no exclamation marks.
- **Word choice:** "leverage" max once; prefer "use"/"build on." Kill filler ("in order to" -> "to"; drop "it's important to note that"). Strong verbs: Anchor, Modernize, Reassert, Unlock, Cut, Ship, Bet. Cut filler adjectives (cohesive, comprehensive, seamless, robust...) unless concrete.
- **Hedging:** max one hedge per claim. If a claim needs three hedges, it isn't ready.
- **Punctuation:** real em-dashes (cap ~2/paragraph); no hyphens as fake em-dashes; semicolons rare; colons after bolded mini-headers (`**Focus:** ...`) are fine.
- **Formatting:** bold-density as navigation (3–8 bolded phrases/paragraph; a bold-only scan should yield the spine in 30 seconds). Italics for captions/asides/member quotes. Tables for matrix content with atomic cells.
- **Vary sentence cadence.** Medium sentences carry the argument; drop short fragments for emphasis.

## Length budgets (calibrate to type)
- Decision doc / 1-pager: 500–1,500 words
- Retrospective: 1,500–3,000
- Strategy vision: 3,000–5,000
- PRD / requirements: 5,000–10,000 when content demands

If the content needs materially more or less, flag it before drafting rather than silently overshooting.

## Anti-patterns to avoid
Throat-clearing intros ("This memo is intended to provide..."), AI boilerplate (abstract-noun stacking + future-facing infinitive + no commitment), hedge stacking, adjective-as-substance, run-on table cells, passive voice in accountability moments, conclusion-light closings, forced trios.

## Output
Write the polished result to the target path (`04-report.md` in the competitive pipeline, or wherever the user specifies). Preserve all citations and the document's factual content; change only the prose and arrangement.
