---
name: ai-ml
description: >
  AI/ML engineering: model training, inference, MLOps, LLM integration, prompt engineering, vector databases, RAG systems, fine-tuning, deployment. Technology-agnostic.
triggers: [AI, ML, machine learning, deep learning, neural network, LLM, prompt, embedding, vector, RAG, fine-tuning, model training, inference, MLOps]
anti_triggers: [traditional backend, frontend UI, database schema, DevOps pipeline]
last_verified: 2026-09-21
---

# AI/ML Engineering Module (pattern-based)

## Core Principles (technology-agnostic)

1. **Data quality first** — garbage in, garbage out
2. **Reproducibility** — version data, code, and models
3. **Evaluation metrics** — measure before deploying
4. **Cost awareness** — track inference costs and latency
5. **Ethical AI** — bias detection, fairness, transparency

## Key Patterns

### LLM Integration Patterns
- Prompt engineering and templates
- Token management and costs
- Context window optimization
- Streaming responses
- Function calling and tools

### Vector Database Patterns
- Embedding generation
- Similarity search
- Index optimization
- Hybrid search (keyword + semantic)

### RAG Patterns
- Document chunking strategies
- Retrieval optimization
- Context assembly
- Citation and source tracking

### Model Deployment Patterns
- Model serving (any framework)
- Batch vs real-time inference
- A/B testing models
- Model versioning and rollback

### MLOps Patterns
- Experiment tracking
- Pipeline orchestration
- Model registry
- Monitoring and drift detection

## Anti-Patterns
- Bad: "Just use the biggest model for everything" — violates cost awareness
- Good: "Match model size to task complexity" — satisfies cost awareness

- Bad: "No evaluation before deployment" — violates evaluation metrics
- Good: "Benchmark against test set first" — satisfies evaluation metrics

## Output Contract
- Model architectures
- Training configurations
- Evaluation reports
- Deployment strategies
- Monitoring dashboards