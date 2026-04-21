---
name: model_skill
description: Semi-autonomous model planning skill that consumes FE + EDA artifacts and returns ranked model strategy and evaluation priorities.
---

# Model Skill

Use this skill after feature planning to transform upstream artifacts into a practical modeling strategy.

## Inputs

Required:

- `fe_plan`
- `eda_result`

Optional:

- `problem_type`
- `target`
- `model_candidates`
- `constraints`

## Outputs

- `risk_flags`
- `model_candidates_ranked`
- `training_strategy`
- `evaluation_focus`
- `recommendations`
- `model_for_llm`

## Capability Boundaries

This skill **does**:

- prioritize model families under current data risks
- define evaluation metrics/checks based on task and risk profile
- generate model-ready context for downstream LLM/agent components

This skill **does not**:

- train final production models
- replace dedicated evaluation/reporting skills
