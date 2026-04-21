import json
import os
from typing import Any, Callable, Dict, List


ToolFn = Callable[..., Any]


def validate_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(payload, dict):
        raise TypeError("FE skill payload must be a dictionary.")
    normalized = dict(payload)
    if "intent" not in normalized:
        normalized["intent"] = "Generate a feature engineering plan."
    normalized.setdefault("problem_type", None)
    normalized.setdefault("eda_result", {})
    normalized.setdefault("eda_for_llm", {})
    normalized.setdefault("model_candidates", [])
    normalized.setdefault("kg_candidates", {})
    return normalized


def _collect_data_issues(eda_result: Dict[str, Any]) -> List[Dict[str, Any]]:
    issues: List[Dict[str, Any]] = []

    for col, value in eda_result.get("missing", {}).items():
        rate = value.get("missing_rate", 0)
        if rate >= 0.3:
            issues.append(
                {
                    "issue": "high_missing",
                    "columns": [col],
                    "severity": "high",
                    "suggestion": "create a missingness flag and impute or drop after review",
                }
            )

    for col, value in eda_result.get("distribution", {}).items():
        skew = abs(value.get("skew", 0))
        if skew > 1:
            issues.append(
                {
                    "issue": "high_skew",
                    "columns": [col],
                    "severity": "medium",
                    "suggestion": "consider log, yeo-johnson, or robust scaling transformations",
                }
            )

    for col, value in eda_result.get("outliers", {}).items():
        ratio = value.get("outlier_ratio", 0)
        if ratio > 0.05:
            issues.append(
                {
                    "issue": "outlier_heavy",
                    "columns": [col],
                    "severity": "medium",
                    "suggestion": "consider capping, robust scaling, or model families tolerant to outliers",
                }
            )

    return issues


def _build_transform_steps(
    payload: Dict[str, Any],
    issues: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    eda_result = payload.get("eda_result", {})
    schema = eda_result.get("schema", {})
    model_candidates = payload.get("model_candidates", [])
    model_categories = {
        str(candidate.get("category", "")).lower()
        for candidate in model_candidates
        if isinstance(candidate, dict)
    }

    steps: List[Dict[str, Any]] = []

    for issue in issues:
        column = issue["columns"][0]
        if issue["issue"] == "high_missing":
            steps.append(
                {
                    "column": column,
                    "method": "missing_flag_plus_imputation",
                    "reason": "missing rate is high and should be tracked explicitly",
                    "priority": "high",
                }
            )
        elif issue["issue"] == "high_skew":
            steps.append(
                {
                    "column": column,
                    "method": "log_transform_or_power_transform",
                    "reason": "distribution is highly skewed",
                    "priority": "high",
                }
            )
        elif issue["issue"] == "outlier_heavy":
            steps.append(
                {
                    "column": column,
                    "method": "robust_scaling_or_capping",
                    "reason": "outlier ratio is high",
                    "priority": "medium",
                }
            )

    for column, info in schema.items():
        semantic_type = info.get("semantic_type")
        unique_count = info.get("n_unique", 0)
        if semantic_type == "categorical":
            if unique_count <= 10:
                method = "one_hot_encoding"
            else:
                method = "frequency_or_target_encoding_review"
            steps.append(
                {
                    "column": column,
                    "method": method,
                    "reason": "categorical feature requires encoding before most downstream models",
                    "priority": "medium",
                }
            )

    if "linear" in model_categories or "neural" in model_categories:
        steps.append(
            {
                "column": "__all_numeric__",
                "method": "scaling",
                "reason": "linear or neural models benefit from normalized numeric ranges",
                "priority": "medium",
            }
        )

    return steps


def _build_feature_selection(eda_result: Dict[str, Any]) -> Dict[str, Any]:
    drop_candidates = []
    keep_candidates = []

    for col, value in eda_result.get("missing", {}).items():
        if value.get("missing_rate", 0) >= 0.6:
            drop_candidates.append(col)

    for pair in eda_result.get("correlation", {}).get("high_correlation_pairs", []):
        feature_2 = pair.get("feature_2")
        if feature_2 and feature_2 not in drop_candidates:
            drop_candidates.append(feature_2)

    important_features = eda_result.get("kg_candidates", {}).get("important_features", [])
    keep_candidates.extend([feature for feature in important_features if feature not in keep_candidates])

    return {
        "drop": drop_candidates,
        "keep": keep_candidates,
        "method": "rule_based_screening_from_missingness_and_correlation",
    }


def _build_model_alignment(problem_type: str, model_candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    alignment = []

    for candidate in model_candidates:
        if not isinstance(candidate, dict):
            continue

        name = candidate.get("name", "unknown_model")
        category = str(candidate.get("category", "")).lower()

        if category == "linear":
            strategy = "prioritize scaling, low-collinearity features, and interpretable encodings"
        elif category == "tree":
            strategy = "prioritize strong signals, allow limited outliers, and avoid unnecessary scaling"
        elif category == "neural":
            strategy = "normalize numeric inputs and keep encoding strategy consistent"
        else:
            strategy = "align feature set with the selected model family requirements"

        if problem_type == "classification":
            strategy += "; keep class imbalance handling in mind during FE"

        alignment.append({"model": name, "strategy": strategy})

    return alignment


def build_feature_plan(payload: Dict[str, Any]) -> Dict[str, Any]:
    payload = validate_payload(payload)
    eda_result = payload.get("eda_result", {})
    issues = _collect_data_issues(eda_result)
    feature_steps = _build_transform_steps(payload, issues)
    feature_selection = _build_feature_selection(eda_result)
    model_alignment = _build_model_alignment(payload.get("problem_type"), payload.get("model_candidates", []))

    return {
        "status": "success",
        "intent": payload.get("intent"),
        "problem_type": payload.get("problem_type"),
        "data_issues": issues,
        "feature_engineering": feature_steps,
        "feature_selection": feature_selection,
        "model_alignment": model_alignment,
        "recommended_steps": [
            "review the highest-priority transformations first",
            "finalize encoding and scaling choices per downstream model family",
            "move approved transformations into an executable FE pipeline",
        ],
        "notes": [
            "This FE plan is generated from current EDA signals and should be refined with domain context before execution."
        ],
    }


def save_fe_skill_artifacts(result: Dict[str, Any], output_dir: str) -> Dict[str, str]:
    os.makedirs(output_dir, exist_ok=True)
    result_path = os.path.join(output_dir, "fe_skill_result.json")
    with open(result_path, "w", encoding="utf-8") as result_file:
        json.dump(result, result_file, indent=2, ensure_ascii=True)
    return {"result_path": result_path}


TOOL_REGISTRY: Dict[str, ToolFn] = {
    "validate_payload": validate_payload,
    "build_feature_plan": build_feature_plan,
    "save_fe_skill_artifacts": save_fe_skill_artifacts,
}


def list_tools() -> List[str]:
    return sorted(TOOL_REGISTRY.keys())


def invoke_tool(tool_name: str, *args: Any, **kwargs: Any) -> Any:
    if tool_name not in TOOL_REGISTRY:
        raise KeyError("Unknown fe_skill tool: {0}".format(tool_name))
    return TOOL_REGISTRY[tool_name](*args, **kwargs)
