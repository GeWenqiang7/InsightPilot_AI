---
name: report_skill
description: Semi-autonomous reporting skill for turning analysis outputs into structured summaries, reports, and delivery artifacts.
---

# Report Skill

Use this skill when an agent needs a reusable reporting workflow after analysis and modeling.

This skill is designed to:

- consume EDA, FE, modeling, and evaluation outputs
- structure report sections and artifact plans
- expose a unified tool surface for future report generation
- remain portable across projects and agent frameworks

## Inputs

Required:

- `eda_result`
- `fe_plan`
- `model_result`
- `evaluation_result`

Optional:

- `advisor_result`
- `user_query`
- `intent`
- `rag_context`
- `kg_context`

## Outputs

- `executive_summary`
- `key_findings`
- `action_plan`
- `requirement_alignment`
- `visualization_plan`
- `advisor_integration`
- `rag_kg_hooks`
- `delivery_decision`
- `report_markdown`
- `report_for_llm`