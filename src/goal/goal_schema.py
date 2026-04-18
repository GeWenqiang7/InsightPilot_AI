'''
输入：一个包含多个目标的列表，每个目标包含以下字段：
- goal_id: 目标的唯一标识符
- goal_name: 目标的名称
- target: 目标的具体内容或描述
- problem_type: 目标所属的问题类型（如分类、回归、聚类等）
- model_candidates: 一个包含多个模型候选项的列表，每个候选项包含以下字段：
  - name: 模型的名称
    - category: 模型的类别（如树模型、线性模型、神经网络等）
    - reason: 选择该模型的理由
- reason: 选择该目标的理由  

输出：一个包含多个Goal对象的列表，每个Goal对象包含以下属性：
- goal_id: 目标的唯一标识符
- goal_name: 目标的名称
- target: 目标的具体内容或描述
- problem_type: 目标所属的问题类型（如分类、回归、聚类等）
- model_candidates: 一个包含多个模型候选项的列表，每个候选项包含以下字段：
  - name: 模型的名称
    - category: 模型的类别（如树模型、线性模型、神经网络等）
    - reason: 选择该模型的理由
- reason: 选择该目标的理由


示例输入：
[
  {
    "goal_id": 1,
    "goal_name": "预测客户流失",
    "target": "预测哪些客户可能会流失",
    "problem_type": "分类",
    "model_candidates": [
      {
        "name": "随机森林",
        "category": "树模型",
        "reason": "能够处理高维数据且不易过拟合"
      },
      {
        "name": "逻辑回归",
        "category": "线性模型",
        "reason": "模型简单且易于解释"
      }
    ],
    "reason": "客户流失是公司面临的主要问题，预测流失客户可以帮助制定挽留策略"
  }
]
'''

from typing import List, Optional, Dict

class Goal:
    """
    工程级 Goal Schema（支持：
    - ranking
    - RAG增强
    - Agent扩展
    ）
    """

    def __init__(
        self,
        goal_id: int,
        goal_name: str,
        target: Optional[str],
        problem_type: str,

        # 🔥 分析层
        analysis_perspective: Optional[str],
        business_value: Optional[str],

        # 🔥 特征工程建议
        fe_suggestions: Optional[List[Dict]] = None,

        # 🔥 模型建议
        model_candidates: Optional[List[Dict]] = None,

        # 🔥 评估建议
        evaluation_suggestions: Optional[Dict] = None,

        # 🔥 风险
        risks: Optional[List[str]] = None,

        # 🔥 原始reason
        reason: Optional[str] = None,

        # 🔥 Ranking核心（最重要）
        score: float = 0.0,
        priority: int = 0,
        confidence: float = 0.0
    ):
        self.goal_id = goal_id
        self.goal_name = goal_name
        self.target = target
        self.problem_type = problem_type

        self.analysis_perspective = analysis_perspective
        self.business_value = business_value

        self.fe_suggestions = fe_suggestions or []
        self.model_candidates = model_candidates or []
        self.evaluation_suggestions = evaluation_suggestions or {}

        self.risks = risks or []
        self.reason = reason

        self.score = score
        self.priority = priority
        self.confidence = confidence

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            goal_id=data.get("goal_id"),
            goal_name=data.get("goal_name"),
            target=data.get("target"),
            problem_type=data.get("problem_type"),

            analysis_perspective=data.get("analysis_perspective"),
            business_value=data.get("business_value"),

            fe_suggestions=data.get("fe_suggestions", []),
            model_candidates=data.get("model_candidates", []),
            evaluation_suggestions=data.get("evaluation_suggestions", {}),

            risks=data.get("risks", []),
            reason=data.get("reason"),

            #  兼容priority_rank
            score=data.get("score", 0.0),
            priority=data.get("priority", data.get("priority_rank", 0)),
            confidence=data.get("confidence", 0.0)
        )

    def to_dict(self):
        return {
            "goal_id": self.goal_id,
            "goal_name": self.goal_name,
            "target": self.target,
            "problem_type": self.problem_type,

            "analysis_perspective": self.analysis_perspective,
            "business_value": self.business_value,

            "fe_suggestions": self.fe_suggestions,
            "model_candidates": self.model_candidates,
            "evaluation_suggestions": self.evaluation_suggestions,

            "risks": self.risks,
            "reason": self.reason,

            "score": self.score,
            "priority": self.priority,
            "confidence": self.confidence
        }

    def __repr__(self):
        return f"<Goal {self.goal_id}: {self.goal_name} (score={self.score}, priority={self.priority})>"