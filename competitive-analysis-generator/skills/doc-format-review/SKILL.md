---
name: doc-format-review
description: Publishes a markdown file to a Google Doc and reviews formatting quality — runs a preprocessor that fixes known converter bugs (multi-byte UTF-8 drift, bold-bleed bullets, link-text issues), publishes via the google-docs skill, then reads the doc back to spot-check tables, headers, bold spans, and citation placement. Use when publishing any markdown report to a Google Doc, or to QA an existing doc's rendering.
---

# Doc Format Review

## Role

General-purpose **publish + format-QA** stage. Input: any markdown file (in the competitive pipeline, `04-report.md`). Output: a published or updated Google Doc plus a read-back spot-check. Reusable for any markdown -> GDoc task, not just competitive analysis.

## Why this exists — the converter bug

The `google-docs` skill's converter (`/root/.claude/skills/google-docs/scripts/document_formatter.py`) computes text-range positions using **byte offsets where it needs character offsets**. Every multi-byte UTF-8 character before a bold span or link adds (byte_count − 1) bytes of cumulative drift. In a doc with many em-dashes, by the bottom the bold-span and link-text end-positions are off by ~3 chars per em-dash before them — producing `**Bold sentenc**e` or `[Link tex](url)t`, and at the extreme, swapped heading detection between adjacent lines. Drift accumulates **downward**, so the bottom of a long doc is worst.

The fix script eliminates the root cause by stripping multi-byte characters to ASCII before publishing.

## Workflow

```bash
# 1. Preprocess — fix the markdown before it ever reaches the converter
python /root/.claude/skills/doc-format-review/fix_md_for_gdoc.py SOURCE.md OUT.md

# 2a. Create a new doc
python /root/.claude/skills/google-docs/scripts/create_doc.py --file OUT.md   # returns a doc id/URL
# 2b. OR update an existing doc in place (preserves the URL)
python /root/.claude/skills/google-docs/scripts/update_doc.py --id <doc_id> --file OUT.md

# 3. Read back and spot-check — drift accumulates downward, so check the bottom hardest
python /root/.claude/skills/google-docs/scripts/read_doc.py <doc_id>
```

## What the fix script does (in order)
1. **Strip multi-byte UTF-8** (the root cause): `—`->`--`, `–`->`-`, `×`->`x`, `→`->`->`, `★`->`*`, traffic-light emoji -> `[G]/[Y]/[R]`. Belt-and-suspenders final pass replaces any remaining non-ASCII with `?`.
2. Strip `> blockquote` prefixes (don't render as a box anyway).
3. Convert `- **X:**` and `- **X.** Y` bullets to `- **X** -- Y` (avoids bold-bleed).
4. Add `-- ` separator after `- **X** Y` bullets lacking one.
5. Rewrite `- [Text](url) ...` bullets to `- Text ([link](url)) ...` (leading-`[` bug).
6. Convert `**X.** Y` standalone-paragraph leads to `**X** -- Y` (avoids setext-H1 promotion).
7. Replace `[Foo (Bar)](url)` -> `[Foo, Bar](url)` (parens in link text).
8. Inject a blank line between a bullet block and a following non-bullet paragraph.

## Format-review checklist (on read-back)
- **Bottom sections first** (Sources, Next Steps) — drift is worst there. Confirm no `**partial**bold` or `[partial]link` artifacts.
- **Tables** render as real tables; cells atomic; no stray pipes.
- **Headers** map to the right level; no body paragraph promoted to a heading.
- **Citations** stay attached to their claim (inline), clickable, not orphaned.
- **Bold spans** open and close on the right words.

If anything still looks broken, find the multi-byte char that escaped the strip pass and add it to the script's map.

## Notes
- WebFetch fails on authenticated Google Docs (returns the sign-in page) — always use `read_doc.py`, never WebFetch, to read back.
- **Cosmetic trade-off:** the published doc uses `--` instead of `—`. The source markdown keeps proper em-dashes. Accept until the converter is fixed upstream.
- This is a workaround for a real upstream bug in the `google-docs` converter — worth flagging to its maintainer eventually.
