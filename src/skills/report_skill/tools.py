import json
import os
from typing import Any, Callable, Dict, List


ToolFn = Callable[..., Any]


def validate_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(payload, dict):
        raise TypeError("Report skill payload must be a dictionary.")
    if "intent" not in payload:
        payload = dict(payload)
        payload["intent"] = "Generate a reporting plan."
    return payload


def build_report_plan(payload: Dict[str, Any]) -> Dict[str, Any]:
    payload = validate_payload(payload)
    return {
        "status": "scaffold",
        "intent": payload.get("intent"),
        "sections": [
            "problem summary",
            "data understanding",
            "feature engineering summary",
            "modeling and evaluation summary",
            "recommended next actions",
        ],
        "artifact_targets": ["markdown_report", "notebook_summary", "presentation_outline"],
    }


def save_report_skill_artifacts(result: Dict[str, Any], output_dir: str) -> Dict[str, str]:
    os.makedirs(output_dir, exist_ok=True)
    result_path = os.path.join(output_dir, "report_skill_result.json")
    with open(result_path, "w", encoding="utf-8") as result_file:
        json.dump(result, result_file, indent=2, ensure_ascii=True)
    return {"result_path": result_path}


TOOL_REGISTRY: Dict[str, ToolFn] = {
    "validate_payload": validate_payload,
    "build_report_plan": build_report_plan,
    "save_report_skill_artifacts": save_report_skill_artifacts,
}


def list_tools() -> List[str]:
    return sorted(TOOL_REGISTRY.keys())


def invoke_tool(tool_name: str, *args: Any, **kwargs: Any) -> Any:
    if tool_name not in TOOL_REGISTRY:
        raise KeyError("Unknown report_skill tool: {0}".format(tool_name))
    return TOOL_REGISTRY[tool_name](*args, **kwargs)
