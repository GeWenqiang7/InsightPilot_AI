"""Model tool registry adapter.

Exposes a function-calling interface for model planning and delegates execution to
`src.skills.model_skill`.
"""

from typing import Any, Dict, Tuple

from src.skills.model_skill.adapters import run_model_skill_from_state



def get_tool_definition() -> Dict[str, Any]:
    return {
        "type": "function",
        "function": {
            "name": "run_model",
            "description": "Generate model strategy and evaluation focus from FE plan + EDA result.",
            "parameters": {
                "type": "object",
                "properties": {
                    "problem_type": {
                        "type": ["string", "null"],
                        "enum": ["classification", "regression", "clustering", None],
                    },
                    "target": {"type": ["string", "null"]},
                    "model_candidates": {
                        "type": "array",
                        "items": {"type": "object"},
                    },
                    "output_dir": {"type": "string"},
                },
                "required": [],
                "additionalProperties": False,
            },
        },
    }



def run(state: Dict[str, Any]) -> Dict[str, Any]:
    print("\n[MODEL TOOL] Delegating to model_skill...")
    return run_model_skill_from_state(state, save_artifacts=True)



def invoke(params: Dict[str, Any], state: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    params = params or {}
    local_state = dict(state)

    for key in ("problem_type", "target", "model_candidates", "output_dir"):
        if key in params:
            local_state[key] = params.get(key)

    local_state = run(local_state)

    tool_result = {
        "model_path": local_state.get("model_path"),
        "problem_type": local_state.get("model_result", {}).get("problem_type"),
        "candidate_count": len(local_state.get("model_result", {}).get("model_candidates_ranked", [])),
        "risk_count": len(local_state.get("model_result", {}).get("risk_flags", [])),
        "primary_metrics": local_state.get("model_result", {}).get("evaluation_focus", {}).get("metrics", []),
    }
    return tool_result, local_state
