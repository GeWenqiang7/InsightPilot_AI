# run_eda.py
# =====================================
# 作用：
# 1. 读取数据
# 2. 运行EDA Pipeline
# 3. 处理JSON序列化问题
# 4. 保存结果（给RAG/LLM用）
# =====================================

import os
import json
import pandas as pd

from eda.pipeline import EDAPipeline

# 1. JSON序列化工具
def json_converter(o):
    import numpy as np
    import pandas as pd

    if isinstance(o, (np.integer,)):
        return int(o)
    elif isinstance(o, (np.floating,)):
        return float(o)
    elif isinstance(o, (np.ndarray,)):
        return o.tolist()
    elif isinstance(o, pd.Series):
        return o.to_dict()
    elif isinstance(o, pd.DataFrame):
        return o.to_dict()
    else:
        return str(o)


# 2. 获取路径
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 项目根目录
PROJECT_ROOT = os.path.dirname(BASE_DIR)

# 数据路径
data_path = os.path.join(
    PROJECT_ROOT,
    "douyinshop_data",
    "user_personalized_features.csv"
)

print("📂 数据路径:", data_path)
print("📂 是否存在:", os.path.exists(data_path))


# 3. 读取数据
df = pd.read_csv(data_path)

print("✅ 数据加载成功")
print("Shape:", df.shape)


# 定义 target

# ✅ 方式1：列名
target = "Total_Spending"

# ✅ 方式2（可选）：表达式
# target = "click / impression"

# ✅ 方式3（可选）：函数
# def my_target(df):
#     return (df["revenue"] - df["cost"]) / df["cost"]
# target = my_target


# 跑EDA
eda = EDAPipeline(df, target=target)
result = eda.run()

print("\n🚀 EDA运行成功 ✅")
print("模块输出：", result.keys())


# 保存结果（RAG用）
output_path = os.path.join(PROJECT_ROOT, "eda_result.json")

with open(output_path, "w") as f:
    json.dump(result, f, indent=2, default=json_converter)

print(f"\n💾 EDA结果已保存：{output_path}")


# 压缩给LLM用

def compress_eda_for_llm(eda):
    return {
        "high_missing": {
            k: v for k, v in eda["missing"].items()
            if v["missing_rate"] > 0.2
        },
        "top_features": eda["correlation"].get("top_features", []),
        "insights": eda["feature_insights"]
    }


eda_small = compress_eda_for_llm(result)

llm_path = os.path.join(PROJECT_ROOT, "eda_for_llm.json")

with open(llm_path, "w") as f:
    json.dump(eda_small, f, indent=2, default=json_converter)

print(f"🤖 LLM输入已保存：{llm_path}")