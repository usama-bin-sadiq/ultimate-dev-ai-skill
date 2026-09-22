---
name: ai-ml-skill
description: >
  Meta-cognitive skill for AI/ML. Teaches HOW to think about intelligent
  systems — data, models, evaluation, and deployment — regardless of
  specific framework or algorithm.
triggers: [ai, ml, model, training, inference, prediction, learning, intelligent, automate]
provides: ai_ml_ability
---

# AI/ML Skill — Build Intelligent Systems

## Purpose

An **ability**. AI/ML is about learning from data to make predictions or decisions.
This skill teaches you how to think about intelligent systems — not just specific
frameworks or algorithms.

## The Ability

```
Given any AI/ML problem, you can:
1. Identify if ML is actually the right solution
2. Define the problem in ML terms (input, output, metric)
3. Design the data pipeline (collection → training → serving)
4. Evaluate honestly (is it actually good enough?)
5. Deploy and monitor (models degrade over time)
```

## How to Build ANY Intelligent System

### Step 1: Is ML the Right Solution?

```
Before using ML, ask:

CAN it be solved with rules?
  → If yes, use rules (simpler, faster, explainable)

CAN it be solved with a lookup table?
  → If yes, use a lookup table

DO you have enough data?
  → No data = no ML (garbage in, garbage out)

DO you have labeled examples?
  → Supervised learning needs labels

IS the problem well-defined?
  → Vague problem = vague model

RULE: ML is a last resort, not a first choice.
```

### Step 2: Define the Problem in ML Terms

```
For ANY ML problem, define:

INPUT:    What does the model see? (features)
OUTPUT:   What does the model predict? (target)
METRIC:   How do we measure success? (accuracy, F1, MAE, etc.)
BASELINE: What's the simplest model that works? (always predict the majority class)
DATA:     Where does training data come from?
LABELS:   How are labels created? (human, algorithm, ground truth)
```

### Step 3: Design the Data Pipeline

```
For ANY ML system:

COLLECT  → Gather raw data
CLEAN    → Handle missing values, outliers, errors
LABEL    → Create ground truth (if supervised)
SPLIT    → Train / validation / test (never leak test data)
FEATURE  → Transform raw data into model inputs
TRAIN    → Fit the model
EVALUATE → Measure on held-out data
DEPLOY   → Serve predictions
MONITOR  → Track data drift and model performance

RULE: The pipeline IS the system. The model is just a component.
```

### Step 4: Evaluate Honestly

```
Evaluation checklist:

□ Does it beat the baseline?
□ Does it work on held-out data? (not just training data)
□ Does it work on edge cases?
□ Is it fair? (no bias across groups)
□ Is it fast enough? (latency requirements)
□ Is it interpretable? (can you explain why?)
□ Does it degrade over time? (data drift)

RULE: If you can't measure it, you can't improve it.
```

### Step 5: Deploy and Monitor

```
ML deployment is NOT like software deployment:

1. Models degrade over time (data drift)
2. Predictions need monitoring (not just errors)
3. Retraining is ongoing (not one-time)
4. A/B testing is essential (model vs model)
5. Rollback must be instant (bad predictions = bad UX)

Monitor:
  → Prediction distribution (is it shifting?)
  → Feature distribution (is input changing?)
  → Error rate (is it getting worse?)
  → Latency (is it getting slower?)
```

## AI/ML Anti-Patterns

- DO NOT use ML when rules will do
- DO NOT train without a baseline comparison
- DO NOT skip data validation and cleaning
- DO NOT deploy without monitoring for data drift
- DO NOT ignore bias and fairness checks
