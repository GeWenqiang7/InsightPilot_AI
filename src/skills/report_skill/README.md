# Report Skill

`report_skill` is the **final synthesis and output layer**.

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
