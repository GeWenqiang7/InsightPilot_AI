import os
from typing import Any, Dict

from src.skills.report_skill.scripts.run_report_skill import run_report_skill
from src.skills.report_skill.tools import save_report_skill_artifacts


def payload_from_state(state: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "intent": state.get("intent", "Generate a reporting plan."),
        "eda_result": state.get("eda_result"),
        "fe_plan": state.get("fe_plan"),
        "model_plan": state.get("model_plan"),
        "evaluation_result": state.get("evaluation_result"),
    }


def run_report_skill_from_state(state: Dict[str, Any], save_artifacts: bool = True) -> Dict[str, Any]:
    payload = payload_from_state(state)
    result = run_report_skill(payload)
    state["report_skill_result"] = result
    state["report_plan"] = result

    if save_artifacts:
        base_dir = state.get("output_dir", "output")
        artifact_dir = os.path.join(base_dir, "report_skill")
        state["report_artifacts"] = save_report_skill_artifacts(result, artifact_dir)

    return state
