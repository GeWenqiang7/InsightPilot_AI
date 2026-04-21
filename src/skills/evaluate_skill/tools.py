import json
import os
from typing import Any, Dict, List


class EvaluateSkillValidationError(ValueError):
    pass



def validate_payload(payload: Dict[str, Any]) -> None:
    if not isinstance(payload, dict):
        raise EvaluateSkillValidationError("payload must be a dict")

    model_result = payload.get("model_result")
    if not isinstance(model_result, dict):
        raise EvaluateSkillValidationError("`model_result` is required and must be a dict")



def extract_eval_risks(model_result: Dict[str, Any], eda_result: Dict[str, Any]) -> List[Dict[str, Any]]:
    risks: List[Dict[str, Any]] = []

    model_risks = model_result.get("risk_flags", [])
    for item in model_risks:
        if not isinstance(item, dict):
            continue
        risks.append(
            {
                "risk": item.get("risk", "unknown_model_risk"),
                "severity": item.get("severity", "medium"),
                "source": "model_skill",
                "evidence": item.get("evidence", []),
            }
        )

    missing = eda_result.get("missing", {}) if isinstance(eda_result, dict) else {}
    high_missing = [col for col, info in missing.items() if info.get("missing_rate", 0) >= 0.4]
    if high_missing:
        risks.append(
            {
                "risk": "severe_missingness",
                "severity": "high",
                "source": "eda_skill",
                "evidence": high_missing,
            }
        )

    if not risks:
        risks.append(
            {
                "risk": "no_critical_risk_detected",
                "severity": "low",
                "source": "evaluate_skill",
                "evidence": [],
            }
        )

    return risks



def build_metric_review(model_result: Dict[str, Any]) -> Dict[str, Any]:
    focus = model_result.get("evaluation_focus", {})
    metrics = focus.get("metrics", []) if isinstance(focus, dict) else []
    checks = focus.get("checks", []) if isinstance(focus, dict) else []

    return {
        "primary_metrics": metrics,
        "diagnostic_checks": checks,
        "review_protocol": [
            "compare baseline vs tuned candidates",
            "check metric stability across folds/splits",
            "confirm business-threshold suitability",
        ],
    }



def build_improvement_actions(risks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    actions: List[Dict[str, Any]] = []

    for risk in risks:
        risk_name = risk.get("risk")
        severity = risk.get("severity", "medium")

        if risk_name in {"class_imbalance", "severe_missingness", "high_missing"}:
            actions.append(
                {
                    "priority": "high",
                    "action": "run mitigation experiment set (resampling/imputation/threshold tuning)",
                    "linked_risk": risk_name,
                }
            )
        elif risk_name == "outlier_sensitive_features":
            actions.append(
                {
                    "priority": "medium",
                    "action": "evaluate robust preprocessing and winsorization variants",
                    "linked_risk": risk_name,
                }
            )
        elif risk_name == "no_critical_risk_detected":
            actions.append(
                {
                    "priority": "medium",
                    "action": "promote current best candidate to controlled validation",
                    "linked_risk": risk_name,
                }
            )
        else:
            actions.append(
                {
                    "priority": "medium" if severity != "high" else "high",
                    "action": "add targeted ablation to validate risk impact",
                    "linked_risk": risk_name,
                }
            )

    return actions



def build_eval_for_llm(result: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "status": result.get("status"),
        "high_risks": [r["risk"] for r in result.get("risk_flags", []) if r.get("severity") == "high"],
        "top_actions": result.get("improvement_actions", [])[:3],
        "metrics": result.get("metric_review", {}).get("primary_metrics", [])[:3],
    }



def save_evaluate_skill_artifacts(result: Dict[str, Any], output_dir: str) -> Dict[str, str]:
    os.makedirs(output_dir, exist_ok=True)
    result_path = os.path.join(output_dir, "evaluate_skill_result.json")
    llm_path = os.path.join(output_dir, "evaluate_skill_for_llm.json")

    with open(result_path, "w", encoding="utf-8") as result_file:
        json.dump(result, result_file, indent=2, ensure_ascii=True)

    with open(llm_path, "w", encoding="utf-8") as llm_file:
        json.dump(result.get("evaluate_for_llm", {}), llm_file, indent=2, ensure_ascii=True)

    return {"result_path": result_path, "llm_path": llm_path}
