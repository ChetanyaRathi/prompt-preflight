# Software / agent work contract

## MD

```md
# Task
[Build/fix/change/refactor specific thing]

# Scope / Context
[Files, components, issue, current behavior, logs, API, or existing code to use]

# Constraints
- Preserve [behavior/API/data/design]
- Do not change [out-of-scope area]

# Output Format
[Patch, plan, table, diff summary, commands, docs, screenshots, etc.]

# Success Criteria
- [Test, command, acceptance criterion, or observable behavior]
- [How to know the work is complete]

# Optional
- Platform/stack: [language/framework/service]
- Plan-first: [when to inspect and wait for confirmation]
- Non-goals: [what not to touch]
```

## XML

```xml
<prompt profile="software">
  <task>[Build/fix/change/refactor specific thing]</task>
  <scope>[Files, components, issue, current behavior, logs, API, or existing code to use]</scope>
  <constraints>
    <item>Preserve [behavior/API/data/design]</item>
    <item>Do not change [out-of-scope area]</item>
  </constraints>
  <output_format>[Patch, plan, table, diff summary, commands, docs, screenshots, etc.]</output_format>
  <success_criteria>
    <item>[Test, command, acceptance criterion, or observable behavior]</item>
    <item>[How to know the work is complete]</item>
  </success_criteria>
  <plan_first>[Optional approval boundary for risky work]</plan_first>
</prompt>
```

## TOML

```toml
profile = "software"
task = "[Build/fix/change/refactor specific thing]"
scope = "[Files, components, issue, current behavior, logs, API, or existing code to use]"
constraints = [
  "Preserve [behavior/API/data/design]",
  "Do not change [out-of-scope area]"
]
output_format = "[Patch, plan, table, diff summary, commands, docs, screenshots, etc.]"
success_criteria = [
  "[Test, command, acceptance criterion, or observable behavior]",
  "[How to know the work is complete]"
]
plan_first = "[Optional approval boundary for risky work]"
```
