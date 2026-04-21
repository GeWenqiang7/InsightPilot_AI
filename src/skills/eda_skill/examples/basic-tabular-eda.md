# Basic Tabular EDA Example

This example shows how an agent might invoke `eda_skill` for a simple supervised tabular dataset and what kind of outputs the skill should return.

## Example Scenario

A planning agent has loaded a customer churn dataset and wants evidence before moving into feature engineering.

The agent knows:

- the data is tabular
- the target column is `churn_flag`
- modeling quality matters more than visual reporting
- retrieval is optional and should only be used if the skill needs help interpreting imbalance or missingness

## Example Invocation Payload

```json
{
  "data": "<customer_churn_dataframe>",
  "intent": "Analyze this dataset before feature engineering and modeling.",
  "target": "churn_flag",
  "problem_type": "classification",
  "analysis_depth": "standard",
  "constraints": {
    "time_budget": "medium"
  },
  "dataset_name": "customer_churn",
  "domain": "subscription analytics"
}
```

## Expected Skill Decisions

The skill should likely:

1. validate that the dataset and target are usable
2. run meta and schema profiling
3. inspect missingness across columns
4. analyze numeric and categorical distributions
5. check for outlier-heavy numeric features
6. inspect target class balance
7. compute feature-target associations where supported
8. synthesize insights and recommendations
9. emit KG candidates for strong feature-target relations
10. generate RAG queries only if recommendations need domain-aware support

## Example Output Sketch

```json
{
  "status": "success",
  "meta": {
    "rows": 12450,
    "cols": 21
  },
  "target": {
    "target_name": "churn_flag",
    "target_type": "binary",
    "class_distribution": {
      "0": 0.86,
      "1": 0.14
    },
    "imbalance_flag": "high"
  },
  "insights": [
    {
      "type": "imbalance",
      "priority": "high",
      "column": "churn_flag",
      "finding": "target is meaningfully imbalanced",
      "why_it_matters": "accuracy alone may be misleading for evaluation",
      "action": "review evaluation metrics and resampling strategy"
    },
    {
      "type": "missing",
      "priority": "high",
      "column": "monthly_income",
      "finding": "monthly_income has a high missing rate",
      "why_it_matters": "this feature may require explicit handling before modeling",
      "action": "drop_or_impute"
    }
  ],
  "recommendations": [
    {
      "category": "evaluation",
      "priority": "high",
      "recommendation": "use F1, recall, and PR-AUC in addition to accuracy"
    },
    {
      "category": "data_quality",
      "priority": "high",
      "recommendation": "design a strategy for monthly_income imputation or exclusion"
    }
  ],
  "kg_candidates": {
    "relations": [
      {
        "source": "tenure_months",
        "target": "TARGET",
        "type": "correlated_with",
        "strength": 0.41
      }
    ],
    "important_features": [
      "tenure_months",
      "support_tickets",
      "monthly_income"
    ]
  },
  "rag_queries": [
    {
      "reason": "need guidance for severe class imbalance handling",
      "query": "binary churn classification severe class imbalance evaluation metric and resampling guidance"
    }
  ]
}
```

## Why This Example Is Useful

This example demonstrates that `eda_skill`:

- does more than raw profiling
- stays within EDA boundaries
- prepares downstream agents with compact evidence
- exposes structured hooks for KG and RAG

## Example Interpretation Rules

In this scenario, the skill should:

- treat imbalance as a high-priority task-aware finding
- avoid making final feature engineering decisions itself
- avoid assuming retrieved guidance is ground truth
- preserve strong feature-target links for graph-based downstream use

## Example Adapter Pattern

In a project-specific adapter, the caller might:

1. pass the dataframe and goal metadata into the skill
2. receive the structured output
3. write `eda_result` and `eda_for_llm` into agent state
4. forward `kg_candidates` to a graph builder
5. forward `rag_queries` to a retriever only if retrieval is enabled

This keeps the skill portable while still making it easy to integrate into a larger agent pipeline.
