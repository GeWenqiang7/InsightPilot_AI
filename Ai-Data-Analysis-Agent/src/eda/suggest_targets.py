'''
执行 target + 校验 target
'''

import pandas as pd


# 自动生成候选target
def suggest_targets(df):
    """
    基于数据结构，生成候选 target（不依赖LLM，先做规则版MVP）

    后期可以升级为 LLM版本
    """

    candidates = []

    for col in df.columns:

        unique_ratio = df[col].nunique() / len(df)

        # 1️⃣ 二分类候选（分类问题）
        if df[col].nunique() == 2:
            candidates.append({
                "target": col,
                "type": "classification",
                "reason": "binary variable"
            })

        # 2️⃣ 类别型（低基数）
        elif df[col].nunique() < 20:
            candidates.append({
                "target": col,
                "type": "classification",
                "reason": "low cardinality categorical"
            })

        # 3️⃣ 连续变量（回归）
        elif pd.api.types.is_numeric_dtype(df[col]):
            candidates.append({
                "target": col,
                "type": "regression",
                "reason": "continuous numeric variable"
            })

    return candidates



# 原有：执行 target（保留）
def analyze_target(df, target_config):
    """
    支持三种target定义：
    1. 字符串列名
    2. 函数
    3. 表达式字符串
    """

    # 直接列名
    if isinstance(target_config, str) and target_config in df.columns:
        return df[target_config], {
            "type": "column",
            "name": target_config
        }

    # 表达式（如 "click / impression"）
    if isinstance(target_config, str):
        try:
            target_series = df.eval(target_config)
            return target_series, {
                "type": "expression",
                "formula": target_config
            }
        except Exception:
            raise ValueError(f"Invalid target expression: {target_config}")

    # 函数
    if callable(target_config):
        target_series = target_config(df)
        return target_series, {
            "type": "function",
            "description": target_config.__name__ if hasattr(target_config, "__name__") else "lambda"
        }

    raise ValueError("Unsupported target_config type")