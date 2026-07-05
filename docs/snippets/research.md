# Research contract

## MD

```md
# Research Question
[Specific question or decision the research should answer]

# Scope
[Date range, geography, audience, exclusions, and depth]

# Sources
[Official docs, papers, credible sources, links, or allowed source types]

# Criteria
[How options should be compared: cost, features, risks, tradeoffs, etc.]

# Output Format
[Brief, table, memo, recommendation, citations, uncertainty notes]

# Optional
- Citation style: [links, footnotes, APA, etc.]
- Uncertainty rule: [mark unknowns instead of guessing]
```

## XML

```xml
<prompt profile="research">
  <research_question>[Specific question or decision the research should answer]</research_question>
  <scope>[Date range, geography, audience, exclusions, and depth]</scope>
  <sources>[Official docs, papers, credible sources, links, or allowed source types]</sources>
  <criteria>[How options should be compared: cost, features, risks, tradeoffs, etc.]</criteria>
  <output_format>[Brief, table, memo, recommendation, citations, uncertainty notes]</output_format>
  <uncertainty_rule>[Optional: mark unknowns instead of guessing]</uncertainty_rule>
</prompt>
```

## TOML

```toml
profile = "research"
research_question = "[Specific question or decision the research should answer]"
scope = "[Date range, geography, audience, exclusions, and depth]"
sources = "[Official docs, papers, credible sources, links, or allowed source types]"
criteria = "[How options should be compared: cost, features, risks, tradeoffs, etc.]"
output_format = "[Brief, table, memo, recommendation, citations, uncertainty notes]"
uncertainty_rule = "[Optional: mark unknowns instead of guessing]"
```
