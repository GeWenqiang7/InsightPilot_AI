'''
数据加载模块
功能：
- 统一数据加载接口，支持多种格式（CSV、Excel等）
- 构建数据 schema，供后续 goal 生成使用
输入：
- file_path: 数据文件路径（CSV、Excel等）
- file_obj: 文件对象（可选，优先级低于 file_path）
输出：
- state["df"]: 加载后的 DataFrame
- state["schema"]: 数据 schema，包括字段名称、类型和描述
'''


import os
import pandas as pd


def load_data(state):
    """
    统一数据入口（支持扩展）

    输入：
        state["file_path"] 或 state["file_obj"]

    输出：
        state["df"]
        state["schema"]
    """

    print("\n📂 [Data Loader] Loading dataset...")

    file_path = state.get("file_path")
    file_obj = state.get("file_obj")

    if file_path:

        if not os.path.exists(file_path):
            raise ValueError(f"File not found: {file_path}")

        if file_path.endswith(".csv"):
            df = pd.read_csv(file_path)

        elif file_path.endswith(".xlsx"):
            df = pd.read_excel(file_path)

        else:
            raise ValueError("Unsupported file format")

    elif file_obj:
        df = pd.read_csv(file_obj)

    else:
        raise ValueError("No data input provided")

    # 🔥 构建 schema（给 goal 用）
    schema = {
        col: {
            "dtype": str(df[col].dtype),
            "n_unique": int(df[col].nunique())
        }
        for col in df.columns
    }

    state["df"] = df
    state["schema"] = schema

    print("✅ Data loaded successfully")

    return state