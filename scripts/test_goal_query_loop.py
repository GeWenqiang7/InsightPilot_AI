"""
测试「用户 query -> goal candidate 生成 -> 多轮补充 -> 选择 goal」闭环。

特点：
- 不依赖真实 OpenAI API
- 不需要交互式 input
- 覆盖 goal_manager + goal_generator + schema 的关键路径
"""

import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from src.goal.goal_manager import (  # noqa: E402
    display_goals,
    handle_goal_generation,
    init_goal_state,
    regenerate_goals,
    select_goal,
)
from src.knowledge.knowledge_manager import KnowledgeManager  # noqa: E402


class MockGoalLLM:
    def generate(self, prompt: str) -> str:
        # 用 prompt 中是否出现“new requirement”来模拟多轮需求后的目标变化
        if "new requirement" in prompt.lower():
            return """
[
  {
    "goal_id": 2,
    "goal_name": "控制误报下提升召回",
    "target": "churn_flag",
    "problem_type": "classification",
    "analysis_perspective": "风险控制",
    "business_value": "高",
    "model_candidates": [{"name":"XGBoost","category":"tree","reason":"鲁棒"}],
    "evaluation_suggestions": {"primary_metric":"recall","secondary_metrics":["precision"]},
    "risks": ["阈值敏感"],
    "score": 0.93,
    "confidence": 0.86,
    "priority_rank": 1,
    "reason": "满足最新业务约束"
  }
]
"""

        return """
[
  {
    "goal_id": 1,
    "goal_name": "预测用户流失",
    "target": "churn_flag",
    "problem_type": "classification",
    "analysis_perspective": "用户行为",
    "business_value": "高",
    "model_candidates": [{"name":"LogisticRegression","category":"linear","reason":"可解释"}],
    "evaluation_suggestions": {"primary_metric":"auc","secondary_metrics":["f1"]},
    "risks": ["类别不平衡"],
    "score": 0.89,
    "confidence": 0.82,
    "priority_rank": 1,
    "reason": "可直接用于留存运营"
  }
]
"""


def main() -> None:
    llm = MockGoalLLM()
    km = KnowledgeManager(llm_client=None)

    state = init_goal_state(
        df=None,
        user_query="我想预测用户流失并做运营干预",
        knowledge_manager=km,
    )
    state["schema"] = {
        "columns": [
            {"name": "age", "type": "int"},
            {"name": "income", "type": "float"},
            {"name": "churn_flag", "type": "int"},
        ]
    }

    # 首轮 goal 生成
    state = handle_goal_generation(state, llm)
    goals_round_1 = display_goals(state)
    assert len(goals_round_1) >= 1
    assert goals_round_1[0]["goal_name"] == "预测用户流失"
    assert "evidence" in goals_round_1[0]
    assert "retrieval_confidence" in goals_round_1[0]

    # 多轮补充需求后重生成
    state = regenerate_goals(state, "new requirement: 需要控制误报并强调召回", llm)
    goals_round_2 = display_goals(state)
    assert len(goals_round_2) >= 1
    assert goals_round_2[0]["goal_name"] == "控制误报下提升召回"
    assert "evidence_topics" in goals_round_2[0]

    # 用户选择
    state = select_goal(state, 2)
    selected = state["selected_goal"].to_dict()
    assert selected["goal_id"] == 2
    assert selected["problem_type"] == "classification"

    print("goal query loop test passed")


if __name__ == "__main__":
    main()
