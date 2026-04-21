import json
import os
from typing import Any, Callable, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from src.skills.eda_skill.analyzers.correlation import analyze_correlation
from src.skills.eda_skill.analyzers.distribution import analyze_distribution
from src.skills.eda_skill.analyzers.insights import generate_feature_insights
from src.skills.eda_skill.analyzers.missing import analyze_missing
from src.skills.eda_skill.analyzers.outlier import analyze_outliers
from src.skills.eda_skill.analyzers.profiler import get_meta_info, get_schema_info
from src.skills.eda_skill.analyzers.target import analyze_target


ToolFn = Callable[..., Any]


def load_tabular_data(data: Any) -> pd.DataFrame:
    if isinstance(data, pd.DataFrame):
        return data
    if isinstance(data, str):
        if not os.path.exists(data):
            raise FileNotFoundError(f"Data path not found: {data}")
        if data.lower().endswith(".csv"):
            return pd.read_csv(data)
        raise ValueError("Only CSV file paths are supported in the current runtime.")
    if isinstance(data, list):
        return pd.DataFrame(data)
    if isinstance(data, dict):
        return pd.DataFrame(data)
    raise TypeError("Unsupported tabular input. Expected DataFrame, CSV path, list of records, or record dict.")


def validate_payload(payload: Dict[str, Any]) -> pd.DataFrame:
    data = payload.get("data")
    if data is None:
        raise ValueError("`data` is required for eda_skill execution.")
    return load_tabular_data(data)


def get_semantic_type(series: pd.Series) -> str:
    if pd.api.types.is_numeric_dtype(series):
        return "numeric"
    if pd.api.types.is_datetime64_any_dtype(series):
        return "datetime"
    if pd.api.types.is_bool_dtype(series):
        return "boolean"
    return "categorical"


def build_meta(df: pd.DataFrame) -> Dict[str, Any]:
    meta = get_meta_info(df)
    meta.update(
        {
            "numeric_cols": int(len(df.select_dtypes(include=np.number).columns)),
            "categorical_cols": int(len(df.select_dtypes(exclude=np.number).columns)),
            "datetime_cols": int(len(df.select_dtypes(include=["datetime64[ns]", "datetimetz"]).columns)),
            "duplicate_rows": int(df.duplicated().sum()),
        }
    )
    return meta


def build_schema(df: pd.DataFrame) -> Dict[str, Dict[str, Any]]:
    schema = get_schema_info(df)
    for col in schema:
        schema[col]["semantic_type"] = get_semantic_type(df[col])
        schema[col]["nullable"] = bool(df[col].isnull().any())
        schema[col]["n_unique"] = int(df[col].nunique(dropna=True))
    return schema


def build_target_summary(
    df: pd.DataFrame, target: Any, problem_type: Optional[str]
) -> Tuple[Optional[pd.Series], Optional[Dict[str, Any]]]:
    if target is None:
        return None, None

    target_series, target_meta = analyze_target(df, target)
    target_summary: Dict[str, Any] = {"target_meta": target_meta}

    if problem_type == "classification":
        distribution = target_series.value_counts(normalize=True, dropna=False).to_dict()
        max_class_share = max(distribution.values()) if distribution else 0.0
        target_summary.update(
            {
                "target_name": target_series.name or str(target),
                "target_type": "classification",
                "class_distribution": {str(k): float(v) for k, v in distribution.items()},
                "imbalance_flag": "high" if max_class_share >= 0.8 else "low",
            }
        )
    elif problem_type == "regression":
        target_summary.update(
            {
                "target_name": target_series.name or str(target),
                "target_type": "continuous",
                "mean": float(target_series.mean()),
                "std": float(target_series.std()),
                "skew": float(target_series.skew()),
            }
        )
    else:
        target_summary.update(
            {
                "target_name": target_series.name or str(target),
                "target_type": "generic",
            }
        )

    return target_series, target_summary


def compress_for_llm(eda_result: Dict[str, Any], max_features: int = 50) -> Dict[str, Any]:
    compressed = {
        "meta": eda_result.get("meta", {}),
        "features": {},
        "insights": eda_result.get("insights", [])[:10],
        "warnings": eda_result.get("confidence_notes", []),
    }

    schema = eda_result.get("schema", {})
    distribution = eda_result.get("distribution", {})
    missing = eda_result.get("missing", {})

    for index, col in enumerate(schema):
        if index >= max_features:
            break

        feature_info = {"type": schema[col]["dtype"]}
        if col in distribution:
            column_dist = distribution[col]
            for key in ("mean", "std", "skew", "kurtosis"):
                value = column_dist.get(key)
                if value is not None and not pd.isna(value):
                    feature_info[key] = round(float(value), 3)

        if col in missing:
            feature_info["missing"] = round(float(missing[col]["missing_rate"]), 3)

        compressed["features"][col] = feature_info

    return compressed


def extract_kg_candidates(eda_result: Dict[str, Any]) -> Dict[str, Any]:
    kg_candidates = {"nodes": [], "relations": [], "important_features": [], "graph_notes": []}
    correlation = eda_result.get("correlation", {})

    feature_target_correlation = correlation.get("feature_target_correlation", {})
    for feature, value in feature_target_correlation.items():
        if value is None or pd.isna(value):
            continue
        kg_candidates["relations"].append(
            {
                "source": feature,
                "target": "TARGET",
                "type": "correlated_with",
                "strength": float(value),
                "evidence": "feature_target_correlation",
            }
        )

    top_features = correlation.get("top_features", [])
    kg_candidates["important_features"] = [item["feature"] for item in top_features if "feature" in item]
    return kg_candidates


def build_recommendations(insights: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    recommendations = []
    for insight in insights:
        recommendations.append(
            {
                "category": insight.get("type", "eda"),
                "priority": "high" if insight.get("type") == "missing" else "medium",
                "recommendation": f"Review `{insight.get('column')}` for `{insight.get('action')}`.",
                "evidence_refs": [f"{insight.get('type')}.{insight.get('column')}"],
            }
        )
    return recommendations


def build_rag_queries(
    problem_type: Optional[str], target_summary: Optional[Dict[str, Any]], missing: Dict[str, Any]
) -> List[Dict[str, str]]:
    rag_queries: List[Dict[str, str]] = []

    if problem_type == "classification" and target_summary and target_summary.get("imbalance_flag") == "high":
        rag_queries.append(
            {
                "reason": "need guidance for severe class imbalance handling",
                "query": "binary classification severe class imbalance evaluation metric and resampling guidance",
            }
        )

    high_missing_cols = [col for col, value in missing.items() if value.get("missing_rate", 0) >= 0.3]
    if high_missing_cols:
        rag_queries.append(
            {
                "reason": "need guidance for handling highly missing features",
                "query": f"high missing rate feature handling strategies for {', '.join(high_missing_cols[:3])}",
            }
        )

    return rag_queries


def save_eda_skill_artifacts(result: Dict[str, Any], output_dir: str) -> Dict[str, str]:
    os.makedirs(output_dir, exist_ok=True)
    result_path = os.path.join(output_dir, "eda_skill_result.json")
    llm_path = os.path.join(output_dir, "eda_skill_for_llm.json")

    with open(result_path, "w", encoding="utf-8") as result_file:
        json.dump(result, result_file, indent=2, ensure_ascii=True)

    with open(llm_path, "w", encoding="utf-8") as llm_file:
        json.dump(result.get("eda_for_llm", {}), llm_file, indent=2, ensure_ascii=True)

    return {"result_path": result_path, "llm_path": llm_path}


TOOL_REGISTRY: Dict[str, ToolFn] = {
    "load_tabular_data": load_tabular_data,
    "build_meta": build_meta,
    "build_schema": build_schema,
    "get_meta_info": get_meta_info,
    "get_schema_info": get_schema_info,
    "analyze_missing": analyze_missing,
    "analyze_distribution": analyze_distribution,
    "analyze_outliers": analyze_outliers,
    "build_target_summary": build_target_summary,
    "analyze_correlation": analyze_correlation,
    "generate_feature_insights": generate_feature_insights,
    "build_recommendations": build_recommendations,
    "compress_for_llm": compress_for_llm,
    "extract_kg_candidates": extract_kg_candidates,
    "build_rag_queries": build_rag_queries,
    "save_eda_skill_artifacts": save_eda_skill_artifacts,
}


def list_tools() -> List[str]:
    return sorted(TOOL_REGISTRY.keys())


def invoke_tool(tool_name: str, *args: Any, **kwargs: Any) -> Any:
    if tool_name not in TOOL_REGISTRY:
        raise KeyError(f"Unknown eda_skill tool: {tool_name}")
    return TOOL_REGISTRY[tool_name](*args, **kwargs)
