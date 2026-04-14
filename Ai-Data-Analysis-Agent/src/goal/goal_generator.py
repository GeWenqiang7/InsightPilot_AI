'''
输入：
- 用户查询：用户的分析需求描述
- 数据集schema：数据集的结构化描述（字段、类型、示例等）    

输出：
- 分析目标列表：每个目标包含目标ID、名称、分析对象（可选）、问题类型、模型候选列表以及选择理由

主要功能：
- 构建提示语：根据用户查询和数据集schema构建适合LLM的提示语，明确要求输出格式为严格的JSON列表。
- 解析LLM输出：从LLM的响应中提取JSON内容，并转换为结构化的分析目标列表。
- 验证和清洗：对生成的分析目标进行验证和清洗，确保每个目标包含必要的信息，并根据问题类型调整分析对象的设置。
- 生成分析目标：外部调用接口，接受用户查询和数据集schema，并通过注入的LLM客户端生成分析目标列表。
'''

import json
import re
from typing import List
from src.goal.goal_schema import Goal


def build_prompt(user_query, schema_summary):

    return f"""
You are a senior data scientist.

[USER REQUEST]
{user_query}

[DATASET SCHEMA]
{json.dumps(schema_summary, indent=2)}

Generate 3-5 analysis goals.

OUTPUT STRICT JSON LIST:
[
  {{
    "goal_id": 1,
    "goal_name": "...",
    "target": "...",
    "problem_type": "...",
    "model_candidates": [
      {{
        "name": "...",
        "category": "...",
        "reason": "..."
      }}
    ],
    "reason": "..."
  }}
]
"""


def parse_json(text):

    try:
        text = text.strip()

        if "```" in text:
            text = re.sub(r"```json", "", text)
            text = re.sub(r"```", "", text)

        match = re.search(r"\[.*\]", text, re.DOTALL)

        if match:
            return json.loads(match.group())

        return []

    except Exception as e:
        return []


def validate_goals(goals):

    cleaned = []

    for g in goals:

        goal = {
            "goal_id": g.get("goal_id"),
            "goal_name": g.get("goal_name"),
            "target": g.get("target"),
            "problem_type": g.get("problem_type"),
            "model_candidates": g.get("model_candidates", []),
            "reason": g.get("reason")
        }

        if goal["problem_type"] == "clustering":
            goal["target"] = None

        cleaned.append(goal)

    return cleaned


# 外部调用（注入llm_client）
def generate_goals(user_query, schema_summary, llm_client) -> List[Goal]:

    prompt = build_prompt(user_query, schema_summary)

    response_text = llm_client.generate(prompt)

    goals_raw = parse_json(response_text)

    goals_clean = validate_goals(goals_raw)

    # 转换为结构化对象
    goals = [Goal.from_dict(g) for g in goals_clean]

    return goals