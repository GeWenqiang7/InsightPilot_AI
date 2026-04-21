# Report Skill

`report_skill` is the **final synthesis and output layer** and the shared reporting skill package.

It aggregates `eda_result`, `fe_plan`, `model_result`, and `evaluation_result` to generate:

- executive summary
- key findings by stage
- prioritized action plan
- requirement alignment to initial user query/intent
- visualization plan (chart-level specs)
- report-level RAG/KG hooks
- markdown report artifact
- compact `report_for_llm`

If `advisor_result` exists, report will integrate advisor scenarios/constraints into the final output.

## Main Entry Points

- `src/skills/report_skill/scripts/run_report_skill.py`
- `src/skills/report_skill/tools.py`
- `src/skills/report_skill/adapters.py`

## Current Scope

This package currently provides:

- direct runtime entrypoint
- project-state adapter
- report composition and markdown artifact generation
- visualization planning and requirement alignment
- RAG/KG integration hooks
- tool manifest for function-calling integration