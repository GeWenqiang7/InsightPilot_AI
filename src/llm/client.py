'''
LLMClient 模块负责与 OpenAI API 进行交互，提供两种主要功能：

1. 兼容旧逻辑的纯文本生成接口 generate(prompt)，保持与之前版本的兼容性。
2. 新增基于 OpenAI function calling 的工具调用闭环接口 run_with_tools(messages, state, ...)，支持模型调用预定义工具并将结果回填给模型，实现更复杂的交互流程。
在 run_with_tools 中，模型可以选择调用一个或多个工具（如 run_eda），每次调用后工具的结果会以特定格式回传给模型，模型可以基于这些结果继续生成下一步的输出或调用更多工具。
整个过程支持多轮交互，直到模型不再调用工具而直接给出最终文本回答，或者达到最大轮数限制。        

升级和维护指南：
- 兼容性：保持 generate 方法不变，确保旧代码继续工作。新功能集中在 run_with_tools 中，旧调用方式不受影响。
- 错误处理：在工具调用过程中增加异常捕获，确保任何工具执行错误都能被捕获并反馈给模型，而不会中断整个交互流程。
- 扩展性：未来可以在 get_tool_definitions 中动态加载更多工具，并在 execute_tool 中统一管理工具调用逻辑，支持权限控制、工具版本等高级功能。
- 文档和示例：提供详细的文档说明和使用示例，帮助开发者理解如何使用新的工具调用接口，以及如何编写符合规范的工具函数。

'''

import json
from typing import List, Dict, Any, Optional

from openai import OpenAI
from src.tools.registry import get_tool_definitions, execute_tool


class LLMClient:
    def __init__(self, model: str = "gpt-4.1", temperature: float = 0.2):
        self.client = OpenAI()
        self.model = model
        self.temperature = temperature

    # =========================
    # 兼容旧逻辑：纯文本生成
    # =========================
    def generate(self, prompt: str) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=self.temperature
        )
        return response.choices[0].message.content

    # =========================
    # 新增：function calling 闭环
    # =========================
    def run_with_tools(
        self,
        messages: List[Dict[str, Any]],
        state: Dict[str, Any],
        max_rounds: int = 8,
        tools: Optional[List[Dict[str, Any]]] = None,
        force_tool_choice: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        messages: 标准 chat messages
        state: 运行态（至少可放 df / target / problem_type 等）
        max_rounds: 最多工具-模型循环次数
        tools: 可选，若不传则自动从 registry 获取
        force_tool_choice:
            - None: 模型自行决定是否调用工具
            - "required": 强制至少调用一个工具
            - 具体工具名，如 "run_eda"
        """
        if tools is None:
            tools = get_tool_definitions()

        working_messages = list(messages)
        working_state = dict(state)

        for _ in range(max_rounds):
            req = {
                "model": self.model,
                "messages": working_messages,
                "temperature": self.temperature,
            }

            # 有工具才传 tools / tool_choice
            if tools:
                req["tools"] = tools

                if force_tool_choice == "required":
                    req["tool_choice"] = "required"
                elif isinstance(force_tool_choice, str) and force_tool_choice not in (None, "", "required"):
                    req["tool_choice"] = {
                        "type": "function",
                        "function": {"name": force_tool_choice}
                    }

            response = self.client.chat.completions.create(**req)
            msg = response.choices[0].message

            # 先把 assistant 消息写入上下文（包含 tool_calls）
            assistant_payload = {
                "role": "assistant",
                "content": msg.content or ""
            }

            # 新 SDK 对象可能有 tool_calls 属性
            tool_calls = getattr(msg, "tool_calls", None)
            if tool_calls:
                assistant_payload["tool_calls"] = [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments
                        }
                    }
                    for tc in tool_calls
                ]

            working_messages.append(assistant_payload)

            # 没有 tool_calls，说明是最终文本回答
            if not tool_calls:
                return {
                    "final_text": msg.content or "",
                    "messages": working_messages,
                    "state": working_state
                }

            # 有 tool_calls -> 逐个执行
            for tc in tool_calls:
                tool_name = tc.function.name
                raw_args = tc.function.arguments or "{}"

                # 解析参数
                try:
                    params = json.loads(raw_args) if isinstance(raw_args, str) else (raw_args or {})
                except Exception as e:
                    params = {}
                    tool_result = {
                        "error": f"Invalid JSON arguments for tool '{tool_name}': {str(e)}",
                        "raw_arguments": raw_args
                    }
                    # 把错误也回喂给模型
                    working_messages.append({
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "name": tool_name,
                        "content": json.dumps(tool_result, ensure_ascii=False)
                    })
                    continue

                # 执行工具
                try:
                    tool_result, working_state = execute_tool(tool_name, params, working_state)
                except Exception as e:
                    tool_result = {
                        "error": f"Tool execution failed: {str(e)}",
                        "tool_name": tool_name,
                        "params": params
                    }

                # 工具结果回填给模型
                working_messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "name": tool_name,
                    "content": json.dumps(tool_result, ensure_ascii=False)
                })

        # 超过 max_rounds 仍未结束，返回兜底
        return {
            "final_text": "Tool-calling loop reached max_rounds without a final answer.",
            "messages": working_messages,
            "state": working_state
        }