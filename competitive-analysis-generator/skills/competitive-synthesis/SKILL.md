---
name: competitive-synthesis
description: Turns verified competitive research notes into a structured analytical draft — findings, a comparison matrix, convergence/divergence/whitespace, gaps and opportunities, and strategic implications. Use as the synthesis stage of a competitive analysis, after claims have been verified.
---

# Competitive Synthesis

## Role in the pipeline

This is the **synthesis stage**. Input: `02-verified.md` (only verified claims). Output: `03-synthesis.md` — a structurally complete analytical draft. You own **what the report says and how it's structured**; the downstream `memo-writing` skill owns **how the prose reads**. So emit a complete, well-organized draft even if the prose is plain — voice polish happens next.

**Build only on `[PASS]` and `[REWORDED]` claims.** Never reintroduce a `[REMOVED]` claim. Carry every claim's inline citation through unchanged — citations must survive into the final report.

## Report structure to produce

```
# Competitive Analysis: <Topic>
*Generated: <date> | Depth: <...> | Lens: <chosen lens> | Competitors: <list>*
*Reference materials used: <list, or "none — researched from scratch">*

## Key Takeaways
3-5 bolded, evidence-backed sentences a busy exec can read alone. Lead with the most important finding; attach 1-2 specific data points each.

## Executive Summary
2-4 sentences. The single most important takeaway first.

## Market Landscape
Size, dynamics, key trends, structure of the space, who the major players are.

## Competitor Profiles  (one per competitor)
### <Competitor>
**Strategic Importance:** Core / Ancillary / Add-on (how central is this space to their overall business?)
**Investment Trajectory:** Aggressive / Growing / Maintaining / Declining
**Positioning:** how they differentiate.
**Key features / recent moves:** what they're shipping or investing in (per chosen dimensions).
**What we couldn't verify:** gaps, pulled directly from 02-verified.md.

## Feature / Dimension Comparison Matrix
Markdown table: competitors as columns, chosen dimensions as rows.
Default to traffic-light ratings for scannability: 🟢 Strong / 🟡 Mixed / 🔴 Weak, with a one-line rationale per cell.
(If a plainer matrix is wanted, use ✓ / ~ / ✗ / ? instead.)

## Where the Market is Converging / Diverging / Whitespace
- Converging: what all players do the same.
- Diverging: where strategic bets differ.
- Whitespace: what no one does well — the opportunity.
(This replaces or augments a plain "Gaps & Opportunities" section.)

## Gaps & Opportunities / Strategic Implications
What this means for your company specifically. Where is the opening, and how central would it be to act on?

## Sources
All cited URLs, grouped by competitor. (Citations also stay inline on each claim.)
```

## Analytical framing tools (apply where they fit the topic)

- **Feature tiers** — when analyzing a product category, classify features as: Tier 1 Tablestakes (expected; no credit for having, churn for lacking), Tier 2 Value-Adds (build stickiness), Tier 3 Differentiators (drive competitive advantage).
- **Consumer-need framing** — for consumer products, evaluate competitors against the jobs the user is trying to do ("Effortless Discovery," "Just Hit Play," "Don't Miss a Drop") rather than a flat feature list.
- These are optional lenses, not mandatory structure. Use the ones the content actually supports; don't force a trio that isn't there.

## Analytical rules
- **One stat, one source.** Never blend two sources into one sentence.
- **Lead with the finding**, then support with evidence. Don't over-qualify.
- **Apply the lens strictly** (from `00-config.md` / the verified notes header). Consumer lens means no creator/B2B/infra content, however prominent elsewhere.

Hand `03-synthesis.md` to `memo-writing` for voice. Do not apply heavy stylistic polish here — keep it structurally complete and accurate.
