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

import os
import json
from openai import OpenAI
import re
import json

client = OpenAI()

# 设计Prompt
def build_prompt(eda, target):

    return f"""
You are a senior data scientist and machine learning expert.

Your goal is to analyze the dataset and generate a GENERALIZED and ROBUST data science plan.

========================
[CONTEXT]
========================

Target variable: {target}

EDA summary:
{json.dumps(eda, indent=2)}

========================
[TASK REQUIREMENTS]
========================

You must:

1. Understand the problem type:
   - classification (e.g. CTR prediction)
   - regression (e.g. spending prediction)
   - clustering (user segmentation)
   - ranking / recommendation

2. Identify data issues:
   - missing values
   - skewness
   - outliers
   - high cardinality categorical features
   - feature imbalance
   - potential leakage

3. Propose feature engineering strategies:
   - transformations (log, scaling, normalization)
   - encoding (one-hot, target encoding, embedding)
   - feature construction
   - behavioral features (if applicable)
   - temporal features (if applicable)

4. Propose feature interactions:
   - cross features
   - aggregations
   - user-item interactions (if applicable)

5. Propose feature selection:
   - drop useless features
   - keep important features
   - reduce dimensionality if needed

6. Suggest suitable model types (for future use):
   - tree-based models
   - linear models
   - deep learning
   - recommendation models

7. Ensure robustness:
   - suggestions must generalize to different datasets
   - avoid overfitting-specific tricks
   - prefer scalable methods

========================
[OUTPUT FORMAT - STRICT JSON ONLY]
========================

{{
  "problem_type": "...",

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

  "feature_interactions": [
    {{
      "columns": ["...", "..."],
      "method": "...",
      "reason": "..."
    }}
  ],

  "feature_selection": {{
    "drop": [],
    "keep": [],
    "method": "optional explanation"
  }},

  "model_suggestions": [
    {{
      "model": "...",
      "reason": "...",
      "suitable_for": "..."
    }}
  ]
}}

========================
[IMPORTANT RULES]
========================

- Output ONLY valid JSON
- No explanation outside JSON
- No markdown
- No ```json
- Ensure fields are always present
- Be consistent and structured
"""


# 调用 LLM
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


# 解析 JSON（防崩）
def parse_response(text):

    try:
        # 去掉 ```json ``` 包裹
        text = text.strip()

        if "```" in text:
            text = re.sub(r"```json", "", text)
            text = re.sub(r"```", "", text)

        # 提取第一个 JSON
        match = re.search(r"\{.*\}", text, re.DOTALL)

        if match:
            json_str = match.group()
            return json.loads(json_str)

        # fallback
        return {
            "raw_text": text,
            "features": []
        }

    except Exception as e:
        return {
            "error": str(e),
            "raw_text": text,
            "features": []
        }


# FE TOOL
def run(state):

    print("🚀 [FE TOOL] Running...")

    eda = state["eda_for_llm"]
    target = state["target"]

    base_dir = state.get("output_dir", "output")
    fe_dir = os.path.join(base_dir, "fe")

    os.makedirs(fe_dir, exist_ok=True)

  
    # 1. 构建 Prompt
    prompt = build_prompt(eda, target)

    # 2. 调用 LLM
    response_text = call_llm(prompt)

    # 3. 解析 JSON
    fe_plan = parse_response(response_text)


    # 4. 保存
    fe_path = os.path.join(fe_dir, "fe_plan.json")

    with open(fe_path, "w") as f:
        json.dump(fe_plan, f, indent=2)

    print(f"✅ FE plan saved to: {fe_path}")


    # 5. 更新 state
    state["fe_plan"] = fe_plan
    state["fe_path"] = fe_path

    return state