"""
    构建轻量级数据结构摘要（供LLM使用）

    输出：
    {
        "num_rows": ...,
        "num_columns": ...,
        "columns": {
            col_name: {
                "dtype": "...",
                "n_unique": ...,
                "example_values": [...]
            }
        }
    }
    """

import pandas as pd

def build_schema_summary(df: pd.DataFrame):
    
    summary = {
        "num_rows": int(df.shape[0]),
        "num_columns": int(df.shape[1]),
        "columns": {}
    }

    for col in df.columns:
        summary["columns"][col] = {
            "dtype": str(df[col].dtype),
            "n_unique": int(df[col].nunique()),
            "example_values": df[col].dropna().astype(str).unique()[:3].tolist()
        }

    return summary