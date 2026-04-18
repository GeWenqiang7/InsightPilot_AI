'''
升级版 Agent：
✔ 支持 goal selection
✔ 自动 target 解析
✔ EDA → FE pipeline
✔ 状态安全检查

输入：state（包含用户选择的 goal、数据等信息）

数据输入（至少包含以下字段之一）：
- file_path: 文件路径（支持 CSV、Excel 等格式）
- file_obj: 文件对象（优先级低于 file_path）    

输出：更新后的 state（包含解析后的 target、EDA/FE 结果等信息）
'''
from src.tools.eda_tool import run as eda_run
from src.tools.fe_tool import run as fe_run
from src.eda.build_targets import analyze_target


class DataAnalysisAgent:

    def __init__(self):
        pass

    def run(self, state):

        print("\n🤖 [Agent] Starting pipeline...")

        # =========================
        # 基础检查
        # =========================
        if "df" not in state:
            raise ValueError("Data not found in state. Please load data first.")

        # =========================
        # 1️⃣ 等待用户选择目标
        # =========================
        if "selected_goal" not in state or state["selected_goal"] is None:
            print("\n⏸ [Agent] Waiting for user to select a goal...")
            return state

        selected_goal = state["selected_goal"]

        print("\n🎯 [Agent] Selected Goal:")
        print(selected_goal)

        # =========================
        # 2️⃣ 从 Goal 提取信息 （支持多目标/子目标）
        # =========================
        state["target"] = selected_goal.target
        state["problem_type"] = selected_goal.problem_type
        state["model_candidates"] = selected_goal.model_candidates

        # =========================
        # 3️⃣ 解析 target（支持表达式/函数）
        # =========================
        if state["target"] is not None:
            print("\n🧩 [Agent] Parsing target...")

            target_series, target_meta = analyze_target(
                state["df"],
                state["target"]
            )

            state["target_series"] = target_series
            state["target_meta"] = target_meta

            print("✅ Target parsed:", target_meta)

        else:
            print("\n📊 [Agent] No target (clustering task)")
            state["target_series"] = None

        # =========================
        # 4️⃣ EDA
        # =========================
        print("\n📊 [Agent] Running EDA Tool...")
        state = eda_run(state)

        # =========================
        # 5️⃣ Feature Engineering
        # =========================
        print("\n🧠 [Agent] Running FE Tool...")
        state = fe_run(state)

        print("\n✅ [Agent] Pipeline finished!")

        return state