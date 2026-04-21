# FE Skill Input And Output Schema

`fe_skill` expects a payload containing feature engineering intent plus upstream EDA context.

Recommended inputs:

- `intent`
- `problem_type`
- `eda_result`
- `eda_for_llm`
- `kg_candidates`

Expected outputs:

- `status`
- `intent`
- `problem_type`
- `recommended_steps`
- `notes`
