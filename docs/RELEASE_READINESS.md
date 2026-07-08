# Prompt Preflight Release Readiness Checklist

Use this checklist before publishing the VS Code extension or announcing the repo broadly.

Public release is ready only when every blocking item below is checked or explicitly deferred.

## Local quality gates

- [ ] **Python tests pass** — `python3 -m unittest discover -s tests -q` passes from the repo root.
- [ ] **VS Code extension tests pass** — `npm test` passes from `vscode-extension/`.
- [ ] **Vague prompt benchmark passes** — `python3 scripts/benchmark_vague_prompts.py --min-block-rate 0.90` passes.
- [ ] **Template docs are current** — `python3 scripts/generate_template_docs.py --check` passes.

## VS Code clean-install gates

- [ ] **Clean VSIX install works** — Install the generated VSIX into a clean VS Code profile or a machine without the dev extension.
- [ ] **Setup Doctor is green** — `Prompt Preflight: Run Setup Doctor` shows no duplicate-extension or missing-analyzer failures.
- [ ] **Core prompt check works** — A Markdown prompt with `Create a car image` opens a result tab with image-specific questions.
- [ ] **Telemetry dashboard works** — After telemetry is enabled and one check runs, `Prompt Preflight: Open Telemetry Dashboard` shows local graph data.
- [ ] **Generated-tab cleanup works** — `Prompt Preflight: Close Generated Tabs` closes result/template/composer tabs without closing normal files.

## Public packaging gates

- [ ] **Analyzer distribution decision is explicit** — Decide whether the Marketplace extension bundles the Python analyzer or requires `promptPreflight.repoPath`.
- [ ] **Publisher account and token are ready** — VS Code Marketplace publisher setup is complete and the publishing token is stored outside the repo.
- [ ] **Versioning is decided** — Choose release version, changelog format, and whether this is public beta or stable.
- [ ] **Package contents are audited** — `npm run package:list` and `npm run package:audit` include only intended extension files and exclude raw videos, node_modules, telemetry, local config, source, tests, and release tooling.

## Docs and launch gates

- [ ] **README has current demo assets** — Root README includes the GIF/image assets and describes Codex, Claude, Kiro, CLI, and VS Code support accurately.
- [ ] **VS Code README has screenshots or GIFs** — Extension README shows prompt check, suggested prompt insertion, Setup Doctor, and telemetry dashboard.
- [ ] **Install docs are external-user friendly** — Docs explain Node 20, Python 3.10+, VSIX install, repoPath, and common troubleshooting.
- [ ] **Launch copy is aligned** — `docs/LAUNCH.md` and README claims match the latest benchmark and feature status.

## Privacy and safety gates

- [ ] **Telemetry remains local and prompt-free** — Telemetry does not store prompt text, response text, suggested rewrites, questions, reason strings, or file contents.
- [ ] **Secret detection blocks and redacts** — A likely pasted credential blocks before model work and user-facing output redacts the secret.
- [ ] **Hooks fail open safely** — Codex, Claude, Kiro, and postflight hook adapters do not make the host unusable on malformed payloads.
- [ ] **No owner-specific website config is accidentally published** — AdSense snippets or other owner-only deployment settings are not committed unless intentionally building the website.

## Repo hygiene gates

- [ ] **Worktree is reviewed** — Remove, ignore, or intentionally commit scratch files, local test prompts, generated VSIX files, and repair scripts.
- [ ] **GitHub metadata is ready** — Repo description, topics, social preview, good-first-issue labels, and contribution notes are polished.
- [ ] **Issues are curated** — Open follow-up issues for known improvements without duplicating existing issues.

## Release call

- [ ] We are comfortable calling this a public beta.
- [ ] Known limitations are documented instead of hidden.
- [ ] A clean user can install, run a check, view Setup Doctor, and view telemetry without help.

When those are true, it is time to release publicly.
