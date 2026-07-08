import * as path from "path";
import * as vscode from "vscode";
import { trackGeneratedPromptDocument } from "./generatedTabs";
import { TEAM_POLICY_FILE_NAME, teamPolicyDocumentSpec } from "./policyDocument";

/**
 * Opens the workspace Prompt Preflight team policy, or creates an untitled
 * policy template when the workspace does not have one yet.
 */
export async function openTeamPolicy(): Promise<void> {
  const folder = vscode.workspace.workspaceFolders?.[0];
  if (!folder) {
    await openUntitledPolicyTemplate();
    return;
  }

  const policyUri = vscode.Uri.file(path.join(folder.uri.fsPath, TEAM_POLICY_FILE_NAME));
  if (await fileExists(policyUri)) {
    const document = await vscode.workspace.openTextDocument(policyUri);
    await vscode.window.showTextDocument(document, vscode.ViewColumn.Beside);
    return;
  }

  await openUntitledPolicyTemplate();
  void vscode.window.showInformationMessage(
    `Prompt Preflight: save this template as ${TEAM_POLICY_FILE_NAME} in your workspace root to share the policy with your team.`
  );
}

/**
 * Opens a new untitled JSON document with the default team policy content.
 */
async function openUntitledPolicyTemplate(): Promise<void> {
  const spec = teamPolicyDocumentSpec();
  const document = await vscode.workspace.openTextDocument({
    language: spec.language,
    content: spec.content
  });
  trackGeneratedPromptDocument(document, "policy");
  await vscode.window.showTextDocument(document, vscode.ViewColumn.Beside);
}

/**
 * Checks whether a VS Code URI points to an existing file.
 */
async function fileExists(uri: vscode.Uri): Promise<boolean> {
  try {
    const stat = await vscode.workspace.fs.stat(uri);
    return stat.type === vscode.FileType.File;
  } catch {
    return false;
  }
}
