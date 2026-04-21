---
name: eda_skill
description: Semi-autonomous exploratory data analysis skill for tabular data. Use when an agent needs structured EDA results, LLM-ready summaries, and optional RAG/KG support before feature engineering, modeling, or recommendation generation.
---

# EDA Skill

Use this skill when an agent needs a reusable, structured, and semi-autonomous exploratory data analysis workflow for tabular data. The caller decides whether to invoke the skill; once invoked, the skill may choose its own analysis order, select relevant sub-analyses, and decide whether RAG or KG support is needed.

This skill is designed to be portable across projects and agent frameworks. It should not be tightly coupled to any single orchestrator, but it may emit project-specific artifacts through adapters.

## Purpose

This skill helps an agent:

- understand dataset shape, schema, and feature quality
- detect common data issues before downstream modeling
- generate structured findings and prioritized recommendations
- compress EDA findings into LLM-friendly context
- emit KG candidates from statistical or semantic feature relations
- formulate RAG queries when domain knowledge is needed to interpret patterns

## When To Invoke

Invoke this skill when one or more of the following are true:

- a tabular dataset has been loaded and needs first-pass understanding
- an agent must decide what data quality issues matter before FE or modeling
- the task requires missing value, distribution, outlier, target, or correlation analysis
- the system needs structured evidence before generating recommendations
- downstream agents need compact EDA summaries instead of raw dataset access
- KG construction needs feature-feature or feature-target relationship candidates
- RAG may help interpret unusual distributions, imbalance, leakage risk, or domain-specific anomalies

## Do Not Invoke

Do not invoke this skill when:

- the task is not about tabular data understanding
- the user only wants visualization styling or report formatting
- the task is already in feature engineering, training, or evaluation execution
- the dataset is unavailable and no usable metadata or profile is provided
- a domain-specific analysis workflow should replace generic EDA entirely

## Skill Role

This is a semi-autonomous skill.

- The caller decides whether to invoke the skill.
- Once invoked, the skill may decide analysis order and depth.
- The skill may skip irrelevant analyses.
- The skill may request or use RAG context when statistical signals alone are insufficient.
- The skill may emit KG candidates, but it does not own full KG reasoning.
- The skill may recommend actions, but it does not directly execute FE, model training, or business decisions unless the caller explicitly delegates those responsibilities.

## Inputs

Required inputs:

- dataset handle, dataframe, or equivalent tabular input
- execution goal or task intent

Strongly recommended inputs:

- target column, target expression, or task type
- problem type such as classification, regression, clustering, or general profiling
- caller constraints such as budget, speed, privacy, or analysis depth

Optional context:

- dataset name and business domain
- schema hints or semantic column descriptions
- prior agent observations
- existing profile artifacts
- RAG retriever handle or retrievable knowledge interface
- KG adapter or graph candidate sink

## Expected Outputs

The skill should produce structured outputs in a stable contract. A framework-specific adapter may rename fields, but the logical outputs should remain consistent.

Core outputs:

- `meta`: dataset size and high-level profile facts
- `schema`: per-column type and uniqueness summary
- `missing`: missingness metrics and severity tags
- `distribution`: numeric and categorical distribution summaries
- `outliers`: outlier signals and severity estimates
- `target`: target analysis when applicable
- `correlation`: feature-feature and feature-target relations when applicable
- `insights`: prioritized findings and suggested follow-up actions

Derived outputs:

- `eda_for_llm`: compressed EDA context for downstream LLM use
- `recommendations`: prioritized remediation or analysis suggestions
- `kg_candidates`: graph-ready candidate nodes, edges, or relations
- `rag_queries`: search prompts or retrieval intents when external/domain knowledge is needed
- `confidence_notes`: caveats, missing prerequisites, weak-signal warnings, or unsupported conclusions

## Autonomy Rules

After invocation, the skill should decide its own workflow using the following principles:

1. Start from the minimum analysis needed to understand the data safely.
2. Expand into deeper analysis only when the task, data shape, or anomalies justify it.
3. Prefer cheap structural checks before expensive or interpretive analysis.
4. If target information exists, decide whether task-aware analysis should override generic profiling.
5. If a column or module is irrelevant, skip it instead of forcing full coverage.
6. If confidence is low, emit a caveat instead of inventing certainty.
7. If domain interpretation is needed, formulate RAG queries rather than guessing.
8. If relationships are structurally useful downstream, emit KG candidates in parallel with insights.

## Suggested Internal Workflow

The skill may adapt the order, but a typical flow is:

1. Validate inputs and identify task mode.
2. Inspect meta and schema.
3. Run missingness analysis.
4. Run distribution analysis.
5. Run outlier analysis where relevant.
6. Run target-aware analysis if a target is defined.
7. Run correlation or dependency analysis where meaningful.
8. Synthesize findings into ranked insights.
9. Compress context for LLM consumers.
10. Emit KG candidates if useful.
11. Build RAG queries if interpretation requires external knowledge.

## Decision Heuristics

Use lightweight heuristics to decide what to run:

- If there is no target, skip target-dependent metrics.
- If the task is clustering or unsupervised profiling, focus on structure, quality, and feature relations.
- If numeric columns are sparse or absent, reduce numeric distribution and outlier emphasis.
- If categorical cardinality is high, note encoding risk and representation complexity.
- If class imbalance is strong, surface it early and consider RAG support for mitigation guidance.
- If correlation is weak or meaningless for the available types, avoid overstating conclusions.
- If feature semantics are unclear, prefer schema-level findings and retrieval queries over domain claims.

## RAG Policy

Use RAG selectively, not by default.

RAG is appropriate when:

- interpreting whether a detected issue is important in a domain context
- choosing between alternative remediation strategies
- explaining imbalance, leakage, drift, or data quality patterns with external guidance
- turning raw EDA findings into more domain-aware recommendations

When using RAG:

- formulate retrieval around the observed signal, not generic EDA keywords alone
- keep queries concise and evidence-driven
- distinguish retrieved guidance from directly observed facts
- attach retrieved context to recommendations, not to raw statistics

Example RAG query intents:

- "high missing rate in credit risk income field handling strategies"
- "severe class imbalance binary classification recommended evaluation metrics"
- "high-skew transactional amount feature transformation best practices"

## KG Policy

Use KG output as a structured byproduct of EDA, not as a replacement for EDA.

Emit KG candidates when:

- feature-target relationships should be preserved for downstream reasoning
- strong feature-feature associations may guide clustering, redundancy checks, or FE
- column semantics or derived relations can be represented as graph edges

Typical KG candidate patterns:

- `feature -> TARGET` with correlation, importance proxy, or dependency label
- `feature_a -> feature_b` with high-association or redundancy label
- `feature -> issue` such as high-missing, high-skew, or outlier-heavy
- `feature -> recommendation` as a soft advisory edge when your framework supports it

The skill should not:

- claim causal relationships from simple correlation alone
- perform full graph reasoning inside the skill unless explicitly delegated
- mix statistical evidence and semantic assertions without labeling the difference

## Capability Boundaries

This skill can:

- perform structured tabular EDA
- produce prioritized data-quality and modeling-readiness findings
- summarize findings for LLMs and other agents
- emit graph candidates and retrieval intents

This skill cannot assume responsibility for:

- final feature engineering execution
- final model selection or training
- business decision approval
- domain-truth validation without retrieval or external evidence
- causal inference beyond available evidence

## Failure And Fallback Rules

If required inputs are missing:

- stop early and return a structured failure note

If analysis is partially possible:

- run the safe subset
- mark skipped modules explicitly
- record why the skipped modules were unavailable or inapplicable

If statistical evidence is weak:

- downgrade confidence
- avoid prescriptive language
- suggest follow-up profiling, sampling checks, or retrieval support

If the dataset is too large or expensive for full analysis:

- prefer sampled or summary-based analysis
- state the sampling or approximation policy clearly

## Output Style

Outputs should be:

- structured first, narrative second
- evidence-based and compact
- safe for downstream machine consumption
- explicit about confidence and limitations

When generating human-readable insights:

- lead with the issue
- name affected columns
- explain why the issue matters
- recommend next actions at a high level
- avoid overstating certainty

## Integration Notes

For project integration, prefer a thin adapter layer:

- the adapter maps project state into skill inputs
- the adapter invokes underlying analyzers
- the adapter writes outputs back to the framework state

Recommended analyzer families:

- profiling
- missingness
- distribution
- outlier detection
- target parsing and target analysis
- correlation or dependency analysis
- insight synthesis
- LLM compression
- KG candidate extraction

## Example Invocation

Example caller intent:

> Analyze this churn dataset before feature engineering. Target is `churn_flag`. Prioritize issues that may affect model quality. Use retrieval only if you need help interpreting imbalance or missingness patterns. Emit graph candidates for strong feature-target relations.

Expected skill behavior:

- run target-aware EDA
- inspect missingness, distributions, outliers, and correlations
- surface imbalance or leakage risk if found
- emit compact recommendations
- return `eda_for_llm`, `insights`, and `kg_candidates`
- build `rag_queries` only when domain interpretation would improve recommendations

## Operating Principle

This skill exists to convert raw tabular data into structured understanding that other agents can trust, reuse, and build on. It should be conservative in claims, deliberate in scope, and useful as both a standalone EDA capability and a shared system component in multi-agent, RAG-assisted, and KG-aware workflows.
