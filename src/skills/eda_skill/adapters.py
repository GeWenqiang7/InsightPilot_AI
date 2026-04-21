import os
from typing import Any, Dict, Optional

from src.skills.eda_skill.scripts.run_eda_skill import run_eda_skill
from src.skills.eda_skill.tools import save_eda_skill_artifacts


def payload_from_state(state: Dict[str, Any]) -> Dict[str, Any]:
    if "df" not in state:
        raise ValueError("State must include `df` for eda_skill execution.")

    return {
        "data": state["df"],
        "intent": state.get("intent", "Analyze this dataset before downstream agent decisions."),
        "target": state.get("target"),
        "problem_type": state.get("problem_type"),
        "analysis_depth": state.get("analysis_depth", "standard"),
        "dataset_name": state.get("dataset_name"),
        "domain": state.get("domain"),
        "column_hints": state.get("column_hints", {}),
        "prior_findings": state.get("prior_findings", []),
        "sampling_policy": state.get("sampling_policy"),
        "constraints": state.get("constraints", {}),
    }


def apply_result_to_state(
    state: Dict[str, Any],
    result: Dict[str, Any],
    artifact_paths: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    state["eda_skill_result"] = result
    state["eda_result"] = result
    state["eda_for_llm"] = result.get("eda_for_llm", {})
    state["kg_candidates"] = result.get("kg_candidates", {})
    state["rag_queries"] = result.get("rag_queries", [])
    state["eda_status"] = result.get("status")

    if artifact_paths:
        state["eda_artifacts"] = artifact_paths
        state["eda_path"] = os.path.dirname(artifact_paths["result_path"])

    return state


def run_eda_skill_from_state(state: Dict[str, Any], save_artifacts: bool = True) -> Dict[str, Any]:
    payload = payload_from_state(state)
    result = run_eda_skill(payload)

    artifact_paths = None
    if save_artifacts:
        base_dir = state.get("output_dir", "output")
        artifact_dir = os.path.join(base_dir, "eda_skill")
        artifact_paths = save_eda_skill_artifacts(result, artifact_dir)

    return apply_result_to_state(state, result, artifact_paths)
