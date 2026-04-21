import os
from typing import Any, Dict, Optional

from src.skills.model_skill.scripts.run_model_skill import run_model_skill
from src.skills.model_skill.tools import save_model_skill_artifacts



def payload_from_state(state: Dict[str, Any]) -> Dict[str, Any]:
    fe_plan = state.get("fe_plan")
    if fe_plan is None and isinstance(state.get("fe_result"), dict):
        fe_plan = state["fe_result"].get("fe_plan")

    return {
        "fe_plan": fe_plan,
        "eda_result": state.get("eda_result") or state.get("eda_skill_result"),
        "problem_type": state.get("problem_type"),
        "target": state.get("target"),
        "model_candidates": state.get("model_candidates", []),
        "constraints": state.get("constraints", {}),
    }



def apply_result_to_state(
    state: Dict[str, Any],
    result: Dict[str, Any],
    artifact_paths: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    state["model_skill_result"] = result
    state["model_result"] = result
    state["model_for_llm"] = result.get("model_for_llm", {})
    state["model_status"] = result.get("status")

    if artifact_paths:
        state["model_artifacts"] = artifact_paths
        state["model_path"] = os.path.dirname(artifact_paths["result_path"])

    return state



def run_model_skill_from_state(state: Dict[str, Any], save_artifacts: bool = True) -> Dict[str, Any]:
    payload = payload_from_state(state)
    result = run_model_skill(payload)

    artifact_paths = None
    if save_artifacts:
        base_dir = state.get("output_dir", "output")
        artifact_dir = os.path.join(base_dir, "model_skill")
        artifact_paths = save_model_skill_artifacts(result, artifact_dir)

    return apply_result_to_state(state, result, artifact_paths)
