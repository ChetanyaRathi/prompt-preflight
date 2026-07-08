import assert from "assert/strict";
import { TEAM_POLICY_FILE_NAME, teamPolicyDocumentSpec, teamPolicyTemplateText } from "../policyDocument";
import { runSuite } from "./testHarness";

/**
 * Unit tests for the team policy document template.
 */
export function runPolicyDocumentTests(): void {
  runSuite("policyDocument", [
    /**
     * Verifies the expected policy file name is stable.
     */
    {
      name: "uses the standard team policy file name",
      run: () => {
        assert.equal(TEAM_POLICY_FILE_NAME, ".prompt-preflight.json");
      }
    },

    /**
     * Verifies the team policy template is valid JSON with expected defaults.
     */
    {
      name: "creates a valid default team policy template",
      run: () => {
        const parsed = JSON.parse(teamPolicyTemplateText()) as {
          enabled: boolean;
          mode: string;
          threshold: number;
          checks: Record<string, string>;
          token_observability: {
            enabled: boolean;
            default_max_output_tokens: number;
            estimated_retry_output_tokens: number;
          };
        };

        assert.equal(parsed.enabled, true);
        assert.equal(parsed.mode, "block");
        assert.equal(parsed.threshold, 45);
        assert.equal(parsed.checks.privacy, "block");
        assert.equal(parsed.checks.clarity, "nudge");
        assert.equal(parsed.token_observability.enabled, true);
        assert.equal(parsed.token_observability.default_max_output_tokens, 1000);
        assert.equal(parsed.token_observability.estimated_retry_output_tokens, 800);
      }
    },

    /**
     * Verifies the policy template opens as JSON content.
     */
    {
      name: "builds a JSON document spec",
      run: () => {
        const spec = teamPolicyDocumentSpec();

        assert.equal(spec.language, "json");
        assert.match(spec.content, /"severity_thresholds"/);
      }
    }
  ]);
}
