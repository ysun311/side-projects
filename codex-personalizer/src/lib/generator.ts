import { type Answers } from "@/lib/questionnaire";

const RESPONSE_RULES = {
  concise: [
    "Lead with the outcome and keep responses concise by default.",
    "Add detail only when it changes the decision or I ask for it.",
  ],
  balanced: [
    "Lead with the outcome, then give the key reasoning and practical next steps.",
    "Use enough detail to make the answer actionable without turning it into a manual.",
  ],
  detailed: [
    "Explain the reasoning, relevant context, tradeoffs, and concrete examples.",
    "Teach unfamiliar concepts without assuming I already know the terminology.",
  ],
} as const;

const INITIATIVE_RULES = {
  "risk-based": [
    "Act without asking on safe, reversible work that stays within the requested scope.",
    "Ask before consequential, destructive, external, or materially scope-changing actions.",
  ],
  "ask-first": [
    "Ask a concise clarifying question before acting when requirements or direction are ambiguous.",
  ],
  "act-first": [
    "Make reasonable assumptions and maintain momentum unless the action is consequential or hard to reverse.",
    "State assumptions that materially affect the result.",
  ],
} as const;

const PROJECT_SPECIFIC_PATTERN =
  /\b(npm|pnpm|yarn|pytest|next\.js|react|typescript|tailwind|framework|repository|repo|database schema|api route)\b|(?:^|\s)(?:src|app|packages)\//i;

export type GenerationResult = {
  markdown: string;
  warnings: string[];
  routedElsewhere: string[];
};

function customFrictionRule(value: string) {
  const normalized = value.replace(/\s+/g, " ").trim();
  const meaningfulWords = normalized.match(/[a-z]{2,}/gi) ?? [];

  if (meaningfulWords.length < 4) return null;

  if (
    /(?:ask|asking).*(?:approval|permission|confirm).*(?:safe|local|sandbox|reversible)|(?:safe|local|sandbox|reversible).*(?:ask|asking).*(?:approval|permission|confirm)/i.test(
      normalized,
    )
  ) {
    return "Do not ask for approval for safe, reversible work within a local sandbox; proceed and report what changed.";
  }

  if (/too (?:long|verbose)|over.?explain|wall of text/i.test(normalized)) {
    return "Avoid over-explaining; give the answer first and expand only when the extra detail is useful.";
  }

  if (/made up|hallucinat|invented|fabricat/i.test(normalized)) {
    return "Never invent missing facts; distinguish verified information, inference, and uncertainty.";
  }

  return `Avoid repeating this behavior: ${normalized.slice(0, 220).replace(/[.!?]?$/, ".")}`;
}

export function generateGuidance(answers: Answers): GenerationResult {
  const sections: string[] = [
    "# Global personal guidance",
    "",
    "> This file applies across every repository. Project-specific frameworks, commands, architecture, paths, and team conventions belong in that repository's `AGENTS.md`.",
  ];
  const warnings: string[] = [];
  const routedElsewhere: string[] = [];

  // Broad goal categories help tailor the questionnaire, but they are not
  // specific enough to deserve permanent space in a global AGENTS.md.

  if (answers.responseStyle) {
    sections.push(
      "",
      "## Communication",
      "",
      ...RESPONSE_RULES[answers.responseStyle].map((rule) => `- ${rule}`),
    );
  }

  if (answers.initiative) {
    sections.push(
      "",
      "## Collaboration and initiative",
      "",
      ...INITIATIVE_RULES[answers.initiative].map((rule) => `- ${rule}`),
    );
  }

  const frustration = answers.frustration.trim();
  if (frustration) {
    if (PROJECT_SPECIFIC_PATTERN.test(frustration)) {
      routedElsewhere.push(frustration);
      warnings.push(
        "One custom answer looks project-specific, so it was routed out of the global file.",
      );
    } else {
      const frictionRule = customFrictionRule(frustration);
      if (frictionRule) {
        sections.push(
          "",
          "## Avoid recurring friction",
          "",
          `- ${frictionRule}`,
        );
      } else {
        warnings.push(
          "One custom answer was too vague to turn into durable global guidance, so it was left out.",
        );
      }
    }
  }

  sections.push(
    "",
    "## Maintaining these instructions",
    "",
    "- Suggest a global instruction only after an explicit correction or repeated cross-project preference.",
    "- Never change this file without showing me the proposed diff and receiving my approval.",
  );

  return {
    markdown: `${sections.join("\n")}\n`,
    warnings,
    routedElsewhere,
  };
}
