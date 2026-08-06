# Config JSON Schema

Prompt Preflight ships a JSON Schema for project policy files:

- Schema: [`schemas/prompt-preflight.schema.json`](../schemas/prompt-preflight.schema.json)
- Example: [`.prompt-preflight.example.json`](../.prompt-preflight.example.json)

## Autocomplete and validation

The VS Code extension contributes `jsonValidation` for:

- `.prompt-preflight.json`
- `.prompt-preflight.example.json`

The schema is bundled into the packaged extension (under `bundled-analyzer/schemas/`) so validation works in Marketplace installs, not only in a checkout of this repo. Editors that support Draft 2020-12 will offer property completion and flag invalid enum values (for example a bad `checks.*` policy).

## Profiles

Config-level `profiles` are not part of this schema. The runtime loader (`config.py`) does not read a `profiles` key from `.prompt-preflight.json` today, so the schema intentionally covers only keys that are actually loaded. If config-level profiles are added to the runtime later, the schema and this doc will be updated to match the shape the loader consumes.
