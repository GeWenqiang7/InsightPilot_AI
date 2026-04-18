'''
测试：目标生成器（Goal Generator）
- 目标：验证目标生成器模块的功能和性能，确保其能够根据用户输入和数据 schema 生成合理的分析目标。
- 输入：用户的分析需求（自然语言）和数据的 schema摘要   
- 输出：一组候选分析目标（包含目标名称、类型、相关模型建议等）
'''

import os
import sys
import pandas as pd


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.utils.schema_utils import build_schema_summary
from src.llm.goal_generator import generate_goals

def main():

    print("\n🚀 Starting Goal Generator Test...\n")

    # 读数据
    data_path = os.path.join(
        os.path.dirname(__file__),
        '..',
        'data',
        'user_personalized_features.csv'
    )

    df = pd.read_csv(data_path)

    print("✅ Data loaded")
    print(f"Shape: {df.shape}")

    # 用户输入分析需求
    user_query = "我想分析用户的购买行为，找出哪些因素影响了他们的总消费金额，并预测未来的消费趋势。"

    print("\n🧠 User Query:")
    print(user_query)


    # 自动 schema
    schema = build_schema_summary(df)

    print("\n📊 Schema Summary (preview):")
    print({
        "num_rows": schema["num_rows"],
        "num_columns": schema["num_columns"]
    })


    # 生成目标
    goals = generate_goals(user_query, schema)


    # 输出分析目标
    print("\n🎯 Candidate Goals:\n")

    if isinstance(goals, list):
        for g in goals:
            print(g)
    else:
        print("❌ Error:")
        print(goals)


if __name__ == "__main__":
    main()