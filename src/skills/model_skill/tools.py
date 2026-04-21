import json
import os
from typing import Any, Dict, List, Optional


VALID_PROBLEM_TYPES = {"classification", "regression", "clustering"}


class ModelSkillValidationError(ValueError):
    pass



def validate_payload(payload: Dict[str, Any]) -> None:
    if not isinstance(payload, dict):
        raise ModelSkillValidationError("payload must be a dict")

    fe_plan = payload.get("fe_plan")
    if not isinstance(fe_plan, dict):
        raise ModelSkillValidationError("`fe_plan` is required and must be a dict")

    eda_result = payload.get("eda_result")
    if not isinstance(eda_result, dict):
        raise ModelSkillValidationError("`eda_result` is required and must be a dict")



def infer_problem_type(payload: Dict[str, Any]) -> str:
    for candidate in (
        payload.get("problem_type"),
        payload.get("fe_plan", {}).get("problem_type"),
        payload.get("eda_result", {}).get("target", {}).get("target_type"),
    ):
        if not candidate:
            continue
        value = str(candidate).lower()
        if value in VALID_PROBLEM_TYPES:
            return value

    return "classification"



def normalize_model_candidates(problem_type: str, model_candidates: Optional[List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
    if model_candidates:
        normalized = []
        for candidate in model_candidates:
            if not isinstance(candidate, dict):
                continue
            name = str(candidate.get("name") or candidate.get("model") or "").strip()
            if not name:
                continue
            normalized.append(
                {
                    "name": name,
                    "family": candidate.get("family", "generic"),
                    "reason": candidate.get("reason", "provided_by_upstream"),
                }
            )
        if normalized:
            return normalized

    defaults = {
        "classification": [
            {"name": "logistic_regression", "family": "linear"},
            {"name": "random_forest_classifier", "family": "tree"},
            {"name": "xgboost_classifier", "family": "boosting"},
        ],
        "regression": [
            {"name": "ridge_regression", "family": "linear"},
            {"name": "random_forest_regressor", "family": "tree"},
            {"name": "xgboost_regressor", "family": "boosting"},
        ],
        "clustering": [
            {"name": "kmeans", "family": "prototype"},
            {"name": "hdbscan", "family": "density"},
            {"name": "gaussian_mixture", "family": "probabilistic"},
        ],
    }
    return defaults[problem_type]



def extract_risk_flags(eda_result: Dict[str, Any], problem_type: str) -> List[Dict[str, Any]]:
    risks: List[Dict[str, Any]] = []

    missing = eda_result.get("missing", {})
    high_missing_cols = [col for col, info in missing.items() if info.get("missing_rate", 0) >= 0.3]
    if high_missing_cols:
        risks.append(
            {
                "risk": "high_missing",
                "severity": "high",
                "evidence": high_missing_cols[:10],
                "impact": "unstable_model_inputs",
            }
        )

    outliers = eda_result.get("outliers", {})
    heavy_outlier_cols = []
    for col, info in outliers.items():
        rate = info.get("outlier_ratio")
        if rate is not None and rate >= 0.05:
            heavy_outlier_cols.append(col)
    if heavy_outlier_cols:
        risks.append(
            {
                "risk": "outlier_sensitive_features",
                "severity": "medium",
                "evidence": heavy_outlier_cols[:10],
                "impact": "metric_instability",
            }
        )

    target = eda_result.get("target", {})
    if problem_type == "classification" and target.get("imbalance_flag") == "high":
        risks.append(
            {
                "risk": "class_imbalance",
                "severity": "high",
                "evidence": target.get("class_distribution", {}),
                "impact": "biased_recall_precision_tradeoff",
            }
        )

    if not risks:
        risks.append(
            {
                "risk": "no_major_data_quality_blockers",
                "severity": "low",
                "evidence": [],
                "impact": "normal_training_path",
            }
        )

    return risks



def build_training_strategy(problem_type: str, fe_plan: Dict[str, Any], risks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    strategy: List[Dict[str, Any]] = [
        {
            "step": "data_split",
            "action": "stratified_split" if problem_type == "classification" else "random_split",
            "notes": "use fixed random_state for reproducibility",
        },
        {
            "step": "pipeline",
            "action": "compose_preprocessing_and_model",
            "notes": "align with feature_engineering plan and avoid leakage",
        },
        {
            "step": "search",
            "action": "lightweight_hyperparameter_search",
            "notes": "prioritize robust baseline before expensive search",
        },
    ]

    fe_actions = fe_plan.get("feature_engineering", []) if isinstance(fe_plan, dict) else []
    if fe_actions:
        strategy.append(
            {
                "step": "fe_execution_guard",
                "action": "apply_high_priority_fe_first",
                "notes": f"total_fe_actions={len(fe_actions)}",
            }
        )

    if any(r["risk"] == "class_imbalance" for r in risks):
        strategy.append(
            {
                "step": "imbalance_mitigation",
                "action": "use_class_weight_or_resampling",
                "notes": "track recall/precision and threshold sensitivity",
            }
        )

    if any(r["risk"] == "high_missing" for r in risks):
        strategy.append(
            {
                "step": "missing_control",
                "action": "add_imputation_and_missing_indicators",
                "notes": "compare imputation variants on validation",
            }
        )

    return strategy



def build_evaluation_focus(problem_type: str, risks: List[Dict[str, Any]]) -> Dict[str, Any]:
    metrics_map = {
        "classification": ["roc_auc", "f1_macro", "precision", "recall", "balanced_accuracy"],
        "regression": ["rmse", "mae", "r2", "mape"],
        "clustering": ["silhouette", "davies_bouldin", "calinski_harabasz"],
    }

    checks = ["data_leakage_check", "feature_drift_snapshot", "error_slice_analysis"]

    if any(r["risk"] == "class_imbalance" for r in risks):
        checks.append("threshold_tuning_curve")
    if any(r["risk"] == "high_missing" for r in risks):
        checks.append("imputation_sensitivity_test")
    if any(r["risk"] == "outlier_sensitive_features" for r in risks):
        checks.append("robustness_under_outlier_trimming")

    return {"metrics": metrics_map[problem_type], "checks": checks}



def rank_model_candidates(candidates: List[Dict[str, Any]], problem_type: str, risks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    ranked: List[Dict[str, Any]] = []
    has_outlier_risk = any(r["risk"] == "outlier_sensitive_features" for r in risks)

    for idx, candidate in enumerate(candidates):
        score = 100 - idx * 5
        family = str(candidate.get("family", "generic"))
        reason = [candidate.get("reason", "default")]

        if problem_type in {"classification", "regression"}:
            if family == "tree":
                score += 5
                reason.append("handles_mixed_feature_scales")
            if family == "linear":
                reason.append("strong_baseline_interpretability")
            if has_outlier_risk and family == "linear":
                score -= 5
                reason.append("potential_outlier_sensitivity")

        ranked.append(
            {
                "name": candidate["name"],
                "family": family,
                "priority_score": score,
                "selection_reason": reason,
            }
        )

    ranked.sort(key=lambda item: item["priority_score"], reverse=True)
    return ranked



def build_model_for_llm(model_result: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "problem_type": model_result["problem_type"],
        "top_models": [
            {
                "name": candidate["name"],
                "score": candidate["priority_score"],
            }
            for candidate in model_result["model_candidates_ranked"][:3]
        ],
        "primary_metrics": model_result["evaluation_focus"]["metrics"][:3],
        "critical_risks": [risk["risk"] for risk in model_result["risk_flags"] if risk["severity"] in {"high", "medium"}],
    }



def save_model_skill_artifacts(result: Dict[str, Any], output_dir: str) -> Dict[str, str]:
    os.makedirs(output_dir, exist_ok=True)
    result_path = os.path.join(output_dir, "model_skill_result.json")
    llm_path = os.path.join(output_dir, "model_skill_for_llm.json")

    with open(result_path, "w", encoding="utf-8") as result_file:
        json.dump(result, result_file, indent=2, ensure_ascii=True)

    with open(llm_path, "w", encoding="utf-8") as llm_file:
        json.dump(result.get("model_for_llm", {}), llm_file, indent=2, ensure_ascii=True)

    return {"result_path": result_path, "llm_path": llm_path}
