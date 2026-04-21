# Model Skill

`model_skill` consumes upstream `fe_plan` and `eda_result`, then produces a structured
modeling strategy package for downstream agents.

## What it outputs

- ranked model candidates
- risk flags derived from EDA signals
- training strategy steps
- evaluation focus (metrics + checks)
- compact `model_for_llm` context

## Expected payload

```json
{
  "fe_plan": {"problem_type": "classification"},
  "eda_result": {},
  "problem_type": "classification",
  "target": "label",
  "model_candidates": []
}
```

## Runtime entrypoints

- `src.skills.model_skill.scripts.run_model_skill.run_model_skill(payload)`
- `src.skills.model_skill.adapters.run_model_skill_from_state(state)`
