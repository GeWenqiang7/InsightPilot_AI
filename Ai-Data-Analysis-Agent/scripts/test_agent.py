"""
Full Pipeline CLI

完整流程：
1. 用户输入分析需求
2. 多轮补充（带记忆）
3. 生成候选 goals
4. 用户选择 goal
5. Agent 执行：
    → EDA（任务感知）
    → FE（任务 + 模型感知）
6. 输出结果
"""

import os
import sys
import pandas as pd

# 让 Python 能找到 src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.agent.goal_manager import (
    handle_goal_generation,
    select_goal,
    regenerate_goals,
    init_goal_state
)

from src.agent.agent import DataAnalysisAgent


# =========================
# 数据加载
# =========================
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


# =========================
# 打印 goals
# =========================
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


# =========================
# 打印历史
# =========================
def print_history(history):

    print("\n🧠 当前需求历史：")
    for i, h in enumerate(history):
        print(f"{i+1}. {h}")


# =========================
# 主流程
# =========================
def main():

    print("\n🚀 AI Data Analysis Agent (CLI)\n")

    df = load_data()

    # =========================
    # 1️⃣ 用户输入需求
    # =========================
    user_query = input("\n🧠 请输入你的分析需求：\n> ")

    state = init_goal_state(df, user_query)

    # =========================
    # 2️⃣ Goal 选择循环
    # =========================
    while True:

        print_history(state["conversation_history"])

        print("\n🤖 Generating candidate goals...\n")

        state = handle_goal_generation(state)

        goals = state.get("candidate_goals", [])

        if not goals:
            print("❌ 没有生成目标，请重新输入")
            continue

        print_goals(goals)

        print("\n👉 操作选项：")
        print("1. 输入 goal_id 选择目标")
        print("2. 输入 'r' 补充需求（不会覆盖历史）")
        print("3. 输入 'q' 退出")

        choice = input("\n你的选择： ").strip()

        # =========================
        # 退出
        # =========================
        if choice.lower() == 'q':
            print("\n👋 已退出")
            return

        # =========================
        # 补充需求（多轮记忆）
        # =========================
        elif choice.lower() == 'r':

            new_query = input("\n🧠 请补充你的需求（无需重复之前内容）：\n> ")

            state = regenerate_goals(state, new_query)

            continue

        # =========================
        # 选择目标
        # =========================
        else:
            try:
                goal_id = int(choice)

                state = select_goal(state, goal_id)

                print("\n✅ 已选择目标：\n")
                print(state["selected_goal"])

                break

            except Exception as e:
                print(f"\n❌ 选择无效: {e}")
                continue

    # =========================
    # 3️⃣ Agent 执行
    # =========================
    print("\n🚀 Running Agent Pipeline...\n")

    agent = DataAnalysisAgent()

    state = agent.run(state)

    # =========================
    # 4️⃣ 输出结果
    # =========================
    print("\n📊 EDA Result Keys:")
    print(state.get("eda_result", {}).keys())

    print("\n📄 Feature Engineering Plan:")
    print(state.get("fe_plan", {}))

    print("\n✅ Pipeline completed!\n")


# =========================
# 入口
# =========================
if __name__ == "__main__":
    main()