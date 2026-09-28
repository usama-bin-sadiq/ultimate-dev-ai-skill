---
name: bigquery-ai-ml
metadata:
  version: "1.1.0"
  category: AiAndMachineLearning
description: >-
  Leverages BigQuery's built-in machine learning and GenAI capabilities
  for advanced data analytics. Use when you need to write SQL queries
  that perform time-series forecasting, predict values, detect outliers or anomalies, find key drivers,
  perform semantic search or vector search, classify text, calculate similarity,
  summarize content, translate language, evaluate models, filter by semantic conditions,
  measure the causal effect of an intervention, compute correlations between columns,
  detect change points or structural breaks, extract trend or seasonality components,
  or leverage generative AI capabilities in BigQuery. Do not use for general
  BigQuery dataset, table, or job management requests.
---

# BigQuery AI & ML

BigQuery integrates with Vertex AI to provide powerful machine learning and
generative AI capabilities directly within SQL queries using built-in functions
like `AI.FORECAST`, `AI.KEY_DRIVERS`, `AI.DETECT_ANOMALIES`, and `AI.GENERATE`.

## Reference Directory

-   **Functions Reference**:

    -   **AI.AGG**: [ai_agg.md](references/ai_agg.md) - Multi-row semantic
        aggregation and summarization.
    -   **AI.CAUSAL_EFFECT**:
        [ai_causal_effect.md](references/ai_causal_effect.md) - Quantifies the
        impact of an intervention on a time series.
    -   **AI.CLASSIFY**: [ai_classify.md](references/ai_classify.md) - Classify
        text.
    -   **AI.DETECT_ANOMALIES**:
        [ai_detect_anomalies.md](references/ai_detect_anomalies.md) - Detect
        anomalies.
    -   **AI.EVALUATE**: [ai_evaluate.md](references/ai_evaluate.md) - Evaluate
        models.
    -   **AI.FORECAST**: [ai_forecast.md](references/ai_forecast.md) -
        Time-series forecasting.
    -   **AI.GENERATE**: [ai_generate.md](references/ai_generate.md) - Generate
        text using LLMs.
    -   **AI.GENERATE_EMBEDDING**:
        [ai_generate_embedding.md](references/ai_generate_embedding.md) -
        Generate embeddings.
    -   **AI.GENERATE_TABLE**:
        [ai_generate_table.md](references/ai_generate_table.md) - Table-valued
        AI generation.
    -   **AI.IF**: [ai_if.md](references/ai_if.md) - Evaluate semantic
        conditions.
    -   **AI.KEY_DRIVERS**: [ai_key_drivers.md](references/ai_key_drivers.md) -
        Identifies key drivers, this is a TVF.
    -   **AI.SCORE**: [ai_score.md](references/ai_score.md) - Score data.
    -   **AI.SEARCH**: [ai_search.md](references/ai_search.md) - Semantic
        search.
    -   **AI.SIMILARITY**: [ai_similarity.md](references/ai_similarity.md) -
        Semantic similarity.
    -   **Remote Models**: [remote_models.md](references/remote_models.md) -
        Working with remote models (Vertex AI).
    -   **CONTRIBUTION_ANALYSIS**:
        [ml_contribution_analysis.md](references/ml_contribution_analysis.md)
        -   Finds contributing factors, key drivers of change. Requires creating
            a MODEL entity.
    -   **ML.CORRELATION**: [ml_correlation.md](references/ml_correlation.md) -
        Calculates correlation between columns, optionally sliced by dimensions.
    -   **ML.DETECT_CHANGE_POINTS**:
        [ml_detect_change_points.md](references/ml_detect_change_points.md) -
        Detects structural breaks or sustained shifts in a time series.
    -   **ML.SEASONALITY**: [ml_seasonality.md](references/ml_seasonality.md) -
        Extracts seasonal components from a time series.
    -   **ML.TREND**: [ml_trend.md](references/ml_trend.md) - Extracts the
        long-term trend component from a time series.
    -   **VECTOR_SEARCH**: [vector_search.md](references/vector_search.md) -
        Vector search best practices.

## Related Skills

-   [BigQuery Basics Skill](../bigquery-basics): SKILL.md file for core BigQuery
    concepts, resource management, CLI, and client libraries.

Each file below is loaded on demand, not at triage. 21 file(s):

- `references/ai_agg.md` — BigQuery AI.AGG. AI.AGG uses a Vertex AI Gemini model to aggregate data based on natural
- `references/ai_causal_effect.md` — BigQuery AI.CAUSAL_EFFECT. AI.CAUSALEFFECT quantifies the impact of specific interventions on time
- `references/ai_classify.md` — BigQuery AI.Classify. AI.CLASSIFY categorizes unstructured data into a predefined set of labels.
- `references/ai_detect_anomalies.md` — BigQuery AI.Detect_Anomalies. AI.DETECTANOMALIES uses the pre-trained TimesFM model to identify
- `references/ai_evaluate.md` — AI.EVALUATE. Evaluates the accuracy of a forecasting model by comparing predicted values
- `references/ai_forecast.md` — prose
- `references/ai_generate.md` — prose
- `references/ai_generate_embedding.md` — prose
- `references/ai_generate_table.md` — AI.GENERATE_TABLE. Uses Gemini models to extract information into a predefined SQL schema.
- `references/ai_if.md` — BigQuery AI.If. AI.IF is a semantic boolean function used to evaluate a condition described in
- `references/ai_key_drivers.md` — BigQuery AI.Key_Drivers. AI.KEYDRIVERS automatically identifies the key dimensional segments most
- `references/ai_score.md` — BigQuery AI.Score. The AI.SCORE function is commonly used with the ORDER BY clause and works well
- `references/ai_search.md` — BigQuery AI.Search. AI.SEARCH is a table-valued function for semantic search on tables that have
- `references/ai_similarity.md` — BigQuery AI.Similarity. AI.SIMILARITY computes the semantic similarity between two inputs.
- `references/ml_contribution_analysis.md` — Contribution analysis, also called key driver analysis, is a method used to
- `references/ml_correlation.md` — BigQuery ML.CORRELATION. ML.CORRELATION is a Table-Valued Function (TVF) that calculates the
- `references/ml_detect_change_points.md` — BigQuery ML.Detect_Change_Points. ML.DETECTCHANGEPOINTS is a one-step Table-Valued Function (TVF) that
- `references/ml_seasonality.md` — BigQuery ML.Seasonality. ML.SEASONALITY is a time-series decomposition function that extracts seasonal
- `references/ml_trend.md` — BigQuery ML.Trend. ML.TREND is a time-series decomposition function that extracts the underlying
- `references/remote_models.md` — prose
- `references/vector_search.md` — VECTOR_SEARCH. BigQuery VECTORSEARCH is a table-valued function used to find semantically

