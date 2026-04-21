import os
from typing import Any, Dict

from src.skills.model_skill.scripts.run_model_skill import run_model_skill
from src.skills.model_skill.tools import save_model_skill_artifacts


def payload_from_state(state: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "intent": state.get("intent", "Generate a modeling plan."),
        "problem_type": state.get("problem_type"),
        "fe_plan": state.get("fe_plan"),
        "eda_result": state.get("eda_result"),
        "kg_candidates": state.get("kg_candidates"),
    }


def run_model_skill_from_state(state: Dict[str, Any], save_artifacts: bool = True) -> Dict[str, Any]:
    payload = payload_from_state(state)
    result = run_model_skill(payload)
    state["model_skill_result"] = result
    state["model_plan"] = result

    if save_artifacts:
        base_dir = state.get("output_dir", "output")
        artifact_dir = os.path.join(base_dir, "model_skill")
        state["model_artifacts"] = save_model_skill_artifacts(result, artifact_dir)

    return state
