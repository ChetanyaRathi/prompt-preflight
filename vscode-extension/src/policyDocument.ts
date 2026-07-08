/**
 * Standard repo-level Prompt Preflight policy file name.
 */
export const TEAM_POLICY_FILE_NAME = ".prompt-preflight.json";

/**
 * Plain document spec for opening a new team policy template.
 */
export interface TeamPolicyDocumentSpec {
  language: string;
  content: string;
}

/**
 * Builds a copy-pasteable default team policy JSON template.
 */
export function teamPolicyTemplateText(): string {
  return `${JSON.stringify(
    {
      enabled: true,
      mode: "block",
      threshold: 45,
      max_questions: 3,
      checks: {
        clarity: "nudge",
        context: "nudge",
        output_contract: "nudge",
        template_contract: "block",
        risk: "block",
        plan_first: "block",
        privacy: "block"
      },
      severity_thresholds: {
        block: "high",
        nudge: "medium"
      },
      telemetry: {
        enabled: false,
        path: ".prompt-preflight-telemetry.jsonl"
      },
      token_observability: {
        enabled: true,
        default_max_output_tokens: 1000,
        estimated_retry_output_tokens: 800
      }
    },
    null,
    2
  )}\n`;
}

/**
 * Builds the untitled document spec shown when a workspace has no team policy
 * file yet.
 */
export function teamPolicyDocumentSpec(): TeamPolicyDocumentSpec {
  return {
    language: "json",
    content: teamPolicyTemplateText()
  };
}
