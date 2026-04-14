'''
输入：
- 用户查询：用户的分析需求描述
- 数据集schema：数据集的结构化描述（字段、类型、示例等）

输出：
- 分析目标列表：每个目标包含目标ID、名称、分析对象（可选）、问题类型、模型候选列表以及选择理由

主要功能：
- 生成分析目标：调用goal_generator模块，根据用户查询和数据集schema生成候选分析目标列表。
- 选择分析目标：根据用户的选择，确定最终的分析目标。
- 更新分析目标：根据用户的反馈或新的查询，重新生成或调整分析目标列表。
'''

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class ModelCandidate:
    name: str
    category: str
    reason: str


@dataclass
class Goal:
    goal_id: int
    goal_name: str
    target: Optional[str]
    problem_type: str
    model_candidates: List[ModelCandidate]
    reason: str

    @staticmethod
    def from_dict(data: dict):
        models = [
            ModelCandidate(**m) for m in data.get("model_candidates", [])
        ]

        return Goal(
            goal_id=data.get("goal_id"),
            goal_name=data.get("goal_name"),
            target=data.get("target"),
            problem_type=data.get("problem_type"),
            model_candidates=models,
            reason=data.get("reason")
        )