# | Building a Competitive-Analysis Web App on Top of a Claude Code Skill — Engineering Retro

*Build retro, 2026-06. Audience: teammates evaluating how to productize an agent skill, and a personal record of the build. Scope: the prototype that turns the `/competitive-analysis` skill into a form-to-report web app.*

> ## | Executive Summary
>
> **We turned a working Claude Code skill into a web app prototype by treating the UI as the easy part and the execution backend as the real problem.** A user fills a form; a verified, citation-checked competitive report comes back. The full pipeline works end-to-end today; the clickable, multi-user version is gated on one identity/permissions fix.
>
> - **We reused the agent instead of rebuilding it.** The backend is headless Claude Code (`claude -p`) driving the existing decomposed skill — same skills, hooks, MCP tools, and trust protocol we already trusted. No re-platforming.
> - **We de-risked with a $2 spike before writing any infrastructure.** One throwaway headless run proved the engine, surfaced the load-bearing gotchas, and told us the architecture was sound — before we committed to a two-tier build.
> - **We hit four real walls** — execution environment, deploy-target constraints, a UI regression, and a cross-account storage boundary — and got through three of them. The fourth (cross-account S3) is scoped and understood, not mysterious.
>
> **Key takeaway for the next person:** when you "make X a web app," the question is never the front end. It is *what executes when the user clicks submit, and can that thing reach everything it needs under the identity it runs as.* Answer that first.
>
> **Discussion questions:** (1) Is headless-CLI-as-backend a pattern we want to standardize, or a prototype crutch? (2) Where should the always-on worker live — a container orchestration platform, or a shared service?

---

# | The Goal

The starting point was a mature, trusted asset: a Claude Code skill (`/competitive-analysis`, later decomposed into an orchestrator plus five focused sub-skills) that produces rigorous competitive reports. Its defining feature is a **mandatory triple-verification trust protocol** — every claim is re-fetched from its source and checked for presence, verbatim support, and accuracy before it survives. Claims that fail are dropped or reworded.

The skill worked, but only for the person running Claude Code. **The goal was reach:** let a teammate answer a few questions in a browser and get the same verified report, without touching a terminal. Markdown form-fields in, structured report out. The longer-term vision was a shareable, on-brand tool hosted where the rest of our analytics lives (Posit Connect).

The trap we wanted to avoid: rebuilding the analysis engine to fit a web framework, and in the process losing the trust protocol that made the skill worth productizing.

# | How We Started

We resisted jumping to code. The first move was to name the decision that actually determined scope: **what runs server-side when the form is submitted?** A web form only collects input. Something has to execute the agent loop — with the skills, the internal tools, and the verification gate — when a user hits submit.

That framing produced three honest options, which we put to the user rather than assuming:

| Option | What it is | Lift |
|---|---|---|
| **Headless Claude Code** | Form → `claude -p` driving the decomposed skill | Low — reuses everything |
| **Agent SDK service** | Rebuild the pipeline as a Python service | High — re-plumb hooks, MCP, artifacts |
| **Wizard-of-Oz** | Form generates a prompt a human runs | Trivial, but not automated |

We chose **headless Claude Code, hosted on Posit Connect, driving the decomposed skill**. Two non-obvious reasons drove the choice, and they became our anchors.

# | What We Anchored On

**Anchor 1 — Reuse the working thing.** Headless `claude -p` inherits the installed skills, the verification hook, and the MCP tool connections *for free*. The Agent SDK path would have meant rebuilding all of that and re-earning trust in it. The cheapest correct backend was the one we already operated.

**Anchor 2 — Design for observability.** The decomposed skill writes each stage to a known file in a per-run directory (`00-config → 01-research → 02-verified → 03-synthesis → 04-report`). That file-based artifact contract is not just clean architecture — **it is a progress bar for free.** A web UI can show "Researching → Verifying → Synthesizing" just by watching the directory fill. The monolithic skill is a black box; the decomposed one is observable. That single property made it the right backend for a UI.

**Anchor 3 — De-risk before you build.** Before any infrastructure, we ran one throwaway headless analysis end-to-end. The rule was simple: if the engine doesn't work as a backend, nothing downstream matters, so prove that first and cheaply.

**Anchor 4 — The trust protocol is non-negotiable.** The whole point of the tool is verified claims. Every step had to preserve the triple-verification gate. We treated "did verification actually run and remove bad claims" as the acceptance test at every stage, not a nice-to-have.

# | The Walls — and How We Got Through Them

The build was a sequence of walls. Each one taught us something transferable.

## Wall 1 — The silent-exit gotcha (`IS_SANDBOX`)

The very first headless run **exited 0 and did nothing.** No error in the obvious place. The cause was buried at the bottom of a wrapper bootstrap log: Claude Code refuses `--permission-mode bypassPermissions` when running as root, *unless* the environment is marked a sandbox. The dev container runs as root.

**Fix:** set `IS_SANDBOX=1`. **Lesson:** an exit-0-with-no-output is a configuration refusal, not success — read the whole log, not just the tail you expected. We baked the flag into the worker so the next person never rediscovers it.

With that fixed, the spike succeeded completely: artifacts filled in order, the verification gate fired, real web research ran (2 searches, 4 fetches), and — critically — **verification dropped a claim that existed only in a search snippet**, exactly as designed. The trust protocol survived the jump to automation. Cost: ~$2, ~5 minutes. The architecture was validated for the price of a coffee.

## Wall 2 — The form-to-prompt contract

Headless mode has no human to answer the skill's interactive questions. We had to pre-supply all answers in the prompt and explicitly instruct "do not ask." This turned out to be the **central interface of the whole system:** the form's fields map one-to-one to the pre-supplied answer lines. Naming that contract early kept the frontend and backend honest about what they owed each other.

## Wall 3 — The deploy target can't run the agent

The plan was to host on Posit Connect. Before deploying anything, we read the platform docs and learned PC content runs as a **non-root, Python-packages-only process on a single shared instance with 60-second startup timeouts.** It cannot install or run the `claude` CLI, and a 5-minute agent job is a bad neighbor on shared serving infra.

**We let the docs kill the assumption instead of burning a deploy to discover it.** That forced the real architecture: **two tiers.** A thin Streamlit frontend on Posit Connect (pure UI) and a worker on the dev container (where the CLI, tools, and hooks live), decoupled by a job bus.

**Lesson:** read the platform's constraints before fighting them. "Can my code even run here?" is cheaper to answer from documentation than from a failed deploy.

## Wall 4 — Latency forces async

A real run is minutes, not seconds. A synchronous web request would time out. This wasn't a wall we hit so much as one we saw coming and designed around: the frontend writes a job and **polls** a status file; the worker processes and updates that file. The artifact contract from Anchor 2 made the status model trivial — we already had observable stages.

## Wall 5 — The deploy crash (`tornado`)

First Posit Connect deploy: the app crashed on startup. The logs were clear this time — `ModuleNotFoundError: No module named 'tornado'`. The newer Streamlit no longer pulls tornado in as a dependency, but Connect's Streamlit runtime shim imports it directly. **Fix:** declare `tornado` explicitly in `requirements.txt`. **Lesson:** a managed runtime has its own assumptions about your dependency tree; pin what the platform's shim needs, not just what your code imports.

## Wall 6 — The theme regression, and the discipline of seeing

We restyled the app to a branded theme (black, red accents, branded header). It looked right — except a dimension chip showed "…oduct features…" with the first letters clipped. We guessed at the CSS twice and redeployed twice. Both guesses were wrong.

So we stopped guessing and **got instrumentation:** a headless browser to load the app, dump the chip's DOM, and read its computed styles. The truth was immediate and not what either guess assumed — the text wasn't truncated at all. An **over-broad `input` CSS rule** had styled the multiselect's *internal* search box, dropping a stray bordered element that overlapped the first chip. We scoped the rule to real text fields, verified the fix in a screenshot *before* deploying, and shipped it once.

**Lesson — the most transferable in the build:** when a UI bug resists two fixes, the problem is your visibility, not your CSS. Buy ground truth (inspect the live DOM) before spending another deploy cycle on a hypothesis.

## Wall 7 — The cross-account storage boundary (the one still standing)

This is the wall that separates "prototype that works" from "tool anyone can use." The full loop worked perfectly **on the dev container**, where the frontend and worker ran under the same identity. The moment the frontend moved to Posit Connect, jobs submitted from the browser sat at "Queued" forever.

The cause, confirmed from the user's own stuck jobs: the Posit Connect app writes job files to S3 under *its* account's identity. The dev container worker, under a *different* account's role, gets `AccessDenied` reading them. In S3, **the writer owns the object; a principal from another account can't read it without a bucket policy granting access** — and we don't own the shared bucket's policy.

**We have not "fought through" this one yet — and saying so is part of the retro.** The fix is concrete and scoped: a dedicated bus bucket with "bucket-owner-enforced" object ownership that both identities have IAM access to, which makes object ownership stop mattering. **Lesson:** distributed systems break at trust boundaries. Same AWS account does not mean same access; same bucket does not mean readable. When two identities must share state, design the permission model first, not last.

## Wall 8 — The dev container won't host arbitrary ports

When the browser path was blocked, we tried to host the clickable UI on the dev container directly (one identity, so the loop works). It turned out the dev container only exposes a **fixed set of pre-baked service ports** through a managed nginx and container-platform port declarations; arbitrary app ports aren't network-reachable, and editing the managed config is fragile. We confirmed Streamlit ran locally (health check passed) but had no clean way to surface it. **We named the dead end rather than hacking managed infrastructure to force it.**

# | What We Shipped

- **A working two-tier prototype.** Streamlit frontend (deployed to Posit Connect, on-brand), an S3 job bus, a dev container worker that drives the decomposed skill headlessly, and a status contract the UI polls. The full form-to-report loop is proven end-to-end under a single identity.
- **A real, verified report on demand.** The demo run produced a 1,770-word analysis of "lifestyle mid-form content" with inline citations — and verification **removed 5 unverifiable claims and reworded 3**, exactly the behavior the tool exists to provide. Published to a Google Doc for sharing.
- **Cost and latency, measured across four runs:** ~$2–4 per quick-scan analysis, ~5–9 minutes. Verification dominates both — which is the point.
- **A version-controlled, documented repo** on internal GitHub, with the skills, the web app, and this retro preserved.

# | What's Left

- **The cross-account S3 fix** (Wall 7) — the one change that converts the live, themed Posit Connect app from "spins forever" to "works for anyone." Highest-leverage next step.
- **An always-on worker.** The dev container is not a durable host; production wants the worker on a container orchestration platform or a shared service.
- **A credentials and cost model.** Every run currently spends one person's Claude credentials. A shared service account and a usage guardrail (e.g. estimated cost shown before a deep dive) come before wide rollout.
- **Optional fidelity:** marrying an earlier hand-built HTML design (collapsing wizard steps, per-source progress, badge-rendered citations) to the live backend.

# | Transferable Lessons

1. **The UI is the easy part.** "Make X a web app" is really "what executes server-side, and under what identity." Answer that before you design a single screen.
2. **De-risk the riskiest assumption first, cheaply.** A $2 throwaway run told us the engine worked as a backend and surfaced the gotchas — before any infrastructure existed.
3. **Reuse beats rebuild when the working thing is trusted.** Headless Claude Code gave us skills, hooks, and tools for free; the SDK rebuild would have re-earned all of it.
4. **Architect for observable intermediate state.** The file-based artifact contract gave us a progress UI, resumability, and a debugging surface — without extra work.
5. **Read the platform before fighting it.** Posit Connect's constraints were in the docs; we got the two-tier architecture from reading, not from a failed deploy.
6. **When a bug resists two fixes, buy visibility.** Inspecting the live DOM ended a guess-and-deploy loop in one step.
7. **Distributed systems fail at trust boundaries.** Same account ≠ same access. Design the permission model up front.
8. **Be honest about "done."** A demoable prototype is not a shared production tool. Naming the remaining gap precisely is what makes a retro useful — and what makes the next step obvious.

# | Next Steps

- **Fix the bus:** stand up a dedicated, bucket-owner-enforced S3 bucket with IAM access for both the Posit Connect app's identity and the worker's identity; repoint both tiers.
- **Move the worker to an always-on host** and add a shared service account.
- **Re-demo the live, clickable Posit Connect app** once the bus is fixed — the milestone for "anyone on the team can use this."
