'''
EDA Tool 是一个“任务驱动的数据理解模块”，能够根据分析目标自动调整分析策略，并生成结构化结果供后续特征工程和建模模块使用。

输入：
- DataFrame（数据集）
- target（可选，分析目标）
- problem_type（可选，任务类型：classification/regression/clustering）

输出：
- eda_result.json（完整EDA结果）
- eda_for_llm.json（压缩版，供LLM使用）

核心功能：
- 自动调整分析策略（根据problem_type和target）
- 生成结构化的EDA结果（包含meta、schema、missing、distribution、outliers、correlation、insights等）
- KG候选构建（从EDA结果中抽取结构化关系）

'''

import os
import json
import numpy as np
import pandas as pd

# 导入EDA模块
from src.eda.missing import analyze_missing
from src.eda.distribution import analyze_distribution
from src.eda.outlier import analyze_outliers
from src.eda.insights import generate_feature_insights
from src.eda.correlation import analyze_correlation
from eda.build_targets import analyze_target


# =========================
# JSON安全处理
# =========================
def json_safe(obj):
    if isinstance(obj, (np.integer,)):
        return int(obj)
    elif isinstance(obj, (np.floating,)):
        return float(obj)
    elif isinstance(obj, (np.ndarray,)):
        return obj.tolist()
    elif isinstance(obj, pd.Series):
        return obj.to_dict()
    elif isinstance(obj, pd.DataFrame):
        return obj.to_dict()
    return str(obj)


# =========================
#  新增：KG候选构建
# =========================
def extract_kg_candidates(eda_result):
    """
    从EDA结果中抽取结构化关系（KG候选）
    """

    kg = {
        "relations": [],
        "important_features": []
    }

    corr = eda_result.get("correlation", {})

    # =========================
    # 1️⃣ feature → target关系
    # =========================
    feature_target_corr = corr.get("feature_target_correlation", {})

    for feature, value in feature_target_corr.items():
        if value is None:
            continue

        relation = {
            "source": feature,
            "target": "TARGET",
            "type": "correlated_with",
            "strength": float(value)
        }

        kg["relations"].append(relation)

    # =========================
    # 2️⃣ Top重要特征
    # =========================
    top_feats = corr.get("top_features", [])

    for f in top_feats:
        kg["important_features"].append(f["feature"])

    return kg


# =========================
# EDA逻辑（模块化调度）
# =========================
def run_basic_eda(df, target=None):

    result = {}

    # 1. meta + schema
    result["meta"] = {
        "rows": df.shape[0],
        "cols": df.shape[1]
    }

    result["schema"] = {
        col: {
            "dtype": str(df[col].dtype),
            "n_unique": int(df[col].nunique())
        }
        for col in df.columns
    }

    # 2. 各模块分析
    result["missing"] = analyze_missing(df)
    result["distribution"] = analyze_distribution(df)
    result["outliers"] = analyze_outliers(df)

    # 3. target处理
    if target is not None:
        target_series, target_meta = analyze_target(df, target)
        result["target"] = target_meta
    else:
        target_series = None
        result["target"] = None

    # 4. correlation
    try:
        result["correlation"] = analyze_correlation(df, target_series)
    except Exception as e:
        result["correlation"] = {
            "error": str(e)
        }

    # 5. insights
    result["insights"] = generate_feature_insights(
        result["missing"],
        result["distribution"],
        result["outliers"]
    )

    return result


# =========================
# 压缩给LLM（降低token）
# =========================
def compress_for_llm(eda):

    compressed = {
        "meta": eda.get("meta", {}),
        "features": {},
        "insights": eda.get("insights", [])
    }

    schema = eda.get("schema", {})
    dist = eda.get("distribution", {})
    missing = eda.get("missing", {})

    for col in schema:

        info = {
            "type": schema[col]["dtype"]
        }

        if col in dist:
            info.update({
                "mean": round(dist[col]["mean"], 3),
                "std": round(dist[col]["std"], 3),
                "skew": round(dist[col]["skew"], 3)
            })

        if col in missing:
            info["missing"] = round(missing[col]["missing_rate"], 3)

        compressed["features"][col] = info

    return compressed


# =========================
# 主入口
# =========================
def run(state):

    print("🚀 [EDA TOOL] Running...")

    df = state["df"]
    target = state.get("target", None)
    problem_type = state.get("problem_type", None)

    # 输出路径
    base_dir = state.get("output_dir", "output")
    eda_dir = os.path.join(base_dir, "eda")
    os.makedirs(eda_dir, exist_ok=True)

    # =========================
    # 1. 调整target
    # =========================
    if problem_type == "clustering":
        print("🔍 Clustering task → No target used")
        target = None

    # =========================
    # 2. 跑EDA
    # =========================
    eda_result = run_basic_eda(df, target)

    # =========================
    # 🔥 3. KG候选构建（核心升级）
    # =========================
    kg_candidates = extract_kg_candidates(eda_result)
    eda_result["kg_candidates"] = kg_candidates

    # =========================
    # 4. task-level分析
    # =========================
    eda_result["task_analysis"] = {}

    if problem_type == "classification":

        if target in df.columns:
            eda_result["task_analysis"]["target_distribution"] = (
                df[target].value_counts(normalize=True).to_dict()
            )

    elif problem_type == "regression":

        if target in df.columns:
            eda_result["task_analysis"]["target_stats"] = {
                "mean": float(df[target].mean()),
                "std": float(df[target].std()),
                "min": float(df[target].min()),
                "max": float(df[target].max())
            }

    # =========================
    # 5. 保存
    # =========================
    full_path = os.path.join(eda_dir, "eda_result.json")

    with open(full_path, "w") as f:
        json.dump(eda_result, f, indent=2, default=json_safe)

    # =========================
    # 6. 压缩给LLM
    # =========================
    eda_small = compress_for_llm(eda_result)

    llm_path = os.path.join(eda_dir, "eda_for_llm.json")

    with open(llm_path, "w") as f:
        json.dump(eda_small, f, indent=2, default=json_safe)

    print(f"✅ EDA done. Saved to {eda_dir}")

    # =========================
    # 7. 更新 state（关键）
    # =========================
    state["eda_result"] = eda_result
    state["eda_for_llm"] = eda_small
    state["eda_path"] = eda_dir

    # 🔥 新增
    state["kg_candidates"] = kg_candidates

    return state