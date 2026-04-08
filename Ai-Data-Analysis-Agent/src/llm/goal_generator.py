'''
用户上传数据 → 轻量数据理解 不是EDA → goal_generator（LLM）→ 候选分析目标

输入：
    df + schema summary + user_query

输出：（举例）
    [
  {
    "goal_id": 1,
    "name": "预测用户是否点击",
    "target": "clicked",
    "type": "classification",
    "reason": "user wants CTR prediction"
  },
  {
    "goal_id": 2,
    "name": "分析消费金额影响因素",
    "target": "Total_Spending",
    "type": "regression"
  }
]
'''

import json
import re
from openai import OpenAI

client = OpenAI()

# Prompt构建
def build_prompt(user_query, schema_summary):

    return f"""
You are a senior data scientist.

A user uploaded a dataset and provided a business request.

=====================
[USER REQUEST]
{user_query}

=====================
[DATASET SCHEMA]
{json.dumps(schema_summary, indent=2)}

=====================
[TASK]

1. Understand the user's business request
2. Propose multiple possible analysis objectives
3. Identify suitable target variables:
   - Must exist in dataset OR be derived from existing columns
   - For clustering tasks, target MUST be null
4. Classify problem type:
   - classification
   - regression
   - clustering
   - time_series (if applicable)
5. Suggest suitable model candidates:
   - tree-based models (e.g. xgboost, random_forest)
   - linear models (e.g. linear_regression, logistic_regression)
   - neural networks (e.g. mlp, deep_learning)
   - clustering models (e.g. kmeans)
   - time series models (e.g. arima, prophet)

=====================
[OUTPUT FORMAT - STRICT JSON ONLY]

[
  {{
    "goal_id": 1,
    "goal_name": "...",
    "target": "... OR null",
    "problem_type": "classification / regression / clustering / time_series",
    "model_candidates": [
      {{
        "name": "...",
        "category": "tree / linear / neural_network / clustering / time_series",
        "reason": "..."
      }}
    ],
    "reason": "..."
  }}
]

=====================
[IMPORTANT RULES]

- Output ONLY JSON
- DO NOT include markdown
- DO NOT include explanation outside JSON
- DO NOT add extra fields
- model_candidates MUST be a list
- Use ONLY English model names (e.g. xgboost, random_forest)
- Suggest 3~5 candidate goals
"""


# 调用LLM
def call_llm(prompt):

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": "You are a professional data scientist."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3
    )

    return response.choices[0].message.content


# JSON解析（防崩）
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
        return {
            "error": str(e),
            "raw_text": text
        }



# 后处理校验（
def validate_goals(goals):

    if not isinstance(goals, list):
        return goals

    cleaned = []

    for g in goals:

        # 必要字段保护
        goal = {
            "goal_id": g.get("goal_id"),
            "goal_name": g.get("goal_name"),
            "target": g.get("target"),
            "problem_type": g.get("problem_type"),
            "model_candidates": g.get("model_candidates", []),
            "reason": g.get("reason")
        }

        # clustering 强制 target = None
        if goal["problem_type"] == "clustering":
            goal["target"] = None

        # model_candidates结构保护
        if not isinstance(goal["model_candidates"], list):
            goal["model_candidates"] = []

        cleaned.append(goal)

    return cleaned


# 主函数（外部调用）
def generate_goals(user_query, schema_summary):

    prompt = build_prompt(user_query, schema_summary)

    response_text = call_llm(prompt)

    goals = parse_json(response_text)

    # 🔥 加一层工程保护
    goals = validate_goals(goals)

    return goals