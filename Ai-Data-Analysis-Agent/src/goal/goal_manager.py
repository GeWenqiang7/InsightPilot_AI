"""
输入：
- 用户查询：用户的分析需求描述
- 数据集schema：数据集的结构化描述（字段、类型、示例等）

输出：
- 候选分析目标列表：每个目标包含目标ID、名称、分析对象（可选）、问题类型、模型候选列表以及选择理由

主要功能：
- 生成分析目标：调用goal_generator模块，根据用户查询和数据集schema生成候选分析目标列表。
- 选择分析目标：根据用户的选择，确定最终的分析目标。
- 更新分析目标：根据用户的反馈或新的查询，重新生成或调整分析目标列表。
"""

from src.goal.goal_generator import generate_goals
from src.goal.goal_schema import Goal
from typing import List


def handle_goal_generation(state, llm_client):

    df = state["df"]
    history = state.get("conversation_history", [])

    if not history:
        raise ValueError("No user query")

    schema = state["schema"]  # 建议提前算好

    goals: List[Goal] = generate_goals(
        user_query=" ".join(history),
        schema_summary=schema,
        llm_client=llm_client
    )

    state["candidate_goals"] = goals

    return state


def select_goal(state, goal_id):

    goals = state.get("candidate_goals", [])

    for g in goals:
        if g.goal_id == goal_id:
            state["selected_goal"] = g
            return state

    raise ValueError(f"Goal {goal_id} not found")


def regenerate_goals(state, new_query, llm_client):

    if "conversation_history" not in state:
        state["conversation_history"] = []

    state["conversation_history"].append(new_query)
    state["conversation_history"] = state["conversation_history"][-5:]

    return handle_goal_generation(state, llm_client)


def init_goal_state(df, user_query):

    return {
        "df": df,
        "conversation_history": [user_query],
        "candidate_goals": [],
        "selected_goal": None
    }