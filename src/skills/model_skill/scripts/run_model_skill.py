from typing import Any, Dict

from src.skills.model_skill.tools import (
    build_evaluation_focus,
    build_model_for_llm,
    build_training_strategy,
    extract_risk_flags,
    infer_problem_type,
    normalize_model_candidates,
    rank_model_candidates,
    validate_payload,
)



def run_model_skill(payload: Dict[str, Any]) -> Dict[str, Any]:
    validate_payload(payload)

    fe_plan = payload["fe_plan"]
    eda_result = payload["eda_result"]
    problem_type = infer_problem_type(payload)

    raw_candidates = payload.get("model_candidates") or fe_plan.get("model_alignment")
    candidates = normalize_model_candidates(problem_type, raw_candidates)
    risk_flags = extract_risk_flags(eda_result, problem_type)
    ranked_candidates = rank_model_candidates(candidates, problem_type, risk_flags)

    result: Dict[str, Any] = {
        "status": "success",
        "problem_type": problem_type,
        "input_summary": {
            "fe_issue_count": len(fe_plan.get("data_issues", [])) if isinstance(fe_plan, dict) else 0,
            "fe_action_count": len(fe_plan.get("feature_engineering", [])) if isinstance(fe_plan, dict) else 0,
            "eda_insight_count": len(eda_result.get("insights", [])) if isinstance(eda_result, dict) else 0,
        },
        "risk_flags": risk_flags,
        "model_candidates_ranked": ranked_candidates,
        "training_strategy": build_training_strategy(problem_type, fe_plan, risk_flags),
        "evaluation_focus": build_evaluation_focus(problem_type, risk_flags),
        "recommendations": [
            {
                "priority": "high" if risk["severity"] == "high" else "medium",
                "action": f"Mitigate {risk['risk']} before final model selection",
                "evidence": risk["evidence"],
            }
            for risk in risk_flags
            if risk["risk"] != "no_major_data_quality_blockers"
        ],
        "confidence_notes": [],
        "model_for_llm": {},
    }

    if not result["recommendations"]:
        result["recommendations"].append(
            {
                "priority": "medium",
                "action": "Proceed with baseline model benchmark and monitor drift post-deployment",
                "evidence": [],
            }
        )

    result["model_for_llm"] = build_model_for_llm(result)
    return result
