# Changelog

## [Unreleased]

### Added
- Six spec-driven template commands that open a chosen template directly from the Command Palette: **New Feature Spec**, **New Requirements Spec**, **New Technical Design Spec**, **New Implementation Plan**, **New Agent Execution Prompt**, and **New Spec Review Checklist**. Each prompts for Markdown / TOML / XML and opens an untitled document without modifying the active editor.

## 0.0.2

- Adds Marketplace beta positioning and packaged README/demo polish.
- Adds `Prompt Preflight: New Prompt Template`, which asks users to choose Markdown, TOML, or XML before selecting a template profile.
- Adds spec-driven development templates for feature specs, requirements specs, technical design specs, implementation plans, agent execution prompts, and spec review checklists.
- Keeps the bundled Python analyzer in the VSIX so Marketplace users do not need `promptPreflight.repoPath`.

## 0.0.1

- Initial local-development VS Code extension.
- Adds prompt checks, Markdown CodeLens, suggested prompt insertion, Prompt Composer, template commands, diagnostics, workspace prompt lint, team policy template, and generated-tab cleanup.
- Adds VSIX packaging metadata and package scripts.
