# Model Skill Input And Output Schema

`model_skill` expects a payload containing modeling intent plus upstream FE and EDA context.

Recommended inputs:

- `intent`
- `problem_type`
- `fe_plan`
- `eda_result`
- `kg_candidates`

Expected outputs:

- `status`
- `intent`
- `problem_type`
- `candidate_model_families`
- `evaluation_focus`
