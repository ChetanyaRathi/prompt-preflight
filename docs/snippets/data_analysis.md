# Data analysis contract

## MD

```md
# Task
[Analyze, clean, calculate, visualize, or summarize specific data]

# Data Source
[File/table/query/source and relevant columns]

# Question
[Metric, segment, hypothesis, comparison, or trend to answer]

# Metrics
[Definitions for revenue, churn, conversion, retention, p95, etc.]

# Output Format
[Chart, table, summary, JSON, notebook, dashboard, or code]

# Validation
[Row counts, totals, expected ranges, reconciliation, or sanity checks]

# Optional
- Segments/filters: [time range, region, cohort, product]
- Assumptions: [how to handle missing or ambiguous data]
```

## XML

```xml
<prompt profile="data_analysis">
  <task>[Analyze, clean, calculate, visualize, or summarize specific data]</task>
  <data_source>[File/table/query/source and relevant columns]</data_source>
  <question>[Metric, segment, hypothesis, comparison, or trend to answer]</question>
  <metrics>[Definitions for revenue, churn, conversion, retention, p95, etc.]</metrics>
  <output_format>[Chart, table, summary, JSON, notebook, dashboard, or code]</output_format>
  <validation>[Row counts, totals, expected ranges, reconciliation, or sanity checks]</validation>
</prompt>
```

## TOML

```toml
profile = "data_analysis"
task = "[Analyze, clean, calculate, visualize, or summarize specific data]"
data_source = "[File/table/query/source and relevant columns]"
question = "[Metric, segment, hypothesis, comparison, or trend to answer]"
metrics = "[Definitions for revenue, churn, conversion, retention, p95, etc.]"
output_format = "[Chart, table, summary, JSON, notebook, dashboard, or code]"
validation = "[Row counts, totals, expected ranges, reconciliation, or sanity checks]"
```
