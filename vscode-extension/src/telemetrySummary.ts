/**
 * Pure, dependency-free telemetry aggregation logic shared by the dashboard and
 * the export command.
 */

export interface TelemetryEvent extends Record<string, unknown> {}

export interface TelemetryDateBucket {
  date: string;
  checked: number;
  blocked: number;
  nudged: number;
  allowed: number;
}

export interface TelemetrySummary {
  schemaVersion: 1;
  generatedAt: string;
  totals: {
    promptsChecked: number;
    blocked: number;
    nudged: number;
    allowed: number;
    bypassed: number;
    followupAccepted: number;
  };
  feedbackEvents: number;
  topChecks: { check: string; count: number }[];
  decisions: Record<string, number>;
  hosts: Record<string, number>;
  intents: Record<string, number>;
  tokens: {
    eventsWithEstimates: number;
    visiblePromptTokens: number;
    estimatedRequestTokens: number;
    estimatedResponseTokens: number;
    estimatedAvoidedRetryTokenOpportunity: number;
    promptRiskBuckets: Record<string, number>;
    responseRiskBuckets: Record<string, number>;
  };
  dateBucketsAvailable: boolean;
  dateBuckets: TelemetryDateBucket[];
  postflight: {
    responsesChecked: number;
    responsesNeedingAttention: number;
    perCheck: Record<string, number>;
  };
}

/**
 * Checks whether an unknown value is a plain object-like record.
 */
function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

/**
 * Safely reads a number-like field from a telemetry object.
 */
function numberField(record: Record<string, unknown>, key: string): number {
  const value = record[key];
  return typeof value === "number" && Number.isFinite(value) ? value : 0;
}

/**
 * Safely reads a string-like field from a telemetry object.
 */
function stringField(record: Record<string, unknown>, key: string, fallback: string): string {
  const value = record[key];
  return typeof value === "string" && value.trim() ? value : fallback;
}

/**
 * Normalizes missing legacy event phases to `preflight`.
 */
function eventPhase(event: TelemetryEvent): "preflight" | "postflight" | "other" {
  const phase = stringField(event, "phase", "preflight");
  if (phase === "preflight" || phase === "postflight") {
    return phase;
  }
  return "other";
}

/**
 * Extracts check names from either preflight or postflight event shapes.
 */
function eventChecks(event: TelemetryEvent): string[] {
  const checks = event.checks;
  if (!Array.isArray(checks)) {
    return [];
  }
  return checks.filter((check): check is string => typeof check === "string" && check.trim().length > 0);
}

/**
 * Converts an ISO timestamp into a compact YYYY-MM-DD dashboard bucket.
 */
function dayBucket(event: TelemetryEvent): string {
  const timestamp = event.timestamp;
  if (typeof timestamp !== "string" || timestamp.length < 10) {
    return "unknown";
  }
  return timestamp.slice(0, 10);
}

/**
 * Adds one to a count map for the provided label.
 */
function increment(counts: Map<string, number>, label: string): void {
  counts.set(label, (counts.get(label) || 0) + 1);
}

/**
 * Summarizes parsed telemetry events for charts, KPI cards, and export.
 */
export function summarizeTelemetryEvents(events: TelemetryEvent[]): TelemetrySummary {
  const decisions = new Map<string, number>();
  const blockedByCheck = new Map<string, number>();
  const postflightBlockedByCheck = new Map<string, number>();
  const hosts = new Map<string, number>();
  const intents = new Map<string, number>();
  const dateBucketsMap = new Map<string, TelemetryDateBucket>();

  const tokens = {
    eventsWithEstimates: 0,
    visiblePromptTokens: 0,
    estimatedRequestTokens: 0,
    estimatedResponseTokens: 0,
    estimatedAvoidedRetryTokenOpportunity: 0,
    promptRiskBuckets: new Map<string, number>(),
    responseRiskBuckets: new Map<string, number>()
  };

  let promptsChecked = 0;
  let promptsBlocked = 0;
  let promptsNudged = 0;
  let promptsAllowed = 0;
  let promptsBypassed = 0;
  let followupAccepted = 0;
  let postflightResponsesChecked = 0;
  let postflightResponsesBlocked = 0;
  let hasTimestamps = false;

  for (const event of events) {
    const phase = eventPhase(event);
    const decision = stringField(event, "decision", "unknown");
    increment(hosts, stringField(event, "host", "unknown"));
    
    const day = dayBucket(event);
    if (day !== "unknown") {
      hasTimestamps = true;
      if (!dateBucketsMap.has(day)) {
        dateBucketsMap.set(day, { date: day, checked: 0, blocked: 0, nudged: 0, allowed: 0 });
      }
    }

    const tokenPayload = isRecord(event.token_observability) ? event.token_observability : undefined;
    if (tokenPayload) {
      tokens.eventsWithEstimates += 1;
      tokens.estimatedAvoidedRetryTokenOpportunity += numberField(tokenPayload, "estimated_avoided_retry_tokens");

      const prompt = isRecord(tokenPayload.prompt) ? tokenPayload.prompt : undefined;
      if (prompt) {
        tokens.visiblePromptTokens += numberField(prompt, "visible_prompt_tokens_estimate");
        tokens.estimatedRequestTokens += numberField(prompt, "estimated_total_request_tokens");
        increment(tokens.promptRiskBuckets, stringField(prompt, "token_risk", "unknown"));
      }

      const response = isRecord(tokenPayload.response) ? tokenPayload.response : undefined;
      if (response) {
        tokens.estimatedResponseTokens += numberField(response, "response_tokens_estimate");
        increment(tokens.responseRiskBuckets, stringField(response, "token_risk", "unknown"));
      }
    }

    if (phase === "preflight") {
      promptsChecked += 1;
      increment(decisions, decision);
      increment(intents, stringField(event, "intent", "unknown"));
      
      const bucket = day !== "unknown" ? dateBucketsMap.get(day) : undefined;
      if (bucket) {
        bucket.checked += 1;
      }

      if (decision === "blocked") {
        promptsBlocked += 1;
        if (bucket) { bucket.blocked += 1; }
        for (const check of eventChecks(event)) {
          increment(blockedByCheck, check);
        }
      } else if (decision === "nudged") {
        promptsNudged += 1;
        if (bucket) { bucket.nudged += 1; }
      } else if (decision === "allowed") {
        promptsAllowed += 1;
        if (bucket) { bucket.allowed += 1; }
      } else if (decision === "bypassed") {
        promptsBypassed += 1;
      } else if (decision === "followup_accepted") {
        followupAccepted += 1;
      }
    }

    if (phase === "postflight") {
      postflightResponsesChecked += 1;
      if (decision === "postflight_blocked") {
        postflightResponsesBlocked += 1;
        for (const check of eventChecks(event)) {
          increment(postflightBlockedByCheck, check);
        }
      }
    }
  }

  const topChecks = [...blockedByCheck.entries()]
    .map(([check, count]) => ({ check, count }))
    .sort((a, b) => b.count - a.count || a.check.localeCompare(b.check));

  const sortedDateBuckets = [...dateBucketsMap.values()].sort((a, b) => a.date.localeCompare(b.date));

  return {
    schemaVersion: 1,
    generatedAt: new Date().toISOString(),
    totals: {
      promptsChecked,
      blocked: promptsBlocked,
      nudged: promptsNudged,
      allowed: promptsAllowed,
      bypassed: promptsBypassed,
      followupAccepted
    },
    feedbackEvents: followupAccepted,
    topChecks,
    decisions: Object.fromEntries(decisions),
    hosts: Object.fromEntries(hosts),
    intents: Object.fromEntries(intents),
    tokens: {
      eventsWithEstimates: tokens.eventsWithEstimates,
      visiblePromptTokens: tokens.visiblePromptTokens,
      estimatedRequestTokens: tokens.estimatedRequestTokens,
      estimatedResponseTokens: tokens.estimatedResponseTokens,
      estimatedAvoidedRetryTokenOpportunity: tokens.estimatedAvoidedRetryTokenOpportunity,
      promptRiskBuckets: Object.fromEntries(tokens.promptRiskBuckets),
      responseRiskBuckets: Object.fromEntries(tokens.responseRiskBuckets)
    },
    dateBucketsAvailable: hasTimestamps,
    dateBuckets: sortedDateBuckets,
    postflight: {
      responsesChecked: postflightResponsesChecked,
      responsesNeedingAttention: postflightResponsesBlocked,
      perCheck: Object.fromEntries(postflightBlockedByCheck)
    }
  };
}
/**
 * Validates the generated JSON export structurally to ensure it contains
 * ONLY whitelisted fields. This serves as a privacy guardrail against
 * leaking raw prompt/response text or reason strings.
 */
export function validatePrivacyGuard(jsonStr: string): void {
  const parsed = JSON.parse(jsonStr) as Record<string, unknown>;

  function assertNumber(val: unknown, path: string): void {
    if (typeof val !== "number") throw new Error(`Privacy guard violation: ${path} must be a number`);
  }

  function assertString(val: unknown, path: string): void {
    if (typeof val !== "string") throw new Error(`Privacy guard violation: ${path} must be a string`);
  }

  function assertBoolean(val: unknown, path: string): void {
    if (typeof val !== "boolean") throw new Error(`Privacy guard violation: ${path} must be a boolean`);
  }

  function assertRecordOfNumbers(val: unknown, path: string): void {
    if (typeof val !== "object" || val === null || Array.isArray(val)) {
      throw new Error(`Privacy guard violation: ${path} must be an object`);
    }
    for (const [k, v] of Object.entries(val)) {
      assertNumber(v, `${path}.${k}`);
    }
  }

  function checkKeys(obj: Record<string, unknown>, allowed: string[], path: string): void {
    for (const key of Object.keys(obj)) {
      if (!allowed.includes(key)) {
        throw new Error(`Privacy guard violation: forbidden key '${key}' at ${path}`);
      }
    }
  }

  checkKeys(parsed, [
    "schemaVersion", "generatedAt", "totals", "feedbackEvents", 
    "topChecks", "decisions", "hosts", "intents", "tokens",
    "dateBucketsAvailable", "dateBuckets", "postflight"
  ], "root");

  assertNumber(parsed.schemaVersion, "schemaVersion");
  assertString(parsed.generatedAt, "generatedAt");
  assertNumber(parsed.feedbackEvents, "feedbackEvents");
  assertBoolean(parsed.dateBucketsAvailable, "dateBucketsAvailable");

  const totals = parsed.totals as Record<string, unknown>;
  checkKeys(totals, [
    "promptsChecked", "blocked", "nudged", "allowed", "bypassed", "followupAccepted"
  ], "totals");
  assertRecordOfNumbers(totals, "totals");

  const topChecks = parsed.topChecks as unknown[];
  if (!Array.isArray(topChecks)) throw new Error("Privacy guard violation: topChecks must be an array");
  for (let i = 0; i < topChecks.length; i++) {
    const item = topChecks[i] as Record<string, unknown>;
    checkKeys(item, ["check", "count"], `topChecks[${i}]`);
    assertString(item.check, `topChecks[${i}].check`);
    assertNumber(item.count, `topChecks[${i}].count`);
  }

  assertRecordOfNumbers(parsed.decisions, "decisions");
  assertRecordOfNumbers(parsed.hosts, "hosts");
  assertRecordOfNumbers(parsed.intents, "intents");

  const tokens = parsed.tokens as Record<string, unknown>;
  checkKeys(tokens, [
    "eventsWithEstimates", "visiblePromptTokens", "estimatedRequestTokens",
    "estimatedResponseTokens", "estimatedAvoidedRetryTokenOpportunity",
    "promptRiskBuckets", "responseRiskBuckets"
  ], "tokens");
  assertNumber(tokens.eventsWithEstimates, "tokens.eventsWithEstimates");
  assertNumber(tokens.visiblePromptTokens, "tokens.visiblePromptTokens");
  assertNumber(tokens.estimatedRequestTokens, "tokens.estimatedRequestTokens");
  assertNumber(tokens.estimatedResponseTokens, "tokens.estimatedResponseTokens");
  assertNumber(tokens.estimatedAvoidedRetryTokenOpportunity, "tokens.estimatedAvoidedRetryTokenOpportunity");
  assertRecordOfNumbers(tokens.promptRiskBuckets, "tokens.promptRiskBuckets");
  assertRecordOfNumbers(tokens.responseRiskBuckets, "tokens.responseRiskBuckets");

  const dateBuckets = parsed.dateBuckets as unknown[];
  if (!Array.isArray(dateBuckets)) throw new Error("Privacy guard violation: dateBuckets must be an array");
  for (let i = 0; i < dateBuckets.length; i++) {
    const item = dateBuckets[i] as Record<string, unknown>;
    checkKeys(item, ["date", "checked", "blocked", "nudged", "allowed"], `dateBuckets[${i}]`);
    assertString(item.date, `dateBuckets[${i}].date`);
    assertNumber(item.checked, `dateBuckets[${i}].checked`);
    assertNumber(item.blocked, `dateBuckets[${i}].blocked`);
    assertNumber(item.nudged, `dateBuckets[${i}].nudged`);
    assertNumber(item.allowed, `dateBuckets[${i}].allowed`);
  }

  const postflight = parsed.postflight as Record<string, unknown>;
  checkKeys(postflight, [
    "responsesChecked", "responsesNeedingAttention", "perCheck"
  ], "postflight");
  assertNumber(postflight.responsesChecked, "postflight.responsesChecked");
  assertNumber(postflight.responsesNeedingAttention, "postflight.responsesNeedingAttention");
  assertRecordOfNumbers(postflight.perCheck, "postflight.perCheck");
}

export function formatAsJson(summary: TelemetrySummary): string {
  const jsonStr = JSON.stringify(summary, null, 2);
  validatePrivacyGuard(jsonStr);
  return jsonStr;
}

export function formatAsMarkdown(summary: TelemetrySummary): string {
  const lines: string[] = [
    "# Prompt Preflight Telemetry Summary",
    "",
    `Generated at: \`${summary.generatedAt}\``,
    "",
    "## Totals",
    "",
    "| Metric | Count |",
    "|---|---|",
    `| Prompts checked | ${summary.totals.promptsChecked} |`,
    `| Blocked | ${summary.totals.blocked} |`,
    `| Nudged | ${summary.totals.nudged} |`,
    `| Allowed | ${summary.totals.allowed} |`,
    `| Bypassed | ${summary.totals.bypassed} |`,
    `| Follow-ups accepted | ${summary.totals.followupAccepted} |`,
    "",
    "## Top Checks Causing Blocks",
    "",
    summary.topChecks.length > 0
      ? "| Check | Count |\n|---|---|\n" + summary.topChecks.map(tc => `| \`${tc.check}\` | ${tc.count} |`).join("\n")
      : "No blocked prompts yet.",
    "",
    "## Decisions",
    "",
    ...Object.entries(summary.decisions).map(([k, v]) => `- \`${k}\`: ${v}`),
    "",
    "## Hosts",
    "",
    ...Object.entries(summary.hosts).map(([k, v]) => `- \`${k}\`: ${v}`),
    "",
    "## Intents",
    "",
    ...Object.entries(summary.intents).map(([k, v]) => `- \`${k}\`: ${v}`),
    "",
    "## Token Observability",
    "",
    `- Events with estimates: ${summary.tokens.eventsWithEstimates}`,
    `- Visible prompt tokens: ${summary.tokens.visiblePromptTokens}`,
    `- Estimated request tokens: ${summary.tokens.estimatedRequestTokens}`,
    `- Estimated response tokens: ${summary.tokens.estimatedResponseTokens}`,
    `- Estimated avoided retry opportunity: ${summary.tokens.estimatedAvoidedRetryTokenOpportunity}`,
    "",
    "## Date Activity",
    "",
    summary.dateBucketsAvailable && summary.dateBuckets.length > 0
      ? "| Date | Checked | Blocked | Nudged | Allowed |\n|---|---|---|---|---|\n" + summary.dateBuckets.map(b => `| ${b.date} | ${b.checked} | ${b.blocked} | ${b.nudged} | ${b.allowed} |`).join("\n")
      : "No dated events available.",
    "",
    "## Postflight",
    "",
    `- Responses checked: ${summary.postflight.responsesChecked}`,
    `- Responses needing attention: ${summary.postflight.responsesNeedingAttention}`,
    "",
    "**Postflight checks causing blocks:**",
    ...Object.entries(summary.postflight.perCheck).map(([k, v]) => `- \`${k}\`: ${v}`),
    "",
    "---",
    "",
    "**Privacy note**: This file stores only aggregate numeric counts, decisions, hosts, intents, check categories, scores, and token estimates. It does not store prompt text, suggested rewrites, questions, or reason strings."
  ];

  return lines.join("\n") + "\n";
}
