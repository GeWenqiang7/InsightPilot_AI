from typing import Any, Dict

from src.skills.eda_skill.tools import (
    analyze_correlation,
    analyze_distribution,
    analyze_missing,
    analyze_outliers,
    build_meta,
    build_rag_queries,
    build_recommendations,
    build_schema,
    build_target_summary,
    compress_for_llm,
    extract_kg_candidates,
    generate_feature_insights,
    validate_payload,
)


def run_eda_skill(payload: Dict[str, Any]) -> Dict[str, Any]:
    df = validate_payload(payload)
    problem_type = payload.get("problem_type")
    target = payload.get("target")

    result: Dict[str, Any] = {
        "status": "success",
        "meta": build_meta(df),
        "schema": build_schema(df),
        "missing": analyze_missing(df),
        "distribution": analyze_distribution(df),
        "outliers": analyze_outliers(df),
        "target": None,
        "correlation": {},
        "insights": [],
        "recommendations": [],
        "eda_for_llm": {},
        "kg_candidates": {},
        "rag_queries": [],
        "confidence_notes": [],
        "skipped_modules": [],
    }

    target_series = None
    if problem_type == "clustering":
        result["skipped_modules"].append({"module": "target", "reason": "clustering tasks do not require a target"})
    elif target is None:
        result["skipped_modules"].append({"module": "target", "reason": "no target provided"})
        result["confidence_notes"].append("target column not provided; skipped target-aware analysis")
    else:
        target_series, result["target"] = build_target_summary(df, target, problem_type)

    try:
        result["correlation"] = analyze_correlation(df, target_series)
    except Exception as exc:
        result["correlation"] = {"error": str(exc)}
        result["confidence_notes"].append("correlation analysis failed and was downgraded")
        result["status"] = "partial"

    result["insights"] = generate_feature_insights(
        result["missing"],
        result["distribution"],
        result["outliers"],
    )
    result["recommendations"] = build_recommendations(result["insights"])
    result["kg_candidates"] = extract_kg_candidates(result)
    result["rag_queries"] = build_rag_queries(problem_type, result["target"], result["missing"])
    result["eda_for_llm"] = compress_for_llm(result)

    if result["skipped_modules"] and result["status"] == "success" and target is None:
        result["status"] = "partial"

    return result
