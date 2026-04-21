# Skills Package

This package contains reusable skills that can be invoked by the current project and by future agent systems.

## Planned Skills

- `eda_skill`: exploratory data analysis for tabular datasets
- `fe_skill`: feature engineering planning and execution
- `model_skill`: model selection, training, and evaluation orchestration

Each skill should follow the same pattern:

- `SKILL.md` for behavior and invocation rules
- `README.md` for implementation-facing usage notes
- `tool_manifest.json` for tool/function-calling integration
- `tools.py` for the unified callable tool surface
- `scripts/` for runtime entrypoints
- `references/` and `examples/` for supporting documents
