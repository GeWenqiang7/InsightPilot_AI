#确认target feature
#feature correlation

import pandas as pd

def resolve_target(df, target_config):
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