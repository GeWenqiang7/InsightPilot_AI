# run_eda.py
# =====================================
# 作用：
# 1. 读取数据
# 2. 运行EDA Pipeline
# 3. 保存完整EDA（debug/RAG）
# 4. 生成压缩EDA（LLM用）
# =====================================

import os
import json
import pandas as pd

from eda.pipeline import EDAPipeline


# ================================
# 1. JSON序列化工具
# ================================
def json_converter(o):
    import numpy as np
    import pandas as pd

    if isinstance(o, (np.integer,)):
        return int(o)
    elif isinstance(o, (np.floating,)):
        if pd.isna(o):
            return None
        return float(o)
    elif isinstance(o, (np.ndarray,)):
        return o.tolist()
    elif isinstance(o, pd.Series):
        return o.to_dict()
    elif isinstance(o, pd.DataFrame):
        return o.to_dict()
    else:
        return str(o)


# ================================
# 2. 路径
# ================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)

data_path = os.path.join(
    PROJECT_ROOT,
    "douyinshop_data",
    "user_personalized_features.csv"
)

print("📂 数据路径:", data_path)
print("📂 是否存在:", os.path.exists(data_path))


# ================================
# 3. 读取数据
# ================================
df = pd.read_csv(data_path)

print("✅ 数据加载成功")
print("Shape:", df.shape)


# ================================
# 4. 定义 target
# ================================
target = "Total_Spending"


# ================================
# 5. 跑EDA
# ================================
eda = EDAPipeline(df, target=target)
result = eda.run()

print("\n🚀 EDA运行成功 ✅")
print("模块输出：", result.keys())


# ================================
# 6. 保存完整EDA（RAG/debug）
# ================================
full_path = os.path.join(PROJECT_ROOT, "eda_result.json")

with open(full_path, "w") as f:
    json.dump(result, f, indent=2, default=json_converter)

print(f"\n💾 完整EDA已保存：{full_path}")


# ================================
# 7. 🔥 LLM压缩（核心升级）
# ================================
def compress_eda_for_llm(eda):

    compressed = {
        "meta": eda.get("meta", {}),
        "features": {},
        "high_missing": {},
        "top_correlations": eda.get("correlation", {}).get("top_features", []),
        "insights": eda.get("feature_insights", [])
    }

    schema = eda.get("schema", {})
    dist = eda.get("distribution", {})
    missing = eda.get("missing", {})

    for col, col_type in schema.items():

        feature_info = {
            "type": col_type
        }

        # =====================
        # 数值特征（来自 distribution）
        # =====================
        if col in dist:
            d = dist[col]

            feature_info.update({
                "mean": round(d.get("mean", 0), 3),
                "std": round(d.get("std", 0), 3),
                "skew": round(d.get("skew", 0), 3)
            })

        # =====================
        # 缺失
        # =====================
        if col in missing:
            miss_rate = missing[col].get("missing_rate", 0)
            feature_info["missing"] = round(miss_rate, 3)

            if miss_rate > 0.3:
                compressed["high_missing"][col] = round(miss_rate, 3)

        compressed["features"][col] = feature_info

    return compressed

# ================================
# 8. 生成LLM输入
# ================================
eda_small = compress_eda_for_llm(result)

llm_path = os.path.join(PROJECT_ROOT, "eda_for_llm.json")

with open(llm_path, "w") as f:
    json.dump(eda_small, f, indent=2, default=json_converter)

print(f"🤖 LLM输入已保存：{llm_path}")