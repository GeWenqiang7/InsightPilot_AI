'''
EDA Tool 是一个专门设计用于自动化探索性数据分析的工具，旨在为数据科学家和机器学习工程师提供快速、全面的数据洞察。
它不仅生成详细的EDA报告，还抽取结构化的KG候选关系，支持后续的特征工程和建模步骤。

输入：
- DataFrame（必需）：待分析的数据集
- target（可选）：分析目标列，若提供将进行针对性分析

输出：
- eda_result.json：完整的EDA分析结果，包含数据质量、分布、相关性等信息
- eda_for_llm.json：压缩后的EDA结果，适合LLM快速理解
- kg_candidates：从EDA结果中抽取的KG候选关系，供后续模块使用    

核心功能：
1. 自动识别数据类型和分析目标，调整EDA策略
2. 生成结构化的EDA结果，包括数据质量、分布、相关性等分析
3. 从EDA结果中抽取KG候选关系，供后续模块使用
4. 兼容旧调用方式，同时支持OpenAI function-calling接口

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
from src.eda.build_targets import analyze_target


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
# Function Calling: 工具定义
# =========================
def get_tool_definition():
    """
    返回 OpenAI function-calling 所需工具定义
    """
    return {
        "type": "function",
        "function": {
            "name": "run_eda",
            "description": "Run exploratory data analysis and return summary + kg candidates.",
            "parameters": {
                "type": "object",
                "properties": {
                    "target": {"type": ["string", "null"]},
                    "problem_type": {
                        "type": ["string", "null"],
                        "enum": ["classification", "regression", "clustering", None]
                    },
                    "output_dir": {"type": "string"}
                },
                "required": [],
                "additionalProperties": False
            }
        }
    }


# =========================
# 新增：KG候选构建
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

    # 1️⃣ feature → target关系
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

    # 2️⃣ Top重要特征
    top_feats = corr.get("top_features", [])
    for f in top_feats:
        if isinstance(f, dict) and "feature" in f:
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
        result["correlation"] = {"error": str(e)}

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
        info = {"type": schema[col]["dtype"]}

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
# 主入口（兼容旧调用）
# =========================
def run(state):
    """
    兼容你当前 agent 中 eda_run(state) 的调用方式
    """
    print("🚀 [EDA TOOL] Running...")

    if "df" not in state:
        raise ValueError("Missing 'df' in state.")

    df = state["df"]
    target = state.get("target", None)
    problem_type = state.get("problem_type", None)

    # 输出路径
    base_dir = state.get("output_dir", "output")
    eda_dir = os.path.join(base_dir, "eda")
    os.makedirs(eda_dir, exist_ok=True)

    # 1. 调整target
    if problem_type == "clustering":
        print("🔍 Clustering task → No target used")
        target = None

    # 2. 跑EDA
    eda_result = run_basic_eda(df, target)

    # 3. KG候选构建
    kg_candidates = extract_kg_candidates(eda_result)
    eda_result["kg_candidates"] = kg_candidates

    # 4. task-level分析
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

    # 5. 保存
    full_path = os.path.join(eda_dir, "eda_result.json")
    with open(full_path, "w", encoding="utf-8") as f:
        json.dump(eda_result, f, indent=2, default=json_safe, ensure_ascii=False)

    # 6. 压缩给LLM
    eda_small = compress_for_llm(eda_result)

    llm_path = os.path.join(eda_dir, "eda_for_llm.json")
    with open(llm_path, "w", encoding="utf-8") as f:
        json.dump(eda_small, f, indent=2, default=json_safe, ensure_ascii=False)

    print(f"✅ EDA done. Saved to {eda_dir}")

    # 7. 更新 state
    state["eda_result"] = eda_result
    state["eda_for_llm"] = eda_small
    state["eda_path"] = eda_dir
    state["kg_candidates"] = kg_candidates

    return state


# =========================
# Function Calling: 执行入口
# =========================
def invoke(params, state):
    """
    供 function-calling 执行：
    - params: 模型传入的函数参数
    - state : 运行上下文（至少包含 df）
    返回:
    - tool_result: 给模型看的结构化结果
    - new_state : 更新后的状态
    """
    if params is None:
        params = {}

    local_state = dict(state)

    # 用 function 参数覆盖 state（若提供）
    if "target" in params:
        local_state["target"] = params.get("target")
    if "problem_type" in params:
        local_state["problem_type"] = params.get("problem_type")
    if "output_dir" in params:
        local_state["output_dir"] = params.get("output_dir")

    local_state = run(local_state)

    tool_result = {
        "eda_path": local_state.get("eda_path"),
        "meta": local_state.get("eda_result", {}).get("meta", {}),
        "insights_count": len(local_state.get("eda_result", {}).get("insights", [])),
        "kg_relations_count": len(local_state.get("kg_candidates", {}).get("relations", [])),
        "important_features_count": len(local_state.get("kg_candidates", {}).get("important_features", []))
    }

    return tool_result, local_state