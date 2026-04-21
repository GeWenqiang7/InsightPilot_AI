'''
输入：
-  用户查询：用户的分析需求或问题描述。
-  数据集schema：数据集的结构信息，包括字段名称、类型和描述。

输出：
-  分析目标列表：每个目标包含以下信息：
   - 目标ID：唯一标识   

主要功能：
1. RAG知识增强：从知识库中检索与用户查询相关的背景知识，提供给LLM作为生成参考。
2. 目标生成：基于用户查询、数据集schema和知识上下文，生成多个分析目标。
3. 目标评估与排序：对生成的目标进行评估，打分并排序，优先展示高价值和高可行性的目标。   

样例输出：
[
  {     
    "goal_id": 1,
    "goal_name": "预测客户流失",
    "target": "预测哪些客户可能会流失",
    "problem_type": "分类",

    "analysis_perspective": "客户行为分析",
    "business_value": "高",

    "model_candidates": [
      {
        "name": "随机森林",
        "category": "树模型",
        "reason": "能够处理高维数据且不易过拟合",
        "strength": "...",
        "risk": "..."
      }
    ],

    "evaluation_suggestions": {
      "primary_metric": "...",
      "secondary_metrics": ["..."],
      "cv_strategy": "..."
    },

    "risks": ["..."],

    "score": 0.92,
    "confidence": 0.88,
    "priority_rank": 1,

    "reason": "客户流失是公司面临的主要问题，预测流失客户可以帮助制定挽留策略"
  }

'''
import json
import re
from typing import List
from src.goal.goal_schema import Goal


# JSON解析
def parse_json(text):

    try:
        text = text.strip()

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

            "analysis_perspective": g.get("analysis_perspective"),
            "business_value": g.get("business_value"),

            "fe_suggestions": g.get("fe_suggestions", []),
            "model_candidates": g.get("model_candidates", []),
            "evaluation_suggestions": g.get("evaluation_suggestions", {}),

            "risks": g.get("risks", []),
            "reason": g.get("reason"),

            "score": g.get("score", 0.0),
            "priority_rank": g.get("priority_rank", 0),
            "confidence": g.get("confidence", 0.0),
            "evidence_topics": g.get("evidence_topics", []),
            "evidence": g.get("evidence", []),
            "uncertainty_notes": g.get("uncertainty_notes", []),
            "retrieval_confidence": g.get("retrieval_confidence", 0.0),
        }

        if goal["problem_type"] == "clustering":
            goal["target"] = None

        cleaned.append(goal)

    return cleaned


# =========================
# 核心接口（RAG + Ranking）
# =========================
def generate_goals(
    user_query,
    schema_summary,
    llm_client,
    knowledge_manager
) -> List[Goal]:

    # 🔥 Step 1: RAG知识
    knowledge_context = knowledge_manager.get_knowledge(user_query)

    # 🔥 Step 2: Prompt（直接写在这里）
    prompt = f"""
You are a senior data scientist.

Your job is to generate AND RANK data analysis goals grounded in retrieved evidence.

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

Retrieved evidence items:
{json.dumps(knowledge_context.get("evidence_items", []), ensure_ascii=False, indent=2)}

========================
TASK:

1. Generate 3-5 analysis goals
2. Each goal must:
   - Define problem_type
   - Suggest models
   - Provide reasoning
   - Include evidence_topics based on retrieved topics
   - Include uncertainty_notes when retrieval evidence is weak

3. Evaluate each goal based on:
   - Business value
   - Feasibility
   - Impact

4. Assign:
   - score (0.0 - 1.0)
   - confidence (0.0 - 1.0)
   - priority_rank (1 = highest)

5. Sort by score DESC

========================
OUTPUT STRICT JSON:
[
  {{
    "goal_id": 1,
    "goal_name": "...",
    "target": "...",
    "problem_type": "...",

    "analysis_perspective": "...",
    "business_value": "...",

    "model_candidates": [
      {{
        "name": "...",
        "category": "...",
        "reason": "...",
        "strength": "...",
        "risk": "..."
      }}
    ],

    "evaluation_suggestions": {{
      "primary_metric": "...",
      "secondary_metrics": ["..."],
      "cv_strategy": "..."
    }},

    "risks": ["..."],

    "score": 0.92,
    "confidence": 0.88,
    "priority_rank": 1,
    "evidence_topics": ["..."],
    "evidence": [
      {{
        "topic": "...",
        "chunk_id": "...",
        "snippet": "..."
      }}
    ],
    "uncertainty_notes": ["..."],
    "retrieval_confidence": 0.75,

    "reason": "..."
  }}
]
"""

    # 🔥 Step 3: LLM生成
    response_text = llm_client.generate(prompt)

    # 🔥 Step 4: 解析
    goals_raw = parse_json(response_text)

    # 🔥 Step 5: 校验
    goals_clean = validate_goals(goals_raw)
    fallback_evidence = knowledge_context.get("evidence_items", [])[:3]
    fallback_topics = knowledge_context.get("topics", [])
    retrieval_confidence = knowledge_context.get("retrieval_confidence", 0.0)
    for goal in goals_clean:
        if not goal.get("evidence_topics"):
            goal["evidence_topics"] = fallback_topics[:3]
        if not goal.get("evidence"):
            goal["evidence"] = fallback_evidence
        if goal.get("retrieval_confidence", 0.0) == 0.0:
            goal["retrieval_confidence"] = retrieval_confidence
        if retrieval_confidence < 0.6 and not goal.get("uncertainty_notes"):
            goal["uncertainty_notes"] = ["knowledge retrieval confidence is limited; validate with domain expert before execution"]

    # 🔥 Step 6: 转对象
    goals = [Goal.from_dict(g) for g in goals_clean]

    # 🔥 Step 7: 排序（关键）
    goals = sorted(goals, key=lambda x: x.score, reverse=True)

    return goals
