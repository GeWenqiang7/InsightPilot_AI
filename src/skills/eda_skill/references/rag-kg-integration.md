# EDA Skill RAG And KG Integration Guide

This document explains how `eda_skill` should cooperate with retrieval systems and knowledge graph pipelines without becoming tightly coupled to a single implementation.

## Design Goal

`eda_skill` should remain useful as a standalone EDA skill, but it should also expose structured hooks for:

- domain-aware recommendation generation through RAG
- graph construction and downstream reasoning through KG candidates

The skill should treat RAG and KG as optional integrations, not mandatory dependencies.

## RAG Integration

### Why RAG Exists Here

EDA observes patterns. RAG helps interpret whether those patterns matter, what remedies are common, and how recommendations should be framed in a domain-aware way.

Use RAG to support interpretation, not to replace measurement.

## When To Trigger RAG

RAG should be considered when:

- a detected pattern needs domain-specific interpretation
- the skill must choose among several plausible remediation strategies
- the dataset shows imbalance, skew, leakage risk, or missingness that benefit from known best practices
- the caller explicitly requests external guidance or supporting references

RAG is not necessary when:

- the finding is purely descriptive and obvious
- the recommendation is already low-risk and generic
- there is not enough evidence to form a precise retrieval query

## RAG Trigger Examples

Good triggers:

- a finance dataset has 35% missingness in income-related columns
- a medical dataset has extreme class imbalance and the caller wants evaluation guidance
- a retail dataset shows strong long-tail transaction amounts and the agent needs transformation options

Weak triggers:

- simple row and column counts
- straightforward dtype summaries
- low-signal weak correlations with no downstream decision impact

## How To Build RAG Queries

RAG queries should be:

- tied to observed evidence
- concise
- domain-aware when domain context exists
- framed around action or interpretation, not just keywords

Recommended template:

```text
<observed_issue> + <data context> + <decision need>
```

Examples:

- `high missing rate in borrower income feature imputation strategy for credit risk modeling`
- `binary churn model severe class imbalance evaluation metric and resampling guidance`
- `high-skew purchase amount feature transformation options for tree and linear models`

## RAG Output Contract

When the skill emits retrieval intents, use a structure like:

```json
[
  {
    "reason": "need guidance on handling severe class imbalance",
    "query": "binary churn model severe class imbalance evaluation metric and resampling guidance",
    "based_on": ["target.class_distribution"]
  }
]
```

If retrieved context is later attached to EDA-derived recommendations, it should remain clearly labeled as external guidance rather than observed fact.

## RAG Safety Rules

- Never present retrieved guidance as if it were measured directly from the dataset.
- Never use RAG to fabricate statistical values.
- Prefer retrieval after basic EDA signals exist, not before.
- If retrieval is unavailable, degrade gracefully and keep the recommendation conservative.

## KG Integration

### Why KG Exists Here

EDA naturally discovers relationships that are useful in graph form:

- feature-target links
- feature-feature associations
- feature-issue links
- feature-recommendation hints

The skill should emit these as candidates so downstream components can decide how to store, validate, or reason over them.

## When To Emit KG Candidates

Emit KG candidates when:

- a relationship is structurally useful to retain
- a downstream graph pipeline exists
- findings may benefit later FE, reasoning, explainability, or ranking

Do not emit noisy graph content for every weak pattern. Prefer fewer, clearer candidates over graph spam.

## Candidate Types

Recommended candidate families:

### Feature To Target

```json
{
  "source": "tenure_months",
  "target": "TARGET",
  "type": "correlated_with",
  "strength": 0.43,
  "evidence": "feature_target_correlation"
}
```

### Feature To Feature

```json
{
  "source": "mrr",
  "target": "plan_value",
  "type": "high_association",
  "strength": 0.82,
  "evidence": "top_feature_pairs"
}
```

### Feature To Issue

```json
{
  "source": "income",
  "target": "high_missingness",
  "type": "has_issue",
  "strength": 0.31,
  "evidence": "missing_rate"
}
```

### Feature To Recommendation

```json
{
  "source": "transaction_amount",
  "target": "log_transform",
  "type": "recommended_action",
  "strength": 0.78,
  "evidence": "skew"
}
```

## KG Output Contract

Suggested output shape:

```json
{
  "nodes": [],
  "relations": [],
  "important_features": [],
  "graph_notes": []
}
```

Suggested node categories:

- `feature`
- `target`
- `issue`
- `recommendation`
- `cluster`

Suggested relation labels:

- `correlated_with`
- `high_association`
- `redundant_with`
- `has_issue`
- `recommended_action`
- `belongs_to_cluster`

## KG Safety Rules

- Do not label correlation as causation.
- Do not emit semantic claims unless the evidence is explicit.
- Keep numeric `strength` values interpretable and traceable.
- Include an evidence source whenever possible.
- Allow downstream graph builders to filter, threshold, or reject candidates.

## Joint RAG And KG Pattern

In some cases, EDA should emit both graph candidates and retrieval intents.

Example:

- observation: `income` has high missingness and strong target association
- KG output: `income -> high_missingness`, `income -> TARGET`
- RAG output: guidance query for handling high-missing but predictive features

This separation is useful:

- KG preserves structure
- RAG improves interpretation and recommendation quality

## Integration Through Adapters

To keep the skill portable, use adapters:

- the RAG adapter accepts `rag_queries` and returns retrieved context
- the KG adapter accepts `kg_candidates` and writes them to the project graph layer

The skill itself should only define:

- when to emit retrieval intents
- when to emit graph candidates
- what evidence each output is based on

It should not assume:

- a specific vector store
- a specific graph database
- a specific agent framework

## Recommended Minimal Integration Flow

1. Run core EDA.
2. Generate ranked insights.
3. Emit KG candidates from strong relationships and issues.
4. Emit RAG queries only for findings that need interpretation help.
5. Let downstream adapters execute retrieval or graph persistence.
6. Merge any external guidance back into recommendation layers with clear attribution.
