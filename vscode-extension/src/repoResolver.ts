import * as fs from "fs";
import * as path from "path";

/**
 * Relative path to the shared Python CLI inside the main prompt-preflight repo.
 */
export const PROMPT_PREFLIGHT_CLI_RELATIVE_PATH = path.join("scripts", "prompt_preflight.py");

/**
 * Inputs used to discover the main prompt-preflight repository checkout.
 */
export interface RepoPathResolutionInput {
  extensionPath: string;
  workspacePath?: string;
  configuredRepoPath?: string;
}

/**
 * Joins a repo candidate with the Python CLI path.
 */
export function cliPathForRepo(repoPath: string): string {
  return path.join(repoPath, PROMPT_PREFLIGHT_CLI_RELATIVE_PATH);
}

/**
 * Returns true when a directory looks like the main prompt-preflight checkout.
 */
export function hasPromptPreflightCli(repoPath: string): boolean {
  return fs.existsSync(cliPathForRepo(repoPath));
}

/**
 * Adds a candidate path once, preserving resolution priority.
 */
function addCandidate(candidates: string[], candidate?: string): void {
  if (!candidate || !candidate.trim()) {
    return;
  }
  const resolved = path.resolve(candidate.trim());
  if (!candidates.includes(resolved)) {
    candidates.push(resolved);
  }
}

/**
 * Builds the ordered list of places where the extension should look for the
 * main repo. This supports local development, installed VSIX usage, and users
 * who open the parent folder that contains `prompt-preflight`.
 */
export function repoPathCandidates(input: RepoPathResolutionInput): string[] {
  const candidates: string[] = [];

  addCandidate(candidates, input.configuredRepoPath);
  addCandidate(candidates, input.workspacePath);
  if (input.workspacePath) {
    addCandidate(candidates, path.join(input.workspacePath, "prompt-preflight"));
  }

  // Development layout:
  // prompt-preflight/
  //   vscode-extension/
  addCandidate(candidates, path.resolve(input.extensionPath, ".."));

  // Future packaged layout fallback if the Python analyzer is bundled later.
  addCandidate(candidates, input.extensionPath);

  return candidates;
}

/**
 * Finds the first candidate that contains the shared Python analyzer. If none
 * match, return the first candidate so the caller can build a precise error.
 */
export function resolveRepoPathFromCandidates(input: RepoPathResolutionInput): string {
  const candidates = repoPathCandidates(input);
  return candidates.find(hasPromptPreflightCli) || candidates[0] || path.resolve(input.extensionPath, "..");
}
