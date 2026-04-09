# scripts/test_pipeline.py

import os
import pandas as pd

from src.tools.eda_tool import run as eda_run
from src.tools.fe_tool import run as fe_run


def main():

    print("🚀 Starting pipeline test...")

    # 1. 读取数据
    data_path = "data/user_personalized_features.csv"

    if not os.path.exists(data_path):
        raise FileNotFoundError(f"❌ Data not found: {data_path}")

    df = pd.read_csv(data_path)

    print(f"✅ Data loaded: {df.shape}")

    # 2. 初始化 state
    state = {
        "df": df,
        "target": "Total_Spending",          
        "output_dir": "output"
    }

    # ============================
    # 3. 跑 EDA
    # ============================
    print("\n📊 Running EDA...")
    state = eda_run(state)

    # 检查EDA输出
    assert "eda_result" in state
    assert "eda_for_llm" in state

    print("✅ EDA finished")

    # ============================
    # 4. 跑 Feature Engineering
    # ============================
    print("\n🧠 Running Feature Engineering...")
    state = fe_run(state)

    # 检查FE输出
    assert "fe_plan" in state

    print("✅ FE finished")

    # ============================
    # 5. 打印结果
    # ============================
    print("\n📄 FE PLAN:")
    print(state["fe_plan"])

    print("\n🎉 Pipeline test completed successfully!")


if __name__ == "__main__":
    main()