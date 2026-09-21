---
name: data-engineering
description: >
  Data pipelines, ETL/ELT, data warehouses, data lakes, streaming data, batch processing, data quality, data governance, analytics engineering. Technology-agnostic.
triggers: [data pipeline, ETL, ELT, data warehouse, data lake, streaming, batch processing, data quality, analytics, data transformation]
anti_triggers: [frontend UI, API design, database schema design, ML model training]
last_verified: 2026-09-21
---

# Data Engineering Module (pattern-based)

## Core Principles (technology-agnostic)

1. **Data quality** — validate, clean, monitor
2. **Idempotency** — rerunnable pipelines
3. **Observability** — lineage, profiling, alerting
4. **Scalability** — handle growing data volumes
5. **Cost optimization** — right-size compute and storage

## Key Patterns

### Pipeline Architecture
- Batch vs streaming
- Orchestration (any workflow engine)
- Error handling and retry logic
- Backfill strategies

### Data Storage Patterns
- Data warehouses (columnar storage)
- Data lakes (object storage)
- Lakehouse architecture (unified)
- Data marts (domain-specific)

### Transformation Patterns
- SQL transformations (any engine)
- Large-scale processing (distributed)
- Data quality frameworks
- Schema validation

### Streaming Patterns
- Event-driven architectures
- Real-time dashboards
- Change data capture (CDC)
- Stream processing

### Governance Patterns
- Data cataloging
- Lineage tracking
- Access control
- Compliance (GDPR, CCPA)

## Anti-Patterns
- Bad: "Process everything in one giant query" — violates scalability
- Good: "Break into modular, testable transformations" — satisfies scalability

- Bad: "Skip data validation" — violates data quality
- Good: "Validate at pipeline entry and exit" — satisfies data quality

## Output Contract
- Pipeline architectures
- Data models
- Transformation logic
- Quality reports
- Governance documentation