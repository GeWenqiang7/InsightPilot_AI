from typing import Any, Dict

from src.skills.fe_skill.tools import build_feature_plan, validate_payload


def run_fe_skill(payload: Dict[str, Any]) -> Dict[str, Any]:
    payload = validate_payload(payload)
    result = build_feature_plan(payload)
    result["skill"] = "fe_skill"
    return result
