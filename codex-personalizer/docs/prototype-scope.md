# Codex Personalizer vertical-slice prototype

This prototype validates the product's highest-risk assumptions before the full 15-step questionnaire is built.

## Included

- Light, Codex-inspired visual system
- Multi-step questionnaire shell
- Clickable progress stepper plus Back and Continue
- One multi-select question
- Two single-select questions
- One constrained free-text answer
- Browser-local persistence and reset
- Deterministic global `AGENTS.md` generation
- Project-specific answer routing
- Editable Markdown, copy, and download

## Deliberately deferred

- Full 15-step question catalog
- Netflix identity enrichment
- Guidance-learning loop
- Local activation helper
- Authentication, backend, analytics, and deployment

## Review questions

1. Does the flow feel faster and clearer than writing global guidance from scratch?
2. Does the visual system feel polished enough for a public prototype?
3. Is the global-versus-project boundary understandable?
4. Does the generated Markdown feel specific enough to be useful and small enough to trust?
