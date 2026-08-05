import * as vscode from "vscode";
import { resolveTelemetryPolicy, readTelemetryFile } from "./telemetryStore";
import { summarizeTelemetryEvents, formatAsJson, formatAsMarkdown } from "./telemetrySummary";

/**
 * Handles the "Prompt Preflight: Export Telemetry Summary" command.
 */
export async function exportTelemetrySummary(workspacePath?: string): Promise<void> {
  if (!workspacePath) {
    void vscode.window.showWarningMessage("Prompt Preflight: open a workspace folder before exporting telemetry.");
    return;
  }

  const policy = resolveTelemetryPolicy(workspacePath);
  const parsed = readTelemetryFile(policy.telemetryPath);

  if (parsed.events.length === 0) {
    void vscode.window.showInformationMessage("Prompt Preflight: No telemetry recorded yet...");
    return;
  }

  const summary = summarizeTelemetryEvents(parsed.events);

  const format = await vscode.window.showQuickPick(["JSON", "Markdown", "Both"], {
    title: "Select Export Format"
  });

  if (!format) {
    return;
  }

  const dateStr = new Date().toISOString().split("T")[0];
  const defaultUri = vscode.Uri.file(`${workspacePath}/prompt-preflight-telemetry-summary-${dateStr}.json`);

  const saveUri = await vscode.window.showSaveDialog({
    title: "Export Telemetry Summary",
    defaultUri: defaultUri,
    filters: {
      "JSON": ["json"],
      "Markdown": ["md"],
      "All Files": ["*"]
    }
  });

  if (!saveUri) {
    return;
  }

  const fs = vscode.workspace.fs;
  const basePath = saveUri.fsPath.replace(/\.(json|md)$/i, "");
  
  const wroteFiles: vscode.Uri[] = [];

  if (format === "JSON" || format === "Both") {
    const jsonPath = vscode.Uri.file(`${basePath}.json`);
    const jsonStr = formatAsJson(summary);
    await fs.writeFile(jsonPath, Buffer.from(jsonStr, "utf8"));
    wroteFiles.push(jsonPath);
  }

  if (format === "Markdown" || format === "Both") {
    const mdPath = vscode.Uri.file(`${basePath}.md`);
    const mdStr = formatAsMarkdown(summary);
    await fs.writeFile(mdPath, Buffer.from(mdStr, "utf8"));
    wroteFiles.push(mdPath);
  }

  const action = await vscode.window.showInformationMessage(
    `Prompt Preflight: Exported telemetry summary successfully.`,
    "Reveal in Explorer", "Open File"
  );

  if (action === "Reveal in Explorer") {
    void vscode.commands.executeCommand("revealFileInOS", wroteFiles[0]);
  } else if (action === "Open File") {
    for (const uri of wroteFiles) {
      void vscode.window.showTextDocument(uri, { preview: false });
    }
  }
}
