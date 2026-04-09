'''
state → 决策 → 调用tool → 更新state
1. 等待用户选择目标（系统层）：如果 state 中没有 selected_goal，暂停执行，等待用户输入。
2. 设置 target（系统层）：从 selected_goal 中提取 target、problem_type 和 model_candidates，更新 state。
3. EDA（工具层）：调用 eda_tool.run(state)，执行EDA分析，并将结果更新回 state。
4. Feature Engineering（工具层）：调用 fe_tool.run(state)，执行特征工程，并将结果更新回 state。 
'''

from src.tools.eda_tool import run as eda_run
from src.tools.fe_tool import run as fe_run
from src.eda.build_targets import analyze_target

class DataAnalysisAgent:
    """
    升级版 Agent：
    支持 goal selection + 中断执行
    """

    def __init__(self):
        pass

    def run(self, state):

        print("\n🤖 [Agent] Starting pipeline...")


        #  等待用户选择目标
        if "selected_goal" not in state or state["selected_goal"] is None:
            print("\n⏸ [Agent] Waiting for user to select a goal...")
            return state


        # 设置 target
        selected_goal = state["selected_goal"]

        print("\n🎯 [Agent] Selected Goal:")
        print(selected_goal)

        state["target"] = selected_goal.get("target")
        state["problem_type"] = selected_goal.get("problem_type")
        state["model_candidates"] = selected_goal.get("model_candidates")

        # =========================
        # Step 2: EDA
        # =========================
        print("\n📊 [Agent] Running EDA Tool...")
        state = eda_run(state)

        # =========================
        # Step 3: Feature Engineering
        # =========================
        print("\n🧠 [Agent] Running FE Tool...")
        state = fe_run(state)

        print("\n✅ [Agent] Pipeline finished!")

        return state