import os
from typing import Any, Dict

from src.skills.fe_skill.scripts.run_fe_skill import run_fe_skill
from src.skills.fe_skill.tools import save_fe_skill_artifacts


def payload_from_state(state: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "intent": state.get("intent", "Generate a feature engineering plan."),
        "problem_type": state.get("problem_type"),
        "eda_result": state.get("eda_result"),
        "eda_for_llm": state.get("eda_for_llm"),
        "kg_candidates": state.get("kg_candidates"),
        "model_candidates": state.get("model_candidates", []),
    }


def run_fe_skill_from_state(state: Dict[str, Any], save_artifacts: bool = True) -> Dict[str, Any]:
    payload = payload_from_state(state)
    result = run_fe_skill(payload)
    state["fe_skill_result"] = result
    state["fe_plan"] = result

    if save_artifacts:
        base_dir = state.get("output_dir", "output")
        artifact_dir = os.path.join(base_dir, "fe_skill")
        state["fe_artifacts"] = save_fe_skill_artifacts(result, artifact_dir)

    return state
