"""
1. 调用 goal_generator
2. 返回 candidate_goals
3. 接收用户选择
4. 支持多轮补充（带记忆）
"""

from src.utils.schema_utils import build_schema_summary
from src.llm.goal_generator import generate_goals


# 生成目标（支持多轮上下文）
def handle_goal_generation(state):
    """
    根据 conversation_history 生成候选 goals
    """

    df = state["df"]

    # 使用历史
    history = state.get("conversation_history", [])

    if not history:
        raise ValueError("❌ No user query provided")

    schema = build_schema_summary(df)

    goals = generate_goals(history, schema)

    state["candidate_goals"] = goals

    return state


# 用户选择目标
def select_goal(state, goal_id):

    goals = state.get("candidate_goals", [])

    for g in goals:
        if g.get("goal_id") == goal_id:
            state["selected_goal"] = g
            return state

    raise ValueError(f"Goal {goal_id} not found")


# 用户补充需求（不会覆盖历史）
def regenerate_goals(state, new_query):
    """
    用户补充需求（不会覆盖历史）
    """

    # 初始化 history（如果不存在）
    if "conversation_history" not in state:
        state["conversation_history"] = []

    # 追加，而不是覆盖
    state["conversation_history"].append(new_query)

    # 防止过长（保留最近5条）
    state["conversation_history"] = state["conversation_history"][-5:]

    return handle_goal_generation(state)



# 初始化入口
def init_goal_state(df, user_query):
    """
    初始化 state（第一轮输入）
    """

    return {
        "df": df,
        "conversation_history": [user_query],
        "candidate_goals": [],
        "selected_goal": None
    }