# Model Skill

`model_skill` is the shared modeling skill package.

It consumes upstream `fe_plan` and `eda_result`, then produces a structured
modeling strategy package for downstream agents.

## What it outputs

- ranked model candidates
- risk flags derived from EDA signals
- training strategy steps
- evaluation focus (metrics + checks)
- compact `model_for_llm` context

## Main Entry Points

- `src/skills/model_skill/scripts/run_model_skill.py`
- `src/skills/model_skill/tools.py`
- `src/skills/model_skill/adapters.py`

## Expected payload

```json
{
  "fe_plan": {"problem_type": "classification"},
  "eda_result": {},
  "problem_type": "classification",
  "target": "label",
  "model_candidates": []
}