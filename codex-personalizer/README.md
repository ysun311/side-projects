# Codex Personalizer

A privacy-first guided setup that turns explicit user preferences into concise global Codex guidance.

This repository currently contains a high-fidelity vertical-slice prototype. It validates the questionnaire experience, global-versus-project scope guard, deterministic Markdown generation, and browser-based review flow before the complete 10–15 minute setup is built.

The product idea: help people customize Codex in minutes instead of waiting for months of accumulated usage patterns. The app asks a small number of identity, collaboration, and trust-calibration questions, then produces a short global `AGENTS.md` draft the user can review before activating.

## What the prototype does

- Presents a polished, clickable multi-step onboarding flow.
- Captures user preferences locally in the browser.
- Generates editable global `AGENTS.md` guidance.
- Warns that project-specific rules belong in each repo’s own `AGENTS.md`.
- Lets the user copy or download the generated Markdown.
- Avoids accounts, analytics, backend storage, and AI APIs in the prototype.

## Run locally

Install Node.js 20.9 or newer and `pnpm` before setting up the project. On macOS with Homebrew:

```bash
brew install node pnpm
node --version
pnpm --version
```

Then clone the repository, install its dependencies, and start the development server:

```bash
git clone https://github.com/ysun311/side-projects.git
cd side-projects/codex-personalizer
pnpm install
pnpm dev
```

Open the local URL printed in Terminal, normally [http://localhost:3000](http://localhost:3000).

### Local preview helper

This repo also includes a helper script used during development:

```bash
./dev.sh
```

Open the `Network` address printed in Terminal. On managed machines, `localhost` may be intercepted by a proxy even when the app is healthy.

The launcher builds and serves a production-style local preview so browser interactions do not depend on the development hot-reload connection. It uses your system `pnpm` when available and otherwise falls back to Codex's bundled copy if you are running inside the same Codex desktop environment.

## Verify

```bash
pnpm lint
pnpm build
```

## Prototype scope

See [docs/prototype-scope.md](docs/prototype-scope.md).

## MVP plan

See [docs/mvp-plan.md](docs/mvp-plan.md).

## Product boundaries

- Generates global personal guidance only.
- Routes project-specific instructions out of the global file.
- Stores answers in the browser when storage is available.
- Uses deterministic, human-authored rule fragments.
- Does not use accounts, analytics, a backend, or an AI API.
