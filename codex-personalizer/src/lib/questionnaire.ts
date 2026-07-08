export const GOAL_OPTIONS = [
  { id: "research", label: "Research and synthesize", icon: "⌕" },
  { id: "writing", label: "Write and communicate", icon: "✎" },
  { id: "building", label: "Build apps and automate", icon: "◇" },
  { id: "analysis", label: "Analyze data and decisions", icon: "↗" },
] as const;

export const RESPONSE_OPTIONS = [
  {
    id: "concise",
    label: "Concise",
    description: "Lead with the answer. Keep detail available, not automatic.",
    recommended: false,
  },
  {
    id: "balanced",
    label: "Balanced",
    description: "Give the outcome, key reasoning, and practical next steps.",
    recommended: true,
  },
  {
    id: "detailed",
    label: "Detailed",
    description: "Teach as you go and include context, tradeoffs, and examples.",
    recommended: false,
  },
] as const;

export const INITIATIVE_OPTIONS = [
  {
    id: "risk-based",
    label: "Use a risk-based threshold",
    description: "Act on safe, reversible work. Ask before consequential actions.",
    recommended: true,
  },
  {
    id: "ask-first",
    label: "Ask before acting",
    description: "Pause when requirements or direction are not explicit.",
    recommended: false,
  },
  {
    id: "act-first",
    label: "Bias toward action",
    description: "Make reasonable assumptions and keep momentum unless risk is high.",
    recommended: false,
  },
] as const;

export type GoalId = (typeof GOAL_OPTIONS)[number]["id"];
export type ResponseStyle = (typeof RESPONSE_OPTIONS)[number]["id"] | "";
export type InitiativeStyle = (typeof INITIATIVE_OPTIONS)[number]["id"] | "";

export type Answers = {
  goals: GoalId[];
  responseStyle: ResponseStyle;
  initiative: InitiativeStyle;
  frustration: string;
};

export const EMPTY_ANSWERS: Answers = {
  goals: [],
  responseStyle: "",
  initiative: "",
  frustration: "",
};

export const PROTOTYPE_STEPS = [
  { id: "welcome", label: "Welcome", group: "Start" },
  { id: "goals", label: "Goals", group: "Know You" },
  { id: "style", label: "Style", group: "Work With You" },
  { id: "trust", label: "Trust", group: "Earn Your Trust" },
  { id: "review", label: "Review", group: "Activate" },
] as const;
