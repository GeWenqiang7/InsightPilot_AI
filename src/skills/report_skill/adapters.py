import os
from typing import Any, Dict, Optional

from src.skills.report_skill.scripts.run_report_skill import run_report_skill
from src.skills.report_skill.tools import save_report_skill_artifacts



def payload_from_state(state: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "eda_result": state.get("eda_result") or state.get("eda_skill_result"),
        "fe_plan": state.get("fe_plan") or state.get("fe_result", {}).get("fe_plan"),
        "model_result": state.get("model_result") or state.get("model_skill_result"),
        "evaluation_result": state.get("evaluation_result") or state.get("evaluate_skill_result"),
        "advisor_result": state.get("advisor_result") or state.get("advisor_skill_result"),
        "user_query": state.get("user_query") or state.get("query"),
        "intent": state.get("intent"),
        "rag_context": state.get("rag_context", []),
        "kg_context": state.get("kg_context", {}),
        "target": state.get("target"),
        "problem_type": state.get("problem_type"),
    }



def apply_result_to_state(
    state: Dict[str, Any],
    result: Dict[str, Any],
    artifact_paths: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    state["report_skill_result"] = result
    state["report_result"] = result
    state["report_for_llm"] = result.get("report_for_llm", {})
    state["report_status"] = result.get("status")

    if artifact_paths:
        state["report_artifacts"] = artifact_paths
        state["report_path"] = os.path.dirname(artifact_paths["result_path"])

    return state



def run_report_skill_from_state(state: Dict[str, Any], save_artifacts: bool = True) -> Dict[str, Any]:
    payload = payload_from_state(state)
    result = run_report_skill(payload)

    artifact_paths = None
    if save_artifacts:
        base_dir = state.get("output_dir", "output")
        artifact_dir = os.path.join(base_dir, "report_skill")
        artifact_paths = save_report_skill_artifacts(result, artifact_dir)

    return apply_result_to_state(state, result, artifact_paths)
