'''
EDA Tool 是一个“任务驱动的数据理解模块”，能够根据分析目标自动调整分析策略，并生成结构化结果供后续特征工程和建模模块使用。

输入：
    df + selected_goal（target + problem_type）

输出：
    eda_result（完整分析）
    eda_for_llm（压缩版）

流程：
1. 数据结构理解（schema）
2. 数据质量评估（missing/outlier）
3. 数据分布建模（distribution）
4. 自动规则洞察（insights）
5. 任务感知分析（problem_type）
6. LLM友好压缩（eda_for_llm）

'''

import os
import json
import numpy as np
import pandas as pd


# 导入EDA模块（
from src.eda.missing import analyze_missing
from src.eda.distribution import analyze_distribution
from src.eda.outlier import analyze_outliers
from src.eda.insights import generate_feature_insights
from src.eda.correlation import analyze_correlation
from eda.build_targets import analyze_target


# JSON安全处理
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



# EDA逻辑（模块化调度）
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

    # 缺失
    result["missing"] = analyze_missing(df)

    # 分布
    result["distribution"] = analyze_distribution(df)

    # 异常值
    result["outliers"] = analyze_outliers(df)

    # 3. target处理
    if target is not None:
        target_series, target_meta = analyze_target(df, target)
        result["target"] = target_meta
    else:
        target_series = None
        result["target"] = None


    # 4. correlation（如果有target则计算feature vs target相关性，否则计算pairwise相关性）
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


# 压缩给LLM（降低token）
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
    # 🔥 1. 根据 problem_type 调整 target
    # =========================
    if problem_type == "clustering":
        print("🔍 Clustering task → No target used")
        target = None

    # =========================
    # 🔥 2. 跑基础EDA
    # =========================
    eda_result = run_basic_eda(df, target)

    # =========================
    # 🔥 3. 加任务级分析（关键升级）
    # =========================
    eda_result["task_analysis"] = {}

    if problem_type == "classification":
        print("📊 Classification task → analyzing target distribution")

        if target in df.columns:
            eda_result["task_analysis"]["target_distribution"] = (
                df[target].value_counts(normalize=True).to_dict()
            )

    elif problem_type == "regression":
        print("📊 Regression task → analyzing target statistics")

        if target in df.columns:
            eda_result["task_analysis"]["target_stats"] = {
                "mean": float(df[target].mean()),
                "std": float(df[target].std()),
                "min": float(df[target].min()),
                "max": float(df[target].max())
            }

    elif problem_type == "clustering":
        print("📊 Clustering task → no target analysis")

    # =========================
    # 4. 保存
    # =========================
    full_path = os.path.join(eda_dir, "eda_result.json")

    with open(full_path, "w") as f:
        json.dump(eda_result, f, indent=2, default=json_safe)

    # =========================
    # 5. 压缩给LLM
    # =========================
    eda_small = compress_for_llm(eda_result)

    llm_path = os.path.join(eda_dir, "eda_for_llm.json")

    with open(llm_path, "w") as f:
        json.dump(eda_small, f, indent=2, default=json_safe)

    print(f"✅ EDA done. Saved to {eda_dir}")

    # =========================
    # 6. 更新 state
    # =========================
    state["eda_result"] = eda_result
    state["eda_for_llm"] = eda_small
    state["eda_path"] = eda_dir

    return state
