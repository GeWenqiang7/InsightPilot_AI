"""EDA tool registry adapter.

This module exposes the OpenAI function-calling schema expected by
`src.tools.registry`, then delegates actual EDA execution to the reusable
`src.skills.eda_skill` package.
"""

from typing import Any, Dict, Tuple

from src.skills.eda_skill.adapters import run_eda_skill_from_state



def get_tool_definition() -> Dict[str, Any]:
    """Return the function-calling definition for the EDA tool."""
    return {
        "type": "function",
        "function": {
            "name": "run_eda",
            "description": "Run EDA skill and return summary + KG candidate counts.",
            "parameters": {
                "type": "object",
                "properties": {
                    "target": {"type": ["string", "null"]},
                    "problem_type": {
                        "type": ["string", "null"],
                        "enum": ["classification", "regression", "clustering", None],
                    },
                    "output_dir": {"type": "string"},
                },
                "required": [],
                "additionalProperties": False,
            },
        },
    }



def run(state: Dict[str, Any]) -> Dict[str, Any]:
    """Compatibility entrypoint for direct agent calls."""
    print("\n[EDA TOOL] Delegating to eda_skill...")
    return run_eda_skill_from_state(state, save_artifacts=True)



def invoke(params: Dict[str, Any], state: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Function-calling execution hook used by `src.tools.registry`."""
    params = params or {}
    local_state = dict(state)

    if "target" in params:
        local_state["target"] = params.get("target")
    if "problem_type" in params:
        local_state["problem_type"] = params.get("problem_type")
    if "output_dir" in params:
        local_state["output_dir"] = params.get("output_dir")

    local_state = run(local_state)

    tool_result = {
        "eda_path": local_state.get("eda_path"),
        "meta": local_state.get("eda_result", {}).get("meta", {}),
        "insights_count": len(local_state.get("eda_result", {}).get("insights", [])),
        "kg_relations_count": len(local_state.get("kg_candidates", {}).get("relations", [])),
        "important_features_count": len(local_state.get("kg_candidates", {}).get("important_features", [])),
    }

    return tool_result, local_state
