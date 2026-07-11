#!/usr/bin/env python3
"""PreToolUse gate for the decomposed competitive-analysis pipeline.

Blocks the `competitive-synthesis` skill from running while any active run has
produced research notes (01-research-notes.md) but not yet a verification
artifact (02-verified.md). This makes the trust/verification step a hard,
harness-enforced gate rather than a model-mediated instruction.

Scope: only ever blocks the `competitive-synthesis` skill. Every other Skill
call (including the general-purpose memo-writing and doc-format-review) passes
through untouched, so their standalone reuse is unaffected.

Mechanism: PreToolUse hooks block the tool call when this script exits with
code 2; stderr is fed back to Claude as the reason. On any unexpected error we
fail OPEN (exit 0) so a bug here can never wedge unrelated Skill calls — the
gate's job is narrow and the orchestrator always writes 01 before synthesis,
so the real failure mode (research done, verify skipped) is still caught.
"""
import json
import os
import sys

GATED_SKILL = "competitive-synthesis"
RESEARCH_ARTIFACT = "01-research-notes.md"
VERIFIED_ARTIFACT = "02-verified.md"
ACTIVE_MARKER = ".active-run"
# A genuine verification pass tags every claim with one of these verdicts.
# An empty or stubbed 02-verified.md has none, so it fails the content check.
VERDICT_TAGS = ("[PASS]", "[REWORDED]", "[REMOVED]")


def _verify_reason(run_dir):
    """Why this run is NOT yet verified, or None if it passes the gate.

    A run is gated unless 02-verified.md exists AND contains at least one
    verdict tag — proof the verification skill actually ran, not just that a
    placeholder file was created.
    """
    verified = os.path.join(run_dir, VERIFIED_ARTIFACT)
    if not os.path.isfile(verified):
        return "no 02-verified.md (verification not run)"
    try:
        with open(verified, encoding="utf-8", errors="replace") as fh:
            content = fh.read()
    except OSError:
        return "02-verified.md exists but is unreadable"
    if not any(tag in content for tag in VERDICT_TAGS):
        return ("02-verified.md exists but contains no verdict tags "
                "([PASS]/[REWORDED]/[REMOVED]) -- looks like a stub, not a "
                "real verification pass")
    return None


def _pending_run_dirs(cwd):
    """Return (run_dir, reason) for runs with research notes that are not
    yet genuinely verified."""
    pending = []
    seen = set()
    reports = os.path.join(cwd, "reports")
    if not os.path.isdir(reports):
        return pending

    def _consider(run_dir):
        if run_dir in seen or not os.path.isdir(run_dir):
            return
        if not os.path.isfile(os.path.join(run_dir, RESEARCH_ARTIFACT)):
            return
        reason = _verify_reason(run_dir)
        if reason:
            pending.append((run_dir, reason))
        seen.add(run_dir)

    # 1) Explicit marker written by the orchestrator (exact, preferred).
    marker = os.path.join(reports, ACTIVE_MARKER)
    if os.path.isfile(marker):
        try:
            with open(marker) as fh:
                _consider(fh.read().strip())
        except OSError:
            pass

    # 2) Fallback scan: any run dir with research notes.
    try:
        for name in os.listdir(reports):
            _consider(os.path.join(reports, name))
    except OSError:
        pass

    return pending


def main():
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        sys.exit(0)  # fail open

    if payload.get("tool_name") != "Skill":
        sys.exit(0)

    tool_input = payload.get("tool_input") or {}
    skill = tool_input.get("skill") or tool_input.get("name") or ""
    if skill != GATED_SKILL:
        sys.exit(0)

    cwd = payload.get("cwd") or os.getcwd()
    pending = _pending_run_dirs(cwd)
    if pending:
        listed = "\n  - ".join("%s  (%s)" % (d, why) for d, why in pending)
        sys.stderr.write(
            "VERIFICATION GATE BLOCKED competitive-synthesis.\n"
            "These runs have research notes (01-research-notes.md) but are not "
            "genuinely verified:\n  - " + listed + "\n"
            "Run the competitive-verify skill to produce a real 02-verified.md "
            "(every claim tagged [PASS]/[REWORDED]/[REMOVED]), then retry "
            "competitive-synthesis. Synthesis must operate only on verified "
            "claims.\n"
        )
        sys.exit(2)  # block

    sys.exit(0)


if __name__ == "__main__":
    main()
