import * as fs from "fs";
import * as path from "path";
import * as vscode from "vscode";

/**
 * Command identifier used by diagnostics and command registration to open the
 * Prompt Preflight examples document.
 */
export const OPEN_EXAMPLES_COMMAND = "promptPreflight.openExamples";

/**
 * Finds the Prompt Preflight repository checkout that contains the examples doc.
 */
function resolveRepoPath(extensionPath: string): string {
  const configuredRepoPath = vscode.workspace
    .getConfiguration("promptPreflight")
    .get<string>("repoPath", "")
    .trim();
  return configuredRepoPath || path.resolve(extensionPath, "..");
}

/**
 * Builds the absolute path to the bundled examples document.
 */
function examplesPath(extensionPath: string): string {
  return path.join(resolveRepoPath(extensionPath), "docs", "EXAMPLES.md");
}

/**
 * Opens the bundled prompt examples document beside the user's current editor.
 */
export async function openPromptExamples(context: vscode.ExtensionContext): Promise<void> {
  const filePath = examplesPath(context.extensionPath);
  if (!fs.existsSync(filePath)) {
    void vscode.window.showErrorMessage(
      `Prompt Preflight: could not find examples at ${filePath}. Set promptPreflight.repoPath to your prompt-preflight checkout.`
    );
    return;
  }

  const document = await vscode.workspace.openTextDocument(vscode.Uri.file(filePath));
  await vscode.window.showTextDocument(document, vscode.ViewColumn.Beside);
}
