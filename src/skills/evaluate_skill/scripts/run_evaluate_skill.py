from typing import Any, Dict

from src.skills.evaluate_skill.tools import (
    build_eval_for_llm,
    build_improvement_actions,
    build_metric_review,
    extract_eval_risks,
    validate_payload,
)



def run_evaluate_skill(payload: Dict[str, Any]) -> Dict[str, Any]:
    validate_payload(payload)

    model_result = payload["model_result"]
    eda_result = payload.get("eda_result", {})

    risk_flags = extract_eval_risks(model_result, eda_result)

    result: Dict[str, Any] = {
        "status": "success",
        "risk_flags": risk_flags,
        "metric_review": build_metric_review(model_result),
        "improvement_actions": build_improvement_actions(risk_flags),
        "gate_decision": "needs_review" if any(r["severity"] == "high" for r in risk_flags) else "proceed",
        "confidence_notes": [],
        "evaluate_for_llm": {},
    }

    if result["gate_decision"] == "needs_review":
        result["confidence_notes"].append("high-severity risks detected; require reviewer gate before report generation")

    result["evaluate_for_llm"] = build_eval_for_llm(result)
    return result
