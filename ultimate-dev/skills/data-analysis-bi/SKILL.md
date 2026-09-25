---
name: data-analysis-bi
description: >
  Perform reproducible data analysis and BI work with clear metric definitions,
  data lineage, uncertainty checks, visualizations, and decision-oriented
  storytelling. Use for datasets, dashboards, experiments, KPIs, SQL analysis,
  forecasting support, and executive reporting.
triggers: [data analysis, BI, dashboard, KPI, metric, dataset, SQL analysis, experiment, visualization, forecast]
provides: data_analysis
---

# Data Analysis and BI

Make the result reproducible and decision-ready, not merely visually polished.

## Method

1. State the decision, population, time period, unit, and metric definitions.
2. Inspect data source, schema, quality, sampling, joins, and lineage.
3. Validate completeness, duplicates, missingness, ranges, and leakage.
4. Select methods appropriate to the question; document assumptions and limits.
5. Build reproducible transformations and independent checks.
6. Analyze trends, segments, comparisons, uncertainty, and sensitivity.
7. Create a clear visualization or narrative with an actionable takeaway.
8. Record provenance, code/notebook, limitations, refresh date, and owner.

## Output

```yaml
question: <..>
metric_definitions: [..]
data_sources: [..]
quality_checks: [..]
method: <..>
results: [..]
uncertainty: [..]
limitations: [..]
recommendation: <..>
```

Never fabricate missing values, silently change denominators, or call a
correlation causal. Treat financial, employment, health, and other regulated
data as sensitive and minimize exposure.
