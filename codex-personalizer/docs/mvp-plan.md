# Codex Personalizer MVP plan

The prototype is intentionally local-first and deterministic. The MVP should keep that trust posture while adding enough real workflow support that someone can use it for an actual Codex setup.

## Demo-ready story

For a demo of “Codex helped me build an app quickly,” the strongest story is:

1. Show the problem: personal Codex guidance is powerful, but most people do not know what to write.
2. Click through the onboarding flow.
3. Generate a short global `AGENTS.md`.
4. Explain that the user reviews every line before activation.
5. Copy or download the file.
6. Point to the fast-follow path: local helper can install it into the user’s Codex config area after explicit approval.

## MVP user journey

1. User opens the app.
2. User answers a 10–15 minute questionnaire.
3. App generates a concise global `AGENTS.md` draft.
4. User edits the draft in-browser.
5. User exports it by copying, downloading, or eventually activating through a local helper.
6. User receives clear guidance that repo-specific commands, frameworks, paths, and conventions belong in project-level `AGENTS.md` files.

## MVP feature set

### Keep

- Local-first questionnaire.
- Human-readable generated Markdown.
- Human-in-the-loop review before activation.
- Clear global-versus-project boundary.
- Copy and download export.
- Deterministic generation rules for the first version.

### Add next

- Full question bank covering:
  - role and work context
  - common Codex use cases
  - communication style
  - autonomy and approval preferences
  - verification expectations
  - recurring assistant frustrations
  - privacy and sensitivity boundaries
- Better generated guidance quality:
  - avoid generic statements
  - convert examples into specific operating rules
  - flag answers that are too vague to include
  - keep the global file short
- Save/resume state with an explicit “clear local data” control.
- A final quality checklist before export.
- Example output snippets so users understand what each answer affects.

### Defer

- Netflix identity enrichment from org structure, email, or Slack.
- Automatic learning loop that proposes updates over time.
- Account system.
- Backend persistence.
- Team admin dashboards.
- Direct writes to a user’s machine without a local helper and explicit approval.

## Local helper concept

A local helper is a small companion process or CLI that runs on the user’s computer with their permission. The hosted web app should not directly write to `~/.codex/AGENTS.md`. Instead, the user should approve an activation step locally.

Possible activation options:

- MVP: copy/download only.
- Fast follow: generate a one-line CLI command that writes the approved file locally.
- Later: signed local helper that can preview diffs, back up the current file, and apply the change only after confirmation.

The helper should always:

- show the exact target path
- show a diff before writing
- create a backup
- require explicit approval
- avoid editing project-level files

## Hosting recommendation

For a public demo MVP, Vercel is the simplest fit because this is a Next.js app and can be deployed directly from GitHub.

Suggested path:

1. Push `codex-personalizer/` to GitHub.
2. Import the project into Vercel.
3. Set the project root to `codex-personalizer`.
4. Use the default Next.js build settings.
5. Keep it static/local-first until an AI generation or account feature is truly needed.

## Later automation idea

Identity enrichment would be genuinely useful, but it should be treated as a fast follow because it changes the trust and privacy model. Good future sources could include:

- org structure
- role and team metadata
- frequently contacted collaborators
- recurring Slack/email context
- meeting patterns

The product should present these as suggestions, not silent additions. The user should approve, edit, or reject every proposed instruction before it enters global guidance.

## Guidance learning loop

Codex does not rely on global memory by default, so a future version could collect candidate learnings over time. The key is to keep the global file thin.

Only propose an update when the learning is:

- stable across multiple projects
- about the user’s preferred collaboration style
- actionable by future Codex sessions
- not a temporary project detail
- not sensitive or surprising
- short enough to remain useful in a global file

Every proposed update should require human approval.
