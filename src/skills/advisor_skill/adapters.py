import os
from typing import Any, Dict, Optional

from src.skills.advisor_skill.scripts.run_advisor_skill import run_advisor_skill
from src.skills.advisor_skill.tools import save_advisor_skill_artifacts



def payload_from_state(state: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "model_result": state.get("model_result") or state.get("model_skill_result"),
        "evaluation_result": state.get("evaluation_result") or state.get("evaluate_skill_result"),
        "constraints": state.get("constraints", {}),
        "user_query": state.get("user_query") or state.get("query"),
        "intent": state.get("intent"),
        "rag_context": state.get("rag_context", []),
        "kg_context": state.get("kg_context", {}),
    }



def apply_result_to_state(
    state: Dict[str, Any],
    result: Dict[str, Any],
    artifact_paths: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    state["advisor_skill_result"] = result
    state["advisor_result"] = result
    state["advisor_for_llm"] = result.get("advisor_for_llm", {})
    state["advisor_status"] = result.get("status")

    if artifact_paths:
        state["advisor_artifacts"] = artifact_paths
        state["advisor_path"] = os.path.dirname(artifact_paths["result_path"])

    return state



def run_advisor_skill_from_state(state: Dict[str, Any], save_artifacts: bool = True) -> Dict[str, Any]:
    payload = payload_from_state(state)
    result = run_advisor_skill(payload)

    artifact_paths = None
    if save_artifacts:
        base_dir = state.get("output_dir", "output")
        artifact_dir = os.path.join(base_dir, "advisor_skill")
        artifact_paths = save_advisor_skill_artifacts(result, artifact_dir)

    return apply_result_to_state(state, result, artifact_paths)
