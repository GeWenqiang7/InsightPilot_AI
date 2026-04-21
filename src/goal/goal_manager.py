"""
Goal Manager（增强版）

✔ 多轮用户需求
✔ 上下文记忆
✔ goal生成
✔ goal选择
✔ goal重生成
✔ exit/reset
✔ JSON结构输出
"""

from src.goal.goal_generator import generate_goals
from src.goal.goal_schema import Goal
from typing import List
import json


# =========================
# 🔥 初始化状态
# =========================
def init_goal_state(df, user_query, knowledge_manager):

    return {
    "df": df,
    "conversation_history": [
        {"role": "user", "content": user_query}
    ],
    "candidate_goals": [],
    "selected_goal": None,
    "knowledge_manager": knowledge_manager    
     }


# =========================
#  构建上下文（核心升级）
# =========================
def build_query_from_history(history):

    return "\n".join([h["content"] for h in history])


# =========================
#  生成 goals（核心）
# =========================
def handle_goal_generation(state, llm_client):

    df = state["df"]
    history = state.get("conversation_history", [])

    if not history:
        raise ValueError("No user query")
    
    
    schema = state.get("schema")
    if schema is None:
        raise ValueError("Schema missing. Please load data first.")

    #  拼接历史
    full_query = build_query_from_history(history)

    print("\n🧠 当前上下文：")
    print(full_query)

    #创建知识管理器实例（如果还没有）
    km = state.get("knowledge_manager")

    goals: List[Goal] = generate_goals(
        user_query=full_query,
        schema_summary=schema,
        llm_client=llm_client,
        knowledge_manager=km
    )


    state["candidate_goals"] = goals

    return state


# =========================
# 🔥 展示 goals（JSON）
# =========================
def display_goals(state):

    goals = state.get("candidate_goals", [])

    goals_json = [g.to_dict() for g in goals]

    print("\n===== 当前候选 Goals =====")
    print(json.dumps(goals_json, indent=2, ensure_ascii=False))

    return goals_json


# =========================
# 🔥 选择 goal
# =========================
def select_goal(state, goal_id):

    goals = state.get("candidate_goals", [])

    for g in goals:
        if g.goal_id == goal_id:
            state["selected_goal"] = g

            print(f"\n✅ 已选择 Goal: {g.goal_name}")

            return state

    raise ValueError(f"Goal {goal_id} not found")


# =========================
# 🔥 用户追加需求（核心）
# =========================
def add_user_requirement(state, new_query):

    if "conversation_history" not in state:
        state["conversation_history"] = []

    state["conversation_history"].append({
        "role": "user",
        "content": new_query
    })

    # 🔥 控制长度（防爆token）
    state["conversation_history"] = state["conversation_history"][-5:]

    return state


# =========================
# 🔥 重新生成 goals
# =========================
def regenerate_goals(state, new_query, llm_client):

    state = add_user_requirement(state, new_query)

    return handle_goal_generation(state, llm_client)


# =========================
# 🔥 reset（新增）
# =========================
def reset_state(state):

    print("\n🔄 Reset system...")

    return {
        "df": state["df"],
        "conversation_history": [],
        "candidate_goals": [],
        "selected_goal": None
    }
