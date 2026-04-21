# EDA Skill Execution Policy

This document defines how `eda_skill` should make execution decisions after it has been invoked by an agent.

## Goal

The skill is semi-autonomous:

- the caller decides whether to invoke the skill
- the skill decides how to execute the analysis once invoked

The objective is to produce useful, structured, and evidence-based EDA outputs without over-analyzing irrelevant parts of the dataset or over-claiming from weak signals.

## Core Policy

The skill should:

- begin with the cheapest high-value checks
- adapt depth to the task and available context
- prefer evidence over completeness theater
- skip irrelevant modules explicitly
- return conservative conclusions when confidence is limited

## Execution Phases

The skill should think in phases, even if the implementation is not literally separated this way.

### Phase 1: Validate And Classify The Task

Determine:

- whether usable tabular data is available
- whether a target exists
- whether the task is supervised, unsupervised, or general profiling
- whether constraints require sampling or lighter analysis

If the dataset or intent is insufficient, stop early with a structured failure note.

### Phase 2: Structural Profiling

Run low-cost, broadly useful checks:

- row and column counts
- basic schema and dtypes
- uniqueness and nullability signals
- duplicate row count when feasible

This phase should almost always run first.

### Phase 3: Data Quality Analysis

Run checks that reveal common EDA risks:

- missingness
- invalid or suspicious values if supported
- distribution anomalies
- outlier-heavy columns

This phase should prioritize columns most likely to affect downstream analysis.

### Phase 4: Task-Aware Analysis

If a target is available, decide whether to run:

- target distribution checks
- class imbalance checks
- target leakage heuristics
- feature-target associations

If the task is unsupervised, focus on structure and feature relationships instead.

### Phase 5: Relationship Analysis

Run dependency-oriented analysis only where it is meaningful:

- feature-feature correlation or association
- feature-target relationships
- redundancy hints
- clusterable group hints

Do not force correlation outputs when the data types make them misleading.

### Phase 6: Synthesis

Transform raw findings into:

- ranked insights
- high-level recommendations
- LLM-compressed context
- KG candidates
- RAG queries when needed

This phase is where the skill becomes useful to other agents.

## Prioritization Rules

Prioritize findings that are:

- likely to affect model quality
- likely to create incorrect conclusions
- likely to require human or downstream-agent intervention
- broadly relevant across many columns or major features

Lower priority findings include:

- mild skew with weak downstream impact
- weak correlations with no decision relevance
- cosmetic inconsistencies that do not affect analysis goals

## Module Selection Rules

The skill should dynamically choose modules.

### Always Preferred

- meta profiling
- schema profiling
- missingness analysis

### Usually Preferred

- distribution analysis
- outlier analysis for numeric-heavy datasets

### Conditional

- target analysis only when target exists
- correlation only when relationships are meaningful
- RAG only when interpretation help is needed
- KG emission only when retained structure is useful downstream

## Depth Control

Use the caller's depth setting if provided.

### `light`

- run only structural profiling and high-signal quality checks
- produce concise insights
- avoid expensive or weak-value analysis

### `standard`

- run the normal workflow
- include task-aware checks when relevant
- emit compressed context and key recommendations

### `deep`

- run fuller analysis where data permits
- include broader relationship exploration
- produce richer KG candidates and more nuanced caveats

If no depth is specified, default to `standard`.

## Sampling Policy

If the dataset is too large for full analysis:

- use a documented sampling strategy
- preserve reproducibility when possible
- clearly record that approximate analysis was used

Recommended rules:

- profile full schema when possible
- sample rows for distribution and outlier-heavy work
- avoid pretending sample-level statistics are full-dataset guarantees

## Confidence Policy

The skill should annotate confidence whenever it matters.

High confidence:

- strong, direct, measurable findings
- clear high missingness
- obvious class imbalance
- strong numeric skew or outlier ratios

Medium confidence:

- moderate associations
- pattern-based but not definitive recommendations

Low confidence:

- weak correlations
- sparse support
- semantically unclear features
- sampled approximations with possible instability

## Escalation To RAG

Escalate to retrieval when:

- the evidence is real but interpretation is domain-sensitive
- a recommendation could vary materially by domain or task
- the skill needs best-practice guidance rather than more statistics

Do not escalate to RAG merely because it is available.

## Emission To KG

Emit graph candidates when:

- the relationship is useful enough to retain
- the relationship can be tied to observable evidence
- downstream systems can benefit from graph structure

Filter out:

- weak noisy links
- ambiguous semantic claims
- unsupported causal interpretations

## Failure Handling

If a module fails:

- continue with unaffected modules when safe
- record the module failure
- downgrade status to `partial` when needed

If the failure blocks the whole skill:

- return `failed`
- include the blocking reason and any partial context that was still safely derived

## Output Discipline

The skill should produce outputs that are:

- structured
- explicit about what was observed
- explicit about what was inferred
- explicit about what was skipped
- easy for both humans and agents to consume

## Recommended Summary Pattern

When producing a final synthesis, prefer this order:

1. Major dataset facts
2. Highest-priority risks
3. Target-aware or task-aware observations
4. Recommended follow-up actions
5. Optional RAG and KG hooks
6. Confidence notes and skipped work
