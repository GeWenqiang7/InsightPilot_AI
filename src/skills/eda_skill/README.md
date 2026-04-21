# EDA Skill

`eda_skill` is a semi-autonomous exploratory data analysis skill for tabular datasets.

It is designed to work in two modes:

- as a reusable skill for external agent systems
- as an internal adapter for the current InsightPilot multi-agent workflow

## What It Provides

- a standard `SKILL.md` contract
- a unified tool surface in `tools.py`
- a direct runtime entrypoint in `scripts/run_eda_skill.py`
- project-state adapters in `adapters.py`
- manifest metadata for external tool/function-calling integration

## Main Entry Points

- `src/skills/eda_skill/scripts/run_eda_skill.py`
- `src/skills/eda_skill/tools.py`
- `src/skills/eda_skill/adapters.py`

## Direct Usage

```python
import pandas as pd

from src.skills.eda_skill import run_eda_skill

df = pd.read_csv("data.csv")

result = run_eda_skill(
    {
        "data": df,
        "intent": "Analyze before modeling.",
        "target": "label",
        "problem_type": "classification",
    }
)
```

## Project Integration

```python
from src.skills.eda_skill import run_eda_skill_from_state

state = {
    "df": df,
    "target": "label",
    "problem_type": "classification",
    "output_dir": "output",
}

state = run_eda_skill_from_state(state)
```

## External Integration Notes

Use `tool_manifest.json` when another agent framework needs a stable list of callable tools and their purpose.

The recommended external flow is:

1. Load data through `load_tabular_data` or pass a DataFrame directly.
2. Call `run_eda_skill`.
3. Consume `eda_for_llm`, `kg_candidates`, and `rag_queries`.
4. Optionally persist artifacts with `save_eda_skill_artifacts`.

## Current Scope

This package already supports:

- direct EDA execution
- project-state execution
- tool registry listing and invocation
- artifact persistence

It does not yet provide:

- remote execution wrappers
- framework-specific return schemas for every tool
