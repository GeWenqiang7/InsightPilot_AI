'''
总结文件功能：
1. 构建 Prompt（认知层）：设计一个清晰、结构化的 Prompt
2. 调用 LLM（推理层）：让 LLM 扮演数据科学家，输出fe_plan（严格JSON）；AI 在做数据分析决策
3. 解析 JSON（工程层）：提取 JSON，防止格式问题导致崩溃；保证系统稳定
4. 保存结果（数据层）：输出到 output/fe/fe_plan.json
5. 更新 state（系统层）：将 fe_plan 和路径保存到 state，供后续工具使用；实现工具间的状态流转
state["fe_plan"]

后期可以增加：
- Prompt优化：根据反馈调整Prompt，提升输出质量
- 多轮交互：如果输出不完整或不合理，可以设计多轮对话，进一步询问LLM细节
- 结果验证：设计规则或使用模型验证输出的合理性，提升系统鲁棒性
- 版本控制：保存不同版本的FE计划，便于回溯和比较
- 没有 schema 校验，不保证字段完整，
'''

'''
FE TOOL（升级版）

能力：
1. 基于EDA生成特征工程方案
2. 支持 problem_type（任务驱动）
3. 支持 model_candidates（模型驱动）
4. 输出结构化 JSON（可执行）
'''

import os
import json
import re
from openai import OpenAI

client = OpenAI()


# =========================
# Prompt（🔥升级版）
# =========================
def build_prompt(eda, target, problem_type, model_candidates):

    return f"""
You are a senior data scientist and machine learning expert.

========================
[CONTEXT]
========================

Problem Type: {problem_type}
Target variable: {target}

EDA summary:
{json.dumps(eda, indent=2)}

Model Candidates:
{json.dumps(model_candidates, indent=2)}

========================
[TASK REQUIREMENTS]
========================

You must generate a PRACTICAL feature engineering plan.

1. Adapt to problem type:

- classification:
  handle imbalance, encoding, feature selection

- regression:
  handle skewness, scaling, continuous features

- clustering:
  no target, focus on scaling and dimensionality reduction

2. Identify data issues:
   - missing values
   - skewness
   - outliers

3. Propose feature engineering:
   - transformations (log, scaling)
   - encoding
   - feature construction

4. Align with model_candidates:
   - tree models → no strict scaling
   - linear models → scaling required
   - neural networks → normalization

========================
[OUTPUT FORMAT - STRICT JSON ONLY]
========================

{{
  "problem_type": "{problem_type}",

  "data_issues": [
    {{
      "issue": "...",
      "columns": [],
      "severity": "low / medium / high",
      "suggestion": "..."
    }}
  ],

  "feature_engineering": [
    {{
      "column": "...",
      "method": "...",
      "reason": "...",
      "priority": "high / medium / low"
    }}
  ],

  "feature_selection": {{
    "drop": [],
    "keep": [],
    "method": "..."
  }},

  "model_alignment": [
    {{
      "model": "...",
      "strategy": "..."
    }}
  ]
}}

========================
[IMPORTANT RULES]
========================

- Output ONLY valid JSON
- No explanation outside JSON
- No markdown
- Ensure fields are always present
"""


# =========================
# 调用 LLM
# =========================
def call_llm(prompt):

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": "You are a professional data scientist."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.2
    )

    return response.choices[0].message.content


# =========================
# JSON解析（防崩）
# =========================
def parse_response(text):

    try:
        text = text.strip()

        if "```" in text:
            text = re.sub(r"```json", "", text)
            text = re.sub(r"```", "", text)

        match = re.search(r"\{.*\}", text, re.DOTALL)

        if match:
            return json.loads(match.group())

        return {
            "raw_text": text
        }

    except Exception as e:
        return {
            "error": str(e),
            "raw_text": text
        }


# =========================
# FE TOOL 主入口
# =========================
def run(state):

    print("🚀 [FE TOOL] Running...")

    eda = state["eda_for_llm"]
    target = state.get("target")
    problem_type = state.get("problem_type")
    model_candidates = state.get("model_candidates", [])

    base_dir = state.get("output_dir", "output")
    fe_dir = os.path.join(base_dir, "fe")

    os.makedirs(fe_dir, exist_ok=True)

    # =========================
    # 1️⃣ 构建 Prompt
    # =========================
    prompt = build_prompt(
        eda,
        target,
        problem_type,
        model_candidates
    )

    # =========================
    # 2️⃣ 调用 LLM
    # =========================
    response_text = call_llm(prompt)

    # =========================
    # 3️⃣ 解析 JSON
    # =========================
    fe_plan = parse_response(response_text)

    # =========================
    # 4️⃣ 保存结果
    # =========================
    fe_path = os.path.join(fe_dir, "fe_plan.json")

    with open(fe_path, "w") as f:
        json.dump(fe_plan, f, indent=2)

    print(f"✅ FE plan saved to: {fe_path}")

    # =========================
    # 5️⃣ 更新 state
    # =========================
    state["fe_plan"] = fe_plan
    state["fe_path"] = fe_path

    return state