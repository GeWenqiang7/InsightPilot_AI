'''
输入：
- 用户查询：用户的分析需求描述
- 数据集schema：数据集的结构化描述，包括字段信息、数据类型等    

输出：
- 分析目标列表：每个目标包含目标ID、名称、分析对象、问题类型、模型候选及理由等信息

主要功能：
1. 构建Prompt：根据用户查询、数据集schema和知识上下文构建详细的prompt，指导LLM生成高质量的分析目标。
2. 解析LLM输出：从LLM的文本输出中提取JSON格式的分析目标列表，增强鲁棒性以适应不同格式的输出。
3. 校验和清洗：对解析出的目标进行校验和清洗，确保每个目标都符合预期的结构和内容要求。
4. 接入RAG：在构建prompt时融合知识管理器提供的相关知识上下文，提升生成目标的质量和相关性。

'''
import json
import re
from typing import List
from src.goal.goal_schema import Goal


# =========================
# Prompt Builder（升级）
# =========================
def build_prompt(user_query, schema_summary, knowledge_context):

    return f"""
You are a senior data scientist.

Your task is to generate high-quality data analysis goals.

========================
[USER REQUEST]
{user_query}

========================
[DATASET SCHEMA]
{json.dumps(schema_summary, indent=2)}

========================
[KNOWLEDGE CONTEXT]
{knowledge_context["context_text"]}

Relevant topics:
{knowledge_context["topics"]}

========================
INSTRUCTIONS:

1. Generate 3-5 analysis goals
2. Each goal must:
   - Be specific and actionable
   - Match dataset schema
   - Use best practices from knowledge context

3. Choose appropriate:
   - problem_type (classification / regression / clustering / time_series)
   - model_candidates (with reasons)

4. If classification:
   - consider imbalance
   - suggest evaluation metrics

5. If regression:
   - suggest feature engineering
   - consider distribution issues

========================
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


# =========================
# JSON解析（增强鲁棒性）
# =========================
def parse_json(text):

    try:
        text = text.strip()

        # 去掉markdown code block
        text = re.sub(r"```json", "", text)
        text = re.sub(r"```", "", text)

        match = re.search(r"\[.*\]", text, re.DOTALL)

        if match:
            return json.loads(match.group())

        return []

    except Exception as e:
        print("⚠️ JSON parse failed:", e)
        return []


# =========================
# 清洗 + 校验
# =========================
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

        # clustering不需要target
        if goal["problem_type"] == "clustering":
            goal["target"] = None

        cleaned.append(goal)

    return cleaned


# =========================
# 核心接口（升级：接入RAG）
# =========================
def generate_goals(
    user_query,
    schema_summary,
    llm_client,
    knowledge_manager
) -> List[Goal]:

    # 🔥 Step 1: 获取知识（RAG）
    knowledge_context = knowledge_manager.get_knowledge(user_query)

    # 🔥 Step 2: 构建prompt（融合知识）
    prompt = build_prompt(
        user_query,
        schema_summary,
        knowledge_context
    )

    # 🔥 Step 3: LLM生成
    response_text = llm_client.generate(prompt)

    # 🔥 Step 4: 解析
    goals_raw = parse_json(response_text)

    # 🔥 Step 5: 校验
    goals_clean = validate_goals(goals_raw)

    # 🔥 Step 6: 转结构化对象
    goals = [Goal.from_dict(g) for g in goals_clean]

    return goals