"""
测试 goal_manager 的交互式脚本
让用户输入需求，生成目标，选择目标，补充需求，重新生成目标
"""

import os
import sys
import pandas as pd


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.agent.goal_manager import (
    handle_goal_generation,
    select_goal,
    regenerate_goals,
    init_goal_state  
)


def load_data():
    data_path = os.path.join(
        os.path.dirname(__file__),
        '..',
        'data',
        'user_personalized_features.csv'
    )

    print("\n📂 Loading data...")
    print("Path:", data_path)

    if not os.path.exists(data_path):
        raise FileNotFoundError("❌ Data file not found")

    df = pd.read_csv(data_path)

    print("✅ Data loaded")
    print(f"Shape: {df.shape}")

    return df


def print_goals(goals):
    print("\n🎯 Candidate Goals:\n")

    for g in goals:
        print(f"[{g['goal_id']}] {g['goal_name']}")
        print(f"  - target: {g['target']}")
        print(f"  - type: {g['problem_type']}")
        print(f"  - reason: {g['reason']}")

        if "model_candidates" in g:
            print("  - models:")
            for m in g["model_candidates"]:
                print(f"      * {m['name']} ({m['category']})")

        print("-" * 50)


def print_history(history):
    print("\n🧠 当前需求历史：")
    for i, h in enumerate(history):
        print(f"{i+1}. {h}")


def interactive_loop():

    df = load_data()

    # =========================
    # 用户输入初始需求
    # =========================
    user_query = input("\n🧠 请输入你的分析需求：\n> ")

    # 🔥 初始化 state（关键）
    state = init_goal_state(df, user_query)

    while True:

        # =========================
        # 显示历史（新增）
        # =========================
        print_history(state["conversation_history"])

        # =========================
        # 生成 goals
        # =========================
        print("\n🤖 Generating goals...\n")

        state = handle_goal_generation(state)

        goals = state.get("candidate_goals", [])

        if not goals:
            print("❌ 没有生成目标，请重新输入")
            continue

        print_goals(goals)

        # =========================
        # 操作选项
        # =========================
        print("\n👉 操作选项：")
        print("1. 输入 goal_id 选择目标")
        print("2. 输入 'r' 补充需求（不会覆盖之前内容）")
        print("3. 输入 'q' 退出")

        choice = input("\n你的选择： ").strip()

        if choice.lower() == 'q':
            print("\n👋 已退出")
            break

        # 补充需求
        elif choice.lower() == 'r':
            new_query = input("\n🧠 请补充你的需求（无需重复之前内容）：\n> ")

            state = regenerate_goals(state, new_query)

            continue

        # 选择目标
        else:
            try:
                goal_id = int(choice)

                state = select_goal(state, goal_id)

                print("\n✅ 你选择的目标是：\n")
                print(state["selected_goal"])

                print("\n🚀 下一步：进入 EDA / FE / Model pipeline\n")

                break

            except Exception as e:
                print(f"\n❌ 选择无效: {e}")
                continue


if __name__ == "__main__":
    interactive_loop()