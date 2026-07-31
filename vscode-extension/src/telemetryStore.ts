import * as fs from "fs";
import * as os from "os";
import * as path from "path";
import { TelemetryEvent, TelemetrySummary, summarizeTelemetryEvents } from "./telemetrySummary";

export { TelemetryEvent };

/**
 * Default local telemetry file name used by the Python CLI and host hooks.
 */
export const DEFAULT_TELEMETRY_FILE_NAME = ".prompt-preflight-telemetry.jsonl";

/**
 * Describes where the extension should read telemetry and whether new VS Code
 * checks should append events.
 */
export interface TelemetryPolicy {
  enabled: boolean;
  telemetryPath: string;
  source: "workspace-policy" | "default";
}

/**
 * Summarizes one bar in a dashboard chart.
 */
export interface TelemetryBar {
  label: string;
  value: number;
}

/**
 * Token totals shown in the dashboard. Values are estimates, not billing truth.
 */
export interface TokenTelemetrySummary {
  eventsWithEstimates: number;
  visiblePromptTokensEstimateTotal: number;
  estimatedRequestTokensTotal: number;
  responseTokensEstimateTotal: number;
  estimatedAvoidedRetryTokens: number;
  promptRisk: TelemetryBar[];
  responseRisk: TelemetryBar[];
}

/**
 * Aggregated telemetry data used by the webview dashboard.
 */
export interface TelemetryDashboardSummary {
  telemetryPath: string;
  telemetryEnabled: boolean;
  policySource: "workspace-policy" | "default";
  eventsRead: number;
  malformedLines: number;
  promptsChecked: number;
  promptsBlocked: number;
  promptsNudged: number;
  promptsAllowed: number;
  promptsBypassed: number;
  followupsAccepted: number;
  postflightResponsesChecked: number;
  postflightResponsesBlocked: number;
  decisions: TelemetryBar[];
  blockedByCheck: TelemetryBar[];
  postflightBlockedByCheck: TelemetryBar[];
  hosts: TelemetryBar[];
  dailyEvents: TelemetryBar[];
  tokens: TokenTelemetrySummary;
}

/**
 * Parses a JSON-like object section from `.prompt-preflight.json`.
 */
function readJsonObject(filePath: string): Record<string, unknown> | undefined {
  if (!fs.existsSync(filePath)) {
    return undefined;
  }

  try {
    const parsed = JSON.parse(fs.readFileSync(filePath, "utf8"));
    return isRecord(parsed) ? parsed : undefined;
  } catch {
    return undefined;
  }
}

/**
 * Checks whether an unknown value is a plain object-like record.
 */
function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

/**
 * Summarizes parsed telemetry events for charts and KPI cards.
 */
export function summarizeDashboardEvents(
  events: TelemetryEvent[],
  telemetryPath: string,
  telemetryEnabled: boolean,
  malformedLines = 0,
  policySource: "workspace-policy" | "default" = "default"
): TelemetryDashboardSummary {
  const summary = summarizeTelemetryEvents(events);
  
  const tokens: TokenTelemetrySummary = {
    eventsWithEstimates: summary.tokens.eventsWithEstimates,
    visiblePromptTokensEstimateTotal: summary.tokens.visiblePromptTokens,
    estimatedRequestTokensTotal: summary.tokens.estimatedRequestTokens,
    responseTokensEstimateTotal: summary.tokens.estimatedResponseTokens,
    estimatedAvoidedRetryTokens: summary.tokens.estimatedAvoidedRetryTokenOpportunity,
    promptRisk: barsFromRecord(summary.tokens.promptRiskBuckets),
    responseRisk: barsFromRecord(summary.tokens.responseRiskBuckets)
  };

  return {
    telemetryPath,
    telemetryEnabled,
    policySource,
    eventsRead: events.length,
    malformedLines,
    promptsChecked: summary.totals.promptsChecked,
    promptsBlocked: summary.totals.blocked,
    promptsNudged: summary.totals.nudged,
    promptsAllowed: summary.totals.allowed,
    promptsBypassed: summary.totals.bypassed,
    followupsAccepted: summary.totals.followupAccepted,
    postflightResponsesChecked: summary.postflight.responsesChecked,
    postflightResponsesBlocked: summary.postflight.responsesNeedingAttention,
    decisions: barsFromRecord(summary.decisions),
    blockedByCheck: summary.topChecks.map(tc => ({ label: tc.check, value: tc.count })),
    postflightBlockedByCheck: barsFromRecord(summary.postflight.perCheck),
    hosts: barsFromRecord(summary.hosts),
    dailyEvents: summary.dateBuckets.map(db => ({ label: db.date, value: db.checked })),
    tokens
  };
}

/**
 * Loads and summarizes telemetry for one workspace root.
 */
export function loadTelemetryDashboardSummary(workspacePath: string): TelemetryDashboardSummary {
  const policy = resolveTelemetryPolicy(workspacePath);
  const parsed = readTelemetryFile(policy.telemetryPath);
  return summarizeDashboardEvents(
    parsed.events,
    policy.telemetryPath,
    policy.enabled,
    parsed.malformedLines,
    policy.source
  );
}

/**
 * Resolves a configured telemetry path relative to the workspace root.
 */
function resolveTelemetryFilePath(workspacePath: string, configuredPath: unknown): string {
  const rawPath = typeof configuredPath === "string" && configuredPath.trim()
    ? configuredPath.trim()
    : DEFAULT_TELEMETRY_FILE_NAME;
  const expandedPath = rawPath === "~" || rawPath.startsWith("~/")
    ? path.join(os.homedir(), rawPath.slice(2))
    : rawPath;
  return path.isAbsolute(expandedPath) ? expandedPath : path.join(workspacePath, expandedPath);
}

/**
 * Reads telemetry policy from `.prompt-preflight.json`, falling back to the
 * default local JSONL path when no policy exists.
 */
export function resolveTelemetryPolicy(workspacePath: string): TelemetryPolicy {
  const policyPath = path.join(workspacePath, ".prompt-preflight.json");
  const policy = readJsonObject(policyPath);

  if (!policy) {
    return {
      enabled: false,
      telemetryPath: path.join(workspacePath, DEFAULT_TELEMETRY_FILE_NAME),
      source: "default"
    };
  }

  const telemetry = policy.telemetry;
  if (isRecord(telemetry)) {
    return {
      enabled: Boolean(telemetry.enabled),
      telemetryPath: resolveTelemetryFilePath(workspacePath, telemetry.path),
      source: "workspace-policy"
    };
  }

  return {
    enabled: Boolean(telemetry),
    telemetryPath: resolveTelemetryFilePath(workspacePath, undefined),
    source: "workspace-policy"
  };
}

/**
 * Returns true when VS Code prompt checks should append local telemetry events.
 */
export function shouldRecordTelemetry(workspacePath?: string): boolean {
  if (!workspacePath) {
    return false;
  }
  return resolveTelemetryPolicy(workspacePath).enabled;
}

/**
 * Parses JSONL telemetry text while counting malformed lines for diagnostics.
 */
export function parseTelemetryJsonl(text: string): { events: TelemetryEvent[]; malformedLines: number } {
  const events: TelemetryEvent[] = [];
  let malformedLines = 0;

  for (const line of text.split(/\r?\n/)) {
    if (!line.trim()) {
      continue;
    }
    try {
      const parsed = JSON.parse(line);
      if (isRecord(parsed)) {
        events.push(parsed as TelemetryEvent);
      } else {
        malformedLines += 1;
      }
    } catch {
      malformedLines += 1;
    }
  }

  return { events, malformedLines };
}

/**
 * Reads events from the local telemetry file, returning an empty set if the file
 * has not been created yet.
 */
export function readTelemetryFile(filePath: string): { events: TelemetryEvent[]; malformedLines: number } {
  if (!fs.existsSync(filePath)) {
    return { events: [], malformedLines: 0 };
  }
  return parseTelemetryJsonl(fs.readFileSync(filePath, "utf8"));
}

/**
 * Converts a record of counts into sorted chart bars.
 */
function barsFromRecord(counts: Record<string, number>): TelemetryBar[] {
  return Object.entries(counts)
    .map(([label, value]) => ({ label, value }))
    .sort((left, right) => right.value - left.value || left.label.localeCompare(right.label));
}
