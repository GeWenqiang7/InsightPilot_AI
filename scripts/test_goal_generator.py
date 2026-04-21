'''
测试脚本：测试goal_generator模块的功能和输出

主要功能：
1. 模拟用户查询和数据集schema输入，调用goal_generator生成分析目标。
2. 输出生成的目标列表，验证其结构和内容是否符合预期。

使用说明：
1. 确保已安装必要的依赖（如openai等）。
2. 运行脚本：python test_goal_generator.py
3. 查看输出的分析目标列表，验证其正确性和合理性。
'''

import sys
import os
import json

# =========================
# 修复路径
# =========================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from src.goal.goal_generator import generate_goals
from src.knowledge.knowledge_manager import KnowledgeManager
from src.llm.client import LLMClient


# =========================
# Mock LLM（用于生成goal）
# =========================
class MockLLM:
    def generate(self, prompt):

        print("\n===== LLM收到的Prompt（截断） =====")
        print(prompt[:800])
        print("=================================\n")

        return """
[
  {
    "goal_id": 1,
    "goal_name": "预测用户流失",
    "target": "是否流失",
    "problem_type": "classification",
    "analysis_perspective": "用户行为分析",
    "business_value": "提升留存率",

    "model_candidates": [
      {
        "name": "XGBoost",
        "category": "tree",
        "reason": "适合非线性",
        "strength": "表现强",
        "risk": "可能过拟合"
      }
    ],

    "evaluation_suggestions": {
      "primary_metric": "AUC",
      "secondary_metrics": ["F1"],
      "cv_strategy": "Stratified KFold"
    },

    "risks": ["数据不平衡"],

    "score": 0.92,
    "confidence": 0.9,
    "priority_rank": 1,

    "reason": "核心业务问题"
  },
  {
    "goal_id": 2,
    "goal_name": "用户分群",
    "target": null,
    "problem_type": "clustering",

    "analysis_perspective": "用户细分",
    "business_value": "精准营销",

    "model_candidates": [
      {
        "name": "KMeans",
        "category": "clustering",
        "reason": "简单有效",
        "strength": "快速",
        "risk": "需要归一化"
      }
    ],

    "evaluation_suggestions": {},

    "risks": ["聚类解释性差"],

    "score": 0.75,
    "confidence": 0.7,
    "priority_rank": 2,

    "reason": "辅助分析"
  }
]
"""


def main():

    # 翻译用真实LLM
    real_llm = LLMClient()

    # 生成goal用mock
    mock_llm = MockLLM()
    
    # RAG
    km = KnowledgeManager(llm_client=real_llm)

    user_query = "我想分析用户流失并制定策略"

    schema_summary = {
        "columns": [
            {"name": "user_id", "type": "int"},
            {"name": "age", "type": "int"},
            {"name": "spending", "type": "float"},
            {"name": "is_churn", "type": "int"}
        ]
    }

    goals = generate_goals(
        user_query=user_query,
        schema_summary=schema_summary,
        llm_client=real_llm,

        #⭐ 如果不想动用llm来生成所有的goal，可以先用mock生成，但是翻译部分建议用真实的llm来做，这样可以测试整个流程，节省token
        #llm_client=mock_llm,

        knowledge_manager=km
    )

    # 🔥 正确输出JSON结构
    print("\n===== 最终Goal结果（JSON结构） =====")

    goals_json = [g.to_dict() for g in goals]

    print(json.dumps(goals_json, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()