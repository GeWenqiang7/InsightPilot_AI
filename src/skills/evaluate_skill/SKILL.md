---
name: evaluate_skill
description: Evaluate and risk-review skill that consumes model outputs and emits gate decisions with improvement actions.
---

# Evaluate Skill

## Inputs

Required:

- `model_result`

Optional:

- `eda_result`
- `constraints`

## Outputs

- `risk_flags`
- `metric_review`
- `improvement_actions`
- `gate_decision`
- `evaluate_for_llm`
