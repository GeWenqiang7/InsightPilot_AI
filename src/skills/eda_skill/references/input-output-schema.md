# EDA Skill Input And Output Schema

This document defines the logical contract for `eda_skill`. Different frameworks may wrap these fields differently, but the semantic meaning should stay stable.

## Input Schema

The skill expects an invocation payload with the following structure.

### Required Fields

```json
{
  "data": "<dataframe-or-tabular-handle>",
  "intent": "Analyze this dataset before downstream decision making."
}
```

### Recommended Fields

```json
{
  "target": "target_column_or_expression",
  "problem_type": "classification | regression | clustering | profiling",
  "analysis_depth": "light | standard | deep",
  "constraints": {
    "time_budget": "optional",
    "cost_budget": "optional",
    "privacy_level": "optional"
  }
}
```

### Optional Context Fields

```json
{
  "dataset_name": "customer_churn",
  "domain": "subscription analytics",
  "column_hints": {
    "tenure_months": "customer tenure",
    "mrr": "monthly recurring revenue"
  },
  "existing_profile": {},
  "prior_findings": [],
  "rag_handle": "<retriever-or-knowledge-interface>",
  "kg_handle": "<graph-adapter-or-candidate-sink>",
  "sampling_policy": {
    "enabled": true,
    "max_rows": 50000
  }
}
```

## Input Field Semantics

- `data`: the main tabular object or a resolvable handle to it
- `intent`: the caller's reason for invoking the skill
- `target`: optional supervised target column or expression
- `problem_type`: informs task-aware analysis behavior
- `analysis_depth`: controls breadth and cost
- `constraints`: lets the skill trade off quality and speed
- `column_hints`: optional semantic hints that improve interpretation
- `existing_profile`: reusable metadata from earlier profiling
- `prior_findings`: upstream observations from other agents
- `rag_handle`: retrieval interface used only when needed
- `kg_handle`: sink for graph candidate output
- `sampling_policy`: approximation rules for large datasets

## Output Schema

The skill should return a structured object with stable top-level sections.

### Core Output Shape

```json
{
  "status": "success | partial | failed",
  "meta": {},
  "schema": {},
  "missing": {},
  "distribution": {},
  "outliers": {},
  "target": {},
  "correlation": {},
  "insights": [],
  "recommendations": [],
  "eda_for_llm": {},
  "kg_candidates": {},
  "rag_queries": [],
  "confidence_notes": [],
  "skipped_modules": []
}
```

## Output Field Details

### `status`

- `success`: all relevant analyses completed
- `partial`: some analyses completed and some were skipped or downgraded
- `failed`: required prerequisites were missing or execution could not proceed safely

### `meta`

High-level dataset facts.

Suggested fields:

```json
{
  "rows": 10000,
  "cols": 42,
  "numeric_cols": 18,
  "categorical_cols": 20,
  "datetime_cols": 2,
  "duplicate_rows": 13
}
```

### `schema`

Per-column structure summary.

Suggested per-column fields:

```json
{
  "age": {
    "dtype": "int64",
    "semantic_type": "numeric",
    "n_unique": 61,
    "nullable": false
  }
}
```

### `missing`

Missingness metrics and severity.

Suggested per-column fields:

```json
{
  "income": {
    "missing_rate": 0.31,
    "missing_flag": "high",
    "recommendation_hint": "drop_or_impute"
  }
}
```

### `distribution`

Distribution summaries for numeric and categorical columns.

Suggested numeric fields:

```json
{
  "amount": {
    "mean": 105.2,
    "std": 40.8,
    "skew": 1.73,
    "kurtosis": 4.91
  }
}
```

Suggested categorical fields:

```json
{
  "plan_type": {
    "top_values": {
      "basic": 0.52,
      "pro": 0.31,
      "enterprise": 0.17
    },
    "cardinality": 3
  }
}
```

### `outliers`

Outlier signals and severity estimates.

Suggested fields:

```json
{
  "transaction_amount": {
    "method": "iqr",
    "outlier_ratio": 0.07,
    "severity": "medium"
  }
}
```

### `target`

Task-aware target summary when relevant.

Classification example:

```json
{
  "target_name": "churn_flag",
  "target_type": "binary",
  "class_distribution": {
    "0": 0.88,
    "1": 0.12
  },
  "imbalance_flag": "high"
}
```

Regression example:

```json
{
  "target_name": "sale_price",
  "target_type": "continuous",
  "mean": 220000.0,
  "std": 35000.0,
  "skew": 1.21
}
```

### `correlation`

Feature-feature and feature-target relationships.

Suggested shape:

```json
{
  "feature_target_correlation": {
    "tenure_months": -0.43,
    "support_tickets": 0.37
  },
  "top_feature_pairs": [
    {
      "feature_a": "mrr",
      "feature_b": "plan_value",
      "score": 0.82,
      "type": "pearson"
    }
  ]
}
```

### `insights`

Ranked EDA findings for humans and agents.

Suggested item shape:

```json
{
  "type": "missing",
  "priority": "high",
  "column": "income",
  "finding": "income has a high missing rate",
  "why_it_matters": "may bias model training and reduce feature utility",
  "action": "drop_or_impute"
}
```

### `recommendations`

Higher-level advice synthesized from raw findings.

Suggested item shape:

```json
{
  "category": "data_quality",
  "priority": "high",
  "recommendation": "review imputation strategy for income and employment length",
  "evidence_refs": ["missing.income", "missing.employment_length"]
}
```

### `eda_for_llm`

Compressed context for downstream LLM use. This should be token-aware and preserve only salient facts.

Suggested shape:

```json
{
  "meta": {},
  "features": {},
  "insights": [],
  "warnings": []
}
```

### `kg_candidates`

Graph-ready candidates derived from EDA.

Suggested shape:

```json
{
  "nodes": [],
  "relations": [
    {
      "source": "tenure_months",
      "target": "TARGET",
      "type": "correlated_with",
      "strength": 0.43
    }
  ],
  "important_features": ["tenure_months", "support_tickets"]
}
```

### `rag_queries`

Retrieval intents generated only when external knowledge would improve interpretation.

Suggested shape:

```json
[
  {
    "reason": "class imbalance guidance needed",
    "query": "severe class imbalance binary classification evaluation metric guidance"
  }
]
```

### `confidence_notes`

Warnings, uncertainty, and scope limitations.

Suggested examples:

- `"target column not provided; skipped target-aware analysis"`
- `"correlation findings are weak and should not drive strong FE decisions alone"`
- `"sample-based analysis was used due to dataset size limits"`

### `skipped_modules`

Explicit record of skipped work.

Suggested shape:

```json
[
  {
    "module": "target",
    "reason": "no target provided"
  }
]
```

## Compatibility Guidance

Adapters may:

- rename fields
- wrap the output in framework-specific envelopes
- attach file paths or artifact URIs
- add timing and telemetry metadata

Adapters should not:

- change the semantic meaning of core fields
- hide skipped work or failure reasons
- merge raw observed facts with retrieved advice without labeling them
