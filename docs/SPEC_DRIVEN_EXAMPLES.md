# Spec-Driven Development Examples

Prompt Preflight supports structured templates for a "spec-driven" AI development workflow. This workflow breaks large tasks into manageable steps: defining the feature (`feature_spec`), planning the changes (`implementation_plan`), and executing the code (`agent_execution_prompt`).

All templates can be authored in Markdown, TOML, or XML formats.

## End-to-End Workflow: Adding a CSV Export

This example demonstrates how to thread context through the templates for a generic feature: adding a CSV export to a reports page. The output of one template becomes the input or context for the next.

### Step 1: Feature Spec (Markdown)

First, write a `feature_spec` to define what needs to be built and why. This clarifies the requirements before writing any code.

```md
<!-- profile: feature_spec -->

# Problem Statement
Users need to export their weekly analytics reports to load into internal BI tools. Currently, they have to copy-paste the table manually.

# Goals
- Allow users to download the currently viewed report table as a CSV file.
- The CSV structure must match the columns visible on screen.

# Target Users
Account managers and data analysts who use the reports dashboard.

# Functional Requirements
- Add a "Download CSV" button next to the date picker on the reports page.
- Clicking the button triggers a download of a `.csv` file.

# Acceptance Criteria
- Clicking "Download CSV" downloads a valid CSV file.
- The CSV file contains the exact rows and columns currently active in the table, respecting any applied filters.

# Constraints
- Preserve the existing table component layout and styling.
- Do not change the underlying reporting API.
```

### Step 2: Implementation Plan (TOML)

Next, the developer or a planning agent reads the feature spec and writes an `implementation_plan`. This plan proposes a safe sequence of technical changes. Here, we use the TOML format to demonstrate multi-format support.

```toml
profile = "implementation_plan"
task = "Add CSV export to the Reports page, as defined in the feature spec."
phases = [
  "Create a utility function to convert table data to CSV format.",
  "Add the Download button to the Reports UI and wire it to the utility."
]
implementation_steps = [
  "Add `exportToCsv` function in `src/utils/csv.ts`.",
  "Write unit tests for `exportToCsv` in `src/utils/csv.test.ts`.",
  "Update `src/components/ReportsPage.tsx` to include the download button."
]
dependencies = [
  "Requires the existing `ReportData` type from `src/types/reports.ts`."
]
verification_plan = "Run `npm run test` and verify the new `csv.test.ts` passes. Manually test the button in the local dev server."
rollback_plan = "Revert the commit in `src/components/ReportsPage.tsx` to remove the button."
```

### Step 3: Agent Execution Prompt (Markdown)

Finally, provide an `agent_execution_prompt` to your AI coding agent (like Claude Code, Cursor, or Aider). Notice how it references the feature spec and incorporates the exact steps from the implementation plan.

```md
<!-- profile: agent_execution_prompt -->

# Task
Implement the CSV export feature for the Reports page.

# Source Spec
The feature spec requires adding a "Download CSV" button that exports the active table data.

# Scope
- `src/utils/csv.ts` (new)
- `src/utils/csv.test.ts` (new)
- `src/components/ReportsPage.tsx`

# Constraints
- Preserve the existing table component layout and styling.
- Do not touch the backend API or routing logic.

# Implementation Plan
- Add `exportToCsv` function in `src/utils/csv.ts`.
- Write unit tests for `exportToCsv` in `src/utils/csv.test.ts`.
- Update `src/components/ReportsPage.tsx` to include the download button next to the date picker.

# Verification Plan
Run `npm run test src/utils/csv.test.ts` and verify it passes.

# Output Format
Patch plus a short summary of the changes made.
```
