from typing import Any, Dict

from src.skills.model_skill.tools import build_model_plan, validate_payload


def run_model_skill(payload: Dict[str, Any]) -> Dict[str, Any]:
    payload = validate_payload(payload)
    result = build_model_plan(payload)
    result["skill"] = "model_skill"
    return result
