---
name: advisor_skill
description: Strategy-generation and constraint-optimization skill for post-evaluation decision support.
---

# Advisor Skill

## Inputs

Required:
- `model_result`
- `evaluation_result`

Optional:
- `constraints`
- `user_query`
- `intent`
- `rag_context`
- `kg_context`

## Outputs

- `strategy_plan`
- `constraint_optimization`
- `scenario_options` (3-5)
- `rag_kg_hooks`
- `advisor_for_llm`
