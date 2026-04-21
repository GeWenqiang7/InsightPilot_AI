import os
from typing import Any, Dict, Optional

from src.skills.evaluate_skill.scripts.run_evaluate_skill import run_evaluate_skill
from src.skills.evaluate_skill.tools import save_evaluate_skill_artifacts



def payload_from_state(state: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "model_result": state.get("model_result") or state.get("model_skill_result"),
        "eda_result": state.get("eda_result") or state.get("eda_skill_result", {}),
        "constraints": state.get("constraints", {}),
    }



def apply_result_to_state(
    state: Dict[str, Any],
    result: Dict[str, Any],
    artifact_paths: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    state["evaluate_skill_result"] = result
    state["evaluation_result"] = result
    state["evaluate_for_llm"] = result.get("evaluate_for_llm", {})
    state["evaluation_status"] = result.get("status")

    if artifact_paths:
        state["evaluate_artifacts"] = artifact_paths
        state["evaluate_path"] = os.path.dirname(artifact_paths["result_path"])

    return state



def run_evaluate_skill_from_state(state: Dict[str, Any], save_artifacts: bool = True) -> Dict[str, Any]:
    payload = payload_from_state(state)
    result = run_evaluate_skill(payload)

    artifact_paths = None
    if save_artifacts:
        base_dir = state.get("output_dir", "output")
        artifact_dir = os.path.join(base_dir, "evaluate_skill")
        artifact_paths = save_evaluate_skill_artifacts(result, artifact_dir)

    return apply_result_to_state(state, result, artifact_paths)
