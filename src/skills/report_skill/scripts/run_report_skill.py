from typing import Any, Dict

from src.skills.report_skill.tools import build_report_plan, validate_payload


def run_report_skill(payload: Dict[str, Any]) -> Dict[str, Any]:
    payload = validate_payload(payload)
    result = build_report_plan(payload)
    result["skill"] = "report_skill"
    return result
