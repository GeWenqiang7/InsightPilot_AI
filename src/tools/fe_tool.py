'''
功能：  
1. 兼容旧逻辑的纯文本生成接口 generate(prompt)，保持与之前版本的兼容性。
2. 新增基于 OpenAI function calling 的工具调用闭环接口 run_with_tools(messages, state, ...)，支持模型调用预定义工具并将结果回填给模型，实现更复杂的交互流程。
在 run_with_tools 中，模型可以选择调用一个或多个工具（如 run_eda），每次调用后工具的结果会以特定格式回传给模型，模型可以基于这些结果继续生成下一步的输出或调用更多工具。
整个过程支持多轮交互，直到模型不再调用工具而直接给出最终文本回答，或者达到最大轮数限制。

升级和维护指南：
- 兼容性：保持 generate 方法不变，确保旧代码继续工作。新功能集中在 run_with_tools 中，旧调用方式不受影响。
- 错误处理：在工具调用过程中增加异常捕获，确保任何工具执行
错误都能被捕获并反馈给模型，而不会中断整个交互流程。
- 扩展性：未来可以在 get_tool_definitions 中动态加载更多工具，并在 execute_tool 中统一管理工具调用逻辑，支持权限控制、工具版本等高级功能。
- 文档和示例：提供详细的文档说明和使用示例，帮助开发者理解如何使用新的工具调用接口，以及如何编写符合规范的工具函数。
'''

import os
import json
import re
from typing import Dict, Any, Tuple

from openai import OpenAI

client = OpenAI()


# =========================
# Function Calling: 工具定义
# =========================
def get_tool_definition():
    return {
        "type": "function",
        "function": {
            "name": "run_fe",
            "description": "Generate a feature engineering plan based on EDA summary, problem type, and model candidates.",
            "parameters": {
                "type": "object",
                "properties": {
                    "target": {"type": ["string", "null"]},
                    "problem_type": {
                        "type": ["string", "null"],
                        "enum": ["classification", "regression", "clustering", None]
                    },
                    "model_candidates": {
                        "type": "array",
                        "items": {"type": "object"}
                    },
                    "output_dir": {"type": "string"}
                },
                "required": [],
                "additionalProperties": False
            }
        }
    }


# =========================
# Prompt
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
{json.dumps(eda, indent=2, ensure_ascii=False)}

Model Candidates:
{json.dumps(model_candidates, indent=2, ensure_ascii=False)}

========================
[TASK REQUIREMENTS]
========================

You must generate a PRACTICAL feature engineering plan.

1. Adapt to problem type:
- classification: handle imbalance, encoding, feature selection
- regression: handle skewness, scaling, continuous features
- clustering: no target, focus on scaling and dimensionality reduction

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
def call_llm(prompt: str) -> str:
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
# JSON 解析
# =========================
def parse_response(text: str) -> Dict[str, Any]:
    try:
        text = text.strip()

        if "```" in text:
            text = re.sub(r"```json", "", text)
            text = re.sub(r"```", "", text)

        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            return json.loads(match.group())

        return {"raw_text": text}

    except Exception as e:
        return {"error": str(e), "raw_text": text}


# =========================
# 主入口（兼容旧调用）
# =========================
def run(state: Dict[str, Any]) -> Dict[str, Any]:
    print("🚀 [FE TOOL] Running...")

    if "eda_for_llm" not in state:
        raise ValueError("Missing 'eda_for_llm' in state. Run EDA first.")

    eda = state["eda_for_llm"]
    target = state.get("target")
    problem_type = state.get("problem_type")
    model_candidates = state.get("model_candidates", [])

    base_dir = state.get("output_dir", "output")
    fe_dir = os.path.join(base_dir, "fe")
    os.makedirs(fe_dir, exist_ok=True)

    # 1) 构建 prompt
    prompt = build_prompt(eda, target, problem_type, model_candidates)

    # 2) 调用 LLM
    response_text = call_llm(prompt)

    # 3) 解析 JSON
    fe_plan = parse_response(response_text)

    # 4) 保存
    fe_path = os.path.join(fe_dir, "fe_plan.json")
    with open(fe_path, "w", encoding="utf-8") as f:
        json.dump(fe_plan, f, indent=2, ensure_ascii=False)

    print(f"✅ FE plan saved to: {fe_path}")

    # 5) 更新 state
    state["fe_plan"] = fe_plan
    state["fe_path"] = fe_path

    return state


# =========================
# Function Calling: 执行入口
# =========================
def invoke(params: Dict[str, Any], state: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    params: function calling 传入参数
    state : 上下文状态
    """
    if params is None:
        params = {}

    local_state = dict(state)

    # 允许参数覆盖 state
    if "target" in params:
        local_state["target"] = params.get("target")
    if "problem_type" in params:
        local_state["problem_type"] = params.get("problem_type")
    if "model_candidates" in params:
        local_state["model_candidates"] = params.get("model_candidates")
    if "output_dir" in params:
        local_state["output_dir"] = params.get("output_dir")

    local_state = run(local_state)

    tool_result = {
        "fe_path": local_state.get("fe_path"),
        "problem_type": local_state.get("fe_plan", {}).get("problem_type"),
        "data_issues_count": len(local_state.get("fe_plan", {}).get("data_issues", [])),
        "feature_engineering_count": len(local_state.get("fe_plan", {}).get("feature_engineering", [])),
        "has_error": "error" in local_state.get("fe_plan", {})
    }

    return tool_result, local_state