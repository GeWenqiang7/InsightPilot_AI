"""Evaluate tool registry adapter."""

from typing import Any, Dict, Tuple

from src.skills.evaluate_skill.adapters import run_evaluate_skill_from_state



def get_tool_definition() -> Dict[str, Any]:
    return {
        "type": "function",
        "function": {
            "name": "run_evaluate",
            "description": "Review model outputs, summarize risks, and output improvement actions.",
            "parameters": {
                "type": "object",
                "properties": {
                    "output_dir": {"type": "string"},
                },
                "required": [],
                "additionalProperties": False,
            },
        },
    }



def run(state: Dict[str, Any]) -> Dict[str, Any]:
    print("\n[EVALUATE TOOL] Delegating to evaluate_skill...")
    return run_evaluate_skill_from_state(state, save_artifacts=True)



def invoke(params: Dict[str, Any], state: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    params = params or {}
    local_state = dict(state)

    if "output_dir" in params:
        local_state["output_dir"] = params.get("output_dir")

    local_state = run(local_state)

    tool_result = {
        "evaluate_path": local_state.get("evaluate_path"),
        "gate_decision": local_state.get("evaluation_result", {}).get("gate_decision"),
        "risk_count": len(local_state.get("evaluation_result", {}).get("risk_flags", [])),
        "action_count": len(local_state.get("evaluation_result", {}).get("improvement_actions", [])),
    }
    return tool_result, local_state
