"use client";

import { useEffect, useMemo, useReducer, useRef, useState } from "react";
import {
  EMPTY_ANSWERS,
  GOAL_OPTIONS,
  INITIATIVE_OPTIONS,
  PROTOTYPE_STEPS,
  RESPONSE_OPTIONS,
  type Answers,
  type GoalId,
  type InitiativeStyle,
  type ResponseStyle,
} from "@/lib/questionnaire";
import { generateGuidance } from "@/lib/generator";

const STORAGE_KEY = "codex-personalizer-prototype-v1";

type State = {
  step: number;
  answers: Answers;
  markdownDraft: string;
};

type Action =
  | { type: "hydrate"; state: State }
  | { type: "go"; step: number }
  | { type: "toggle-goal"; goal: GoalId }
  | { type: "response-style"; value: ResponseStyle }
  | { type: "initiative"; value: InitiativeStyle }
  | { type: "frustration"; value: string }
  | { type: "markdown"; value: string }
  | { type: "reset" };

const INITIAL_STATE: State = {
  step: 0,
  answers: EMPTY_ANSWERS,
  markdownDraft: "",
};

function reducer(state: State, action: Action): State {
  switch (action.type) {
    case "hydrate":
      return action.state;
    case "go":
      return { ...state, step: action.step };
    case "toggle-goal": {
      const selected = state.answers.goals.includes(action.goal);
      return {
        ...state,
        answers: {
          ...state.answers,
          goals: selected
            ? state.answers.goals.filter((goal) => goal !== action.goal)
            : [...state.answers.goals, action.goal],
        },
        markdownDraft: "",
      };
    }
    case "response-style":
      return {
        ...state,
        answers: { ...state.answers, responseStyle: action.value },
        markdownDraft: "",
      };
    case "initiative":
      return {
        ...state,
        answers: { ...state.answers, initiative: action.value },
        markdownDraft: "",
      };
    case "frustration":
      return {
        ...state,
        answers: { ...state.answers, frustration: action.value },
        markdownDraft: "",
      };
    case "markdown":
      return { ...state, markdownDraft: action.value };
    case "reset":
      return INITIAL_STATE;
  }
}

function stepIsComplete(step: number, answers: Answers) {
  if (step === 0) return true;
  if (step === 1) return answers.goals.length > 0;
  if (step === 2) return Boolean(answers.responseStyle);
  if (step === 3) return Boolean(answers.initiative);
  return true;
}

export function PersonalizerPrototype() {
  const [state, dispatch] = useReducer(reducer, INITIAL_STATE);
  const [hydrated, setHydrated] = useState(false);
  const [copyState, setCopyState] = useState<"idle" | "copied">("idle");
  const copyTimerRef = useRef<number | null>(null);
  const conversationRef = useRef<HTMLDivElement>(null);
  const generation = useMemo(
    () => generateGuidance(state.answers),
    [state.answers],
  );
  const activeMarkdown = state.markdownDraft || generation.markdown;

  useEffect(() => {
    try {
      const storage = window.localStorage;
      if (!storage) return;
      const stored = storage.getItem(STORAGE_KEY);
      if (stored) dispatch({ type: "hydrate", state: JSON.parse(stored) as State });
    } catch {
      // Storage can be unavailable in privacy-restricted browser contexts.
    } finally {
      setHydrated(true);
    }
  }, []);

  useEffect(() => {
    if (!hydrated) return;
    try {
      window.localStorage?.setItem(STORAGE_KEY, JSON.stringify(state));
    } catch {
      // The questionnaire remains usable for the current session.
    }
  }, [hydrated, state]);

  useEffect(
    () => () => {
      if (copyTimerRef.current) window.clearTimeout(copyTimerRef.current);
    },
    [],
  );

  const current = PROTOTYPE_STEPS[state.step];
  const progress = (state.step / (PROTOTYPE_STEPS.length - 1)) * 100;
  const canContinue = stepIsComplete(state.step, state.answers);

  function goTo(step: number) {
    dispatch({ type: "go", step: Math.max(0, Math.min(step, 4)) });
    conversationRef.current?.scrollTo({ top: 0, behavior: "smooth" });
  }

  async function copyMarkdown() {
    await navigator.clipboard.writeText(activeMarkdown);
    setCopyState("copied");
    if (copyTimerRef.current) window.clearTimeout(copyTimerRef.current);
    copyTimerRef.current = window.setTimeout(() => setCopyState("idle"), 1600);
  }

  function downloadMarkdown() {
    const blob = new Blob([activeMarkdown], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = "AGENTS.md";
    anchor.click();
    URL.revokeObjectURL(url);
  }

  function reset() {
    try {
      window.localStorage?.removeItem(STORAGE_KEY);
    } catch {
      // Storage can be unavailable in privacy-restricted browser contexts.
    }
    dispatch({ type: "reset" });
    conversationRef.current?.scrollTo({ top: 0, behavior: "smooth" });
  }

  return (
    <main className="app-canvas">
      <section className="assistant-shell" aria-label="Codex Personalizer prototype">
        <header className="app-header">
          <div className="brand-lockup">
            <div className="brand-mark" aria-hidden="true">
              <span />
            </div>
            <div>
              <p className="brand-name">Codex Personalizer</p>
              <p className="brand-kicker">A faster way to make Codex yours</p>
            </div>
          </div>
          <button className="quiet-button" type="button" onClick={reset}>
            Start over
          </button>
        </header>

        <div className="progress-region">
          <div className="progress-meta">
            <span>{current.group}</span>
            <span>
              Step {state.step + 1} of {PROTOTYPE_STEPS.length}
            </span>
          </div>
          <div className="progress-track" aria-hidden="true">
            <span style={{ width: `${progress}%` }} />
          </div>
          <nav className="stepper" aria-label="Personalization steps">
            {PROTOTYPE_STEPS.map((step, index) => {
              const reachable = index <= state.step || stepIsComplete(index - 1, state.answers);
              return (
                <button
                  className={index === state.step ? "step active" : "step"}
                  disabled={!reachable}
                  key={step.id}
                  onClick={() => goTo(index)}
                  type="button"
                  aria-current={index === state.step ? "step" : undefined}
                >
                  <span>{index + 1}</span>
                  {step.label}
                </button>
              );
            })}
          </nav>
        </div>

        <div className="conversation" aria-live="polite" ref={conversationRef}>
          <div className={state.step === 0 ? "question-panel welcome-panel" : "question-panel"}>
            {renderStep(state, dispatch, activeMarkdown, generation)}
          </div>
        </div>

        <footer className="navigation-bar">
          <button
            className="secondary-button"
            disabled={state.step === 0}
            onClick={() => goTo(state.step - 1)}
            type="button"
          >
            ← Back
          </button>
          {state.step < 4 ? (
            <button
              className="primary-button"
              disabled={!canContinue}
              onClick={() => goTo(state.step + 1)}
              type="button"
            >
              {state.step === 0 ? "Personalize my Codex" : "Continue"} →
            </button>
          ) : (
            <div className="export-actions">
              <button className="secondary-button" onClick={downloadMarkdown} type="button">
                Download
              </button>
              <button className="primary-button" onClick={copyMarkdown} type="button">
                {copyState === "copied" ? "Copied" : "Copy AGENTS.md"}
              </button>
            </div>
          )}
        </footer>
      </section>
      <p className="prototype-note">
        Built with Codex <span aria-hidden="true">|</span> Contact: Giselle Sun (
        <a href="mailto:ysun311@gmail.com">ysun311@gmail.com</a>)
      </p>
    </main>
  );
}

function renderStep(
  state: State,
  dispatch: React.Dispatch<Action>,
  activeMarkdown: string,
  generation: ReturnType<typeof generateGuidance>,
) {
  if (state.step === 0) {
    return (
      <div className="welcome-layout">
        <div className="welcome-intro">
          <p className="eyebrow">Personal setup</p>
          <h1>Make Codex work the way you do.</h1>
          <p className="question-copy">
            Answer a few focused questions. We&apos;ll turn your preferences into a
            concise global AGENTS.md that you can review and edit before using.
          </p>
        </div>
        <div className="welcome-points" aria-label="Setup principles">
          <div><span>01</span><strong>About 10 minutes</strong><small>A short, guided setup.</small></div>
          <div><span>02</span><strong>Private by default</strong><small>Your answers stay in this browser.</small></div>
          <div><span>03</span><strong>Always yours</strong><small>Nothing changes without your review.</small></div>
        </div>
        <div className="welcome-scope">
          <div className="scope-symbol" aria-hidden="true">G</div>
          <div>
            <strong>For global preferences only</strong>
            <p>
              This file should describe how Codex works with you everywhere.
              Frameworks, commands, paths, and repository rules belong in each
              project&apos;s own AGENTS.md.
            </p>
          </div>
        </div>
      </div>
    );
  }

  if (state.step === 1) {
    return (
      <>
        <p className="eyebrow">Know You</p>
        <h1>What do you want Codex to help with most?</h1>
        <p className="question-copy">Choose all that apply. This helps identify where personalization matters most.</p>
        <div className="option-grid two-columns">
          {GOAL_OPTIONS.map((option) => {
            const selected = state.answers.goals.includes(option.id);
            return (
              <button
                className={selected ? "option-card selected" : "option-card"}
                key={option.id}
                onClick={() => dispatch({ type: "toggle-goal", goal: option.id })}
                type="button"
                aria-pressed={selected}
              >
                <span className="option-icon">{option.icon}</span>
                <strong>{option.label}</strong>
                <span className="selection-indicator">{selected ? "✓" : "+"}</span>
              </button>
            );
          })}
        </div>
      </>
    );
  }

  if (state.step === 2) {
    return (
      <>
        <p className="eyebrow">Work With You</p>
        <h1>How much detail feels useful?</h1>
        <p className="question-copy">This becomes the default—not a limit. You can always ask for more or less.</p>
        <div className="option-stack">
          {RESPONSE_OPTIONS.map((option) => (
            <button
              className={state.answers.responseStyle === option.id ? "option-card selected" : "option-card"}
              key={option.id}
              onClick={() => dispatch({ type: "response-style", value: option.id })}
              type="button"
              aria-pressed={state.answers.responseStyle === option.id}
            >
              <span><strong>{option.label}</strong>{option.recommended && <em>Recommended</em>}<small>{option.description}</small></span>
              <span className="selection-indicator">{state.answers.responseStyle === option.id ? "✓" : "○"}</span>
            </button>
          ))}
        </div>
      </>
    );
  }

  if (state.step === 3) {
    return (
      <>
        <p className="eyebrow">Earn Your Trust</p>
        <h1>When should Codex stop and ask?</h1>
        <p className="question-copy">Your answer sets the balance between momentum and control.</p>
        <div className="option-stack">
          {INITIATIVE_OPTIONS.map((option) => (
            <button
              className={state.answers.initiative === option.id ? "option-card selected" : "option-card"}
              key={option.id}
              onClick={() => dispatch({ type: "initiative", value: option.id })}
              type="button"
              aria-pressed={state.answers.initiative === option.id}
            >
              <span><strong>{option.label}</strong>{option.recommended && <em>Recommended</em>}<small>{option.description}</small></span>
              <span className="selection-indicator">{state.answers.initiative === option.id ? "✓" : "○"}</span>
            </button>
          ))}
        </div>
        <label className="custom-answer">
          <span>Optional: what has an AI assistant done that you never want repeated?</span>
          <textarea
            maxLength={300}
            onChange={(event) => dispatch({ type: "frustration", value: event.target.value })}
            placeholder="Example: It kept asking for confirmation on safe, reversible work."
            value={state.answers.frustration}
          />
          <small>{state.answers.frustration.length}/300</small>
        </label>
      </>
    );
  }

  return (
    <>
      <p className="eyebrow">Review and Activate</p>
      <h1>Your first global AGENTS.md</h1>
      <p className="question-copy">Edit directly in the browser. Copy or download only when it feels right.</p>
      {generation.warnings.map((warning) => <div className="warning" key={warning}>⚑ {warning}</div>)}
      <div className="editor-header"><span>AGENTS.md</span><span>{activeMarkdown.split("\n").length} lines</span></div>
      <textarea
        className="markdown-editor"
        onChange={(event) => dispatch({ type: "markdown", value: event.target.value })}
        spellCheck={false}
        value={activeMarkdown}
        aria-label="Editable AGENTS.md preview"
      />
      {generation.routedElsewhere.length > 0 && (
        <div className="routed-card"><strong>Routed elsewhere</strong><p>This custom answer looks project-specific, so it was not added to global guidance.</p></div>
      )}
      <details className="why-card"><summary>What happens after download?</summary><p>You&apos;ll place this file at <code>~/.codex/AGENTS.md</code>. The full product will include backup and verification guidance.</p></details>
    </>
  );
}
