"""Advisor tool registry adapter."""

from typing import Any, Dict, Tuple

from src.skills.advisor_skill.adapters import run_advisor_skill_from_state



def get_tool_definition() -> Dict[str, Any]:
    return {
        "type": "function",
        "function": {
            "name": "run_advisor",
            "description": "Generate strategy plans and constraint optimization suggestions.",
            "parameters": {
                "type": "object",
                "properties": {
                    "constraints": {"type": "object"},
                    "output_dir": {"type": "string"},
                },
                "required": [],
                "additionalProperties": False,
            },
        },
    }



def run(state: Dict[str, Any]) -> Dict[str, Any]:
    print("\n[ADVISOR TOOL] Delegating to advisor_skill...")
    return run_advisor_skill_from_state(state, save_artifacts=True)



def invoke(params: Dict[str, Any], state: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    params = params or {}
    local_state = dict(state)

    if "constraints" in params:
        local_state["constraints"] = params.get("constraints")
    if "output_dir" in params:
        local_state["output_dir"] = params.get("output_dir")

    local_state = run(local_state)

    tool_result = {
        "advisor_path": local_state.get("advisor_path"),
        "strategy_count": len(local_state.get("advisor_result", {}).get("strategy_plan", [])),
        "scenario_count": len(local_state.get("advisor_result", {}).get("scenario_options", [])),
        "constraint_count": len(local_state.get("advisor_result", {}).get("constraint_optimization", [])),
    }
    return tool_result, local_state
