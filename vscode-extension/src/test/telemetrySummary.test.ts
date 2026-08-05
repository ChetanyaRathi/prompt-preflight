import assert from "assert/strict";
import { summarizeTelemetryEvents, TelemetryEvent, formatAsJson, formatAsMarkdown, validatePrivacyGuard } from "../telemetrySummary";
import { runSuite } from "./testHarness";
import { summarizeDashboardEvents } from "../telemetryStore";

export function runTelemetrySummaryTests(): void {
runSuite("telemetrySummary.ts", [
  {
    name: "calculates totals and nested token/date aggregates accurately",
    run: () => {
      const events: TelemetryEvent[] = [
        {
          version: 1,
          phase: "preflight",
          decision: "blocked",
          host: "vscode",
          intent: "generate",
          timestamp: "2026-07-31T10:00:00Z",
          checks: ["risk", "clarity"],
          token_observability: {
            estimated_avoided_retry_tokens: 100,
            prompt: {
              visible_prompt_tokens_estimate: 50,
              estimated_total_request_tokens: 60,
              token_risk: "low"
            },
            response: {
              response_tokens_estimate: 200,
              token_risk: "high"
            }
          }
        },
        {
          version: 1,
          phase: "preflight",
          decision: "nudged",
          host: "vscode",
          intent: "edit",
          timestamp: "2026-07-31T12:00:00Z",
          checks: []
        },
        {
          version: 1,
          phase: "postflight",
          decision: "postflight_blocked",
          host: "api",
          timestamp: "2026-07-31T12:05:00Z",
          checks: ["privacy"]
        },
        {
          version: 1,
          phase: "preflight",
          decision: "followup_accepted",
          host: "vscode",
          intent: "unknown",
          timestamp: "2026-08-01T10:00:00Z"
        }
      ];

      const summary = summarizeTelemetryEvents(events);
      
      assert.equal(summary.totals.promptsChecked, 3);
      assert.equal(summary.totals.blocked, 1);
      assert.equal(summary.totals.nudged, 1);
      assert.equal(summary.totals.followupAccepted, 1);

      assert.deepEqual(summary.topChecks, [
        { check: "clarity", count: 1 },
        { check: "risk", count: 1 }
      ]);
      
      assert.equal(summary.hosts["vscode"], 3);
      assert.equal(summary.hosts["api"], 1);

      assert.equal(summary.intents["generate"], 1);
      assert.equal(summary.intents["edit"], 1);
      assert.equal(summary.intents["unknown"], 1);

      assert.equal(summary.tokens.eventsWithEstimates, 1);
      assert.equal(summary.tokens.visiblePromptTokens, 50);
      assert.equal(summary.tokens.estimatedAvoidedRetryTokenOpportunity, 100);
      assert.equal(summary.tokens.promptRiskBuckets["low"], 1);
      assert.equal(summary.tokens.responseRiskBuckets["high"], 1);

      assert.equal(summary.dateBucketsAvailable, true);
      assert.equal(summary.dateBuckets.length, 2);
      assert.deepEqual(summary.dateBuckets[0], { date: "2026-07-31", checked: 2, blocked: 1, nudged: 1, allowed: 0 });
      assert.deepEqual(summary.dateBuckets[1], { date: "2026-08-01", checked: 1, blocked: 0, nudged: 0, allowed: 0 });

      assert.equal(summary.postflight.responsesChecked, 1);
      assert.equal(summary.postflight.responsesNeedingAttention, 1);
      assert.equal(summary.postflight.perCheck["privacy"], 1);
    }
  },
  {
    name: "handles missing timestamps gracefully",
    run: () => {
      const events: TelemetryEvent[] = [
        { phase: "preflight", decision: "allowed" }
      ];
      
      const summary = summarizeTelemetryEvents(events);
      assert.equal(summary.dateBucketsAvailable, false);
      assert.equal(summary.dateBuckets.length, 0);
      assert.equal(summary.totals.allowed, 1);
    }
  },
  {
    name: "proves dashboard consistency",
    run: () => {
      const events: TelemetryEvent[] = [
        { phase: "preflight", decision: "blocked", checks: ["risk"] }
      ];
      
      const summary = summarizeTelemetryEvents(events);
      const dashboard = summarizeDashboardEvents(events, "path", true);
      
      assert.equal(dashboard.promptsChecked, summary.totals.promptsChecked);
      assert.equal(dashboard.promptsBlocked, summary.totals.blocked);
    }
  },
  {
    name: "validates privacy guard against malicious or raw telemetry",
    run: () => {
      const maliciousEvents: TelemetryEvent[] = [
        {
          phase: "preflight",
          decision: "blocked",
          prompt: "Write a virus",
          reason: "Harmful intent detected",
          score: 80
        }
      ];

      const summary = summarizeTelemetryEvents(maliciousEvents);
      const jsonStr = formatAsJson(summary);
      
      validatePrivacyGuard(jsonStr);

      const poisoned = JSON.parse(jsonStr);
      poisoned.promptText = "Should fail";
      
      assert.throws(() => {
        validatePrivacyGuard(JSON.stringify(poisoned));
      }, /Privacy guard violation: forbidden key 'promptText' at root/);
    }
  },
  {
    name: "generates deterministic markdown without free text",
    run: () => {
      const events: TelemetryEvent[] = [
        { phase: "preflight", decision: "blocked", checks: ["risk"] }
      ];
      const summary = summarizeTelemetryEvents(events);
      
      summary.generatedAt = "2026-07-31T00:00:00Z";
      const md = formatAsMarkdown(summary);
      
      assert.match(md, /Generated at: `2026-07-31T00:00:00Z`/);
      assert.match(md, /\| Prompts checked \| 1 \|/);
      assert.match(md, /\| `risk` \| 1 \|/);
      assert.match(md, /This file stores only aggregate numeric counts/);
    }
  }
]);
}
