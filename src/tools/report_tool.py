"""Report tool registry adapter."""

from typing import Any, Dict, Tuple

from src.skills.report_skill.adapters import run_report_skill_from_state



def get_tool_definition() -> Dict[str, Any]:
    return {
        "type": "function",
        "function": {
            "name": "run_report",
            "description": "Generate final report package from upstream skill artifacts.",
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
    print("\n[REPORT TOOL] Delegating to report_skill...")
    return run_report_skill_from_state(state, save_artifacts=True)



def invoke(params: Dict[str, Any], state: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    params = params or {}
    local_state = dict(state)

    if "output_dir" in params:
        local_state["output_dir"] = params.get("output_dir")

    local_state = run(local_state)

    tool_result = {
        "report_path": local_state.get("report_path"),
        "delivery_decision": local_state.get("report_result", {}).get("delivery_decision"),
        "finding_count": len(local_state.get("report_result", {}).get("key_findings", [])),
        "action_count": len(local_state.get("report_result", {}).get("action_plan", [])),
    }
    return tool_result, local_state
