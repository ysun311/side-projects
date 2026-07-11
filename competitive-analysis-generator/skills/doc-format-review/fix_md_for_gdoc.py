"""Fix markdown patterns that the google-docs converter mangles.

The converter has a recurring "off-by-N" bug that shifts the end-position of
bold spans and link-text spans by ~3 characters in certain contexts.
Empirically the trigger contexts are:

  A) Bullets starting with a link: `- [Text](url) — type` → link text cut short
  B) Bullets with a bold prefix and no em-dash separator: `- **X** Y` → bold-end shifts
  C) Bullets with bold ending in a colon: `- **X:**` → bold-end shifts
  D) Bullets with bold ending in a period followed by more text: `- **X.** Y` → bold-end shifts
  E) Standalone paragraphs starting with `**X.**` near a paragraph boundary → promoted to malformed H1
  F) Links with parens inside link text: `[Foo (Bar)](url)` → link cut at the open-paren
  G) Blockquote `> ` lines used as a "box" → don't render as a box; trailing `---` triggers setext-H2
  H) Bullet block immediately followed by non-bullet paragraph → no blank line → next paragraph mis-parsed

The fix below preprocesses markdown to avoid every one of these triggers
while preserving the visible content and the user's `# | Section` style.
"""
import re
import sys


def fix(text: str) -> str:
    # ROOT-CAUSE FIX: the converter uses byte offsets where it needs character
    # offsets, so any multi-byte UTF-8 character before a bold span or link
    # accumulates a drift of (byte_count - 1) per occurrence. Em-dash `—`
    # (3 bytes) is the worst offender in this report style. Replace em-dashes
    # with `--` (ASCII) to eliminate the drift entirely.
    # Also replace en-dash `–` (3 bytes) → `-`, and the curly quotes are 3
    # bytes too but less common in our markdown.
    text = text.replace('—', '--')   # em-dash → double hyphen
    text = text.replace('–', '-')    # en-dash → single hyphen (e.g., "5-10")
    text = text.replace('…', '...')  # horizontal ellipsis (3 bytes) → 3 dots
    text = text.replace('×', 'x')    # multiplication sign (2 bytes) → x
    text = text.replace('→', '->')   # right-arrow (3 bytes) → ASCII
    text = text.replace('≈', '~')    # approx (3 bytes) → tilde
    text = text.replace('★', '*')    # star (3 bytes) → asterisk
    text = text.replace('·', '-')    # middle dot (2 bytes) → hyphen
    text = text.replace('✓', '[Y]')  # checkmark (3 bytes)
    text = text.replace('✗', '[N]')  # ballot X (3 bytes)
    text = text.replace('❓', '?')    # question mark ornament (3 bytes)
    text = text.replace('🟢', '[G]')
    text = text.replace('🟡', '[Y]')
    text = text.replace('🔴', '[R]')
    text = text.replace('🎁', '[gift]')
    # Final safety: strip any remaining 2+ byte UTF-8 char to '?' to prevent drift
    import re as _re
    text = _re.sub(r'[^\x00-\x7f]', '?', text)

    # F) Parens inside link text — replace " (X)" with ", X" inside [ ]
    def _fix_paren_in_link(m):
        link_text = m.group(1)
        url = m.group(2)
        cleaned = re.sub(r' \(([^)]+)\)', r', \1', link_text)
        return f'[{cleaned}]({url})'
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', _fix_paren_in_link, text)

    # G) Blockquote-as-box — strip `> ` prefix. Don't add `---` rules
    # (they trigger setext-H2 promotion of the preceding paragraph).
    lines = text.split('\n')
    out = []
    for line in lines:
        if line.startswith('> '):
            out.append(line[2:])
        elif line == '>':
            out.append('')
        else:
            out.append(line)
    text = '\n'.join(out)

    # C) Bullets with bold ending in colon: `- **X:**` → `- **X** -- `
    text = re.sub(
        r'^(- \*\*[^*\n]+?):\*\*\s*',
        r'\1** -- ',
        text,
        flags=re.MULTILINE,
    )

    # D) Bullets with bold ending in period + more text: `- **X.** Y` → `- **X** -- Y`
    text = re.sub(
        r'^(- \*\*[^*\n]+?)\.\*\* ',
        r'\1** -- ',
        text,
        flags=re.MULTILINE,
    )

    # B) Bullets with bold prefix and no em-dash separator: `- **X** Y` →
    # `- **X** -- Y`. Use `--` directly (em-dash is already converted to `--`
    # earlier in this pass) and skip if already separated.
    def _bold_bullet_sep(m):
        head = m.group(1)        # `- **X**`
        sep_char = m.group(2)    # first char after `**` and space
        if sep_char == '-':      # already starts with hyphen/dash
            return m.group(0)
        return f'{head} -- {sep_char}'
    text = re.sub(
        r'^(- \*\*[^*\n]+?\*\*) ([^\n])',
        _bold_bullet_sep,
        text,
        flags=re.MULTILINE,
    )

    # A) Bullets starting with a link: `- [Text](url) — type` →
    # `- Text ([link](url)) — type`. Avoids the leading-`[` bullet bug.
    def _bullet_link(m):
        link_text = m.group(1)
        url = m.group(2)
        rest = m.group(3) or ''
        return f'- {link_text} ([link]({url})){rest}'
    text = re.sub(
        r'^- \[([^\]]+)\]\(([^)]+)\)(.*)$',
        _bullet_link,
        text,
        flags=re.MULTILINE,
    )

    # E) Standalone-paragraph bold-leads at start of line (not bullet, not heading).
    # `**X.** Y` → `**X** -- Y` so the parser can't promote to setext/atx heading.
    text = re.sub(
        r'^(\*\*[^*\n]+?)\.\*\* ',
        r'\1** -- ',
        text,
        flags=re.MULTILINE,
    )
    text = re.sub(
        r'^(\*\*[^*\n]+?):\*\* ',
        r'\1** -- ',
        text,
        flags=re.MULTILINE,
    )

    # H) Inject blank line between a bullet block and the following
    # non-bullet, non-heading, non-table paragraph.
    lines2 = text.split('\n')
    out2 = []
    for i, line in enumerate(lines2):
        out2.append(line)
        is_bullet = line.startswith('- ') or line.startswith('* ')
        if is_bullet and i + 1 < len(lines2):
            nxt = lines2[i + 1]
            next_is_bullet = nxt.startswith('- ') or nxt.startswith('* ')
            next_is_blank = nxt.strip() == ''
            next_is_heading = nxt.startswith('#')
            next_is_table = nxt.startswith('|')
            next_is_rule = nxt.strip() == '---'
            if not (next_is_bullet or next_is_blank or next_is_heading
                    or next_is_table or next_is_rule):
                out2.append('')
    text = '\n'.join(out2)

    return text


if __name__ == '__main__':
    src = sys.argv[1]
    dst = sys.argv[2]
    with open(src) as f:
        content = f.read()
    fixed = fix(content)
    with open(dst, 'w') as f:
        f.write(fixed)
    print(f"Wrote {dst}")
