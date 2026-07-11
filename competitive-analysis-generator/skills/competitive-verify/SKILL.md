---
name: competitive-verify
description: Audits factual claims in research notes for source support, recency, and accuracy by re-fetching each cited URL and running a three-check verification pass (presence, verbatim, accuracy). Drops or rewords claims that fail. Use as the verification gate of a competitive analysis, or standalone to fact-check any sourced claim set before it is written up.
---

# Competitive Verify (Trust Gate)

## Role in the pipeline

This is the **verification gate** — the trust crown jewel of the competitive analysis pipeline. Input: `01-research-notes.md`. Output: `02-verified.md`. **No synthesis, writing, or publishing happens until this file exists.** Its job is to re-check every claim against its source so that only verified claims flow downstream.

If invoked standalone, point it at any markdown file of sourced claims; produce the same verified output.

## The triple-verification pass (mandatory, not optional)

For **every** claim in `01-research-notes.md` that carries a citation, re-fetch the cited URL (don't trust the note's earlier fetch — re-fetch fresh) and run all three checks in sequence:

1. **Presence check** — "Does this source contain [the specific claim]?"
2. **Verbatim check** — "Quote the exact sentence or passage that supports this claim."
3. **Accuracy check** — "Does the quoted sentence directly support the claim as written — same number, same context, same meaning?"

**All three must confirm.** If any fails:
- Find the real source that supports it and re-attribute, **or**
- Reword the claim so the source actually supports it, **or**
- **Remove the claim entirely.** Accuracy over completeness — a dropped claim is always safer than an unsupported one.

A claim that fails all three is **dropped, not carried forward.**

## Source-quality audit

While verifying, also flag:
- **Recency:** is this the most recent available source? If the claim relies on an old source, note "as of [year] — no more recent data found." Prefer re-finding a newer source over keeping a stale one.
- **Source type sanity:** is an `[Inference/estimate]` masquerading as `[Platform-direct]`? Is `[Internal]` data given a false public citation? Re-tag correctly.
- **Single-source blending:** if one sentence fused two sources, split it — one stat, one source.

## Output format — 02-verified.md

For every claim, record its verdict and the evidence:

```
# Verified Claims: <topic>  (lens: <lens> | depth: <depth>)

## <Competitor A>
- [PASS] <claim> ([label](url)) [<type>]
    verbatim: "<exact sentence from the re-fetched source>"
- [REWORDED] <original claim> -> <corrected claim> ([label](url)) [<type>]
    verbatim: "<exact sentence>"  | reason: <what was wrong>
- [REMOVED] <claim>  | reason: <which check failed and why>

## <Competitor B>
...

## What we couldn't verify  (consolidated)
- <Competitor>: <metric/claim> — no public disclosure / no source confirmed. Proxy signal available: <signal, labeled as proxy> or "none".
```

Only `[PASS]` and `[REWORDED]` claims are eligible to appear in the final report. The "What we couldn't verify" section feeds the per-competitor honesty note that synthesis and the report must preserve.

## Hard rule

Do not soften this stage to save time. The entire pipeline's credibility rests on it. If you are unsure whether a source supports a claim, the claim is `[REMOVED]`.
