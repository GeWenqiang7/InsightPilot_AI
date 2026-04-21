"""
Tool Registry是一个集中管理系统，用于注册、查询和执行各种工具（如EDA、FE、KG构建等）。它提供了统一的接口，使得LLM能够调用这些工具来完成特定任务。

核心功能：
1. 注册工具：通过register_tool函数注册工具，指定工具名称、定义函数和执行函数。
2. 查询工具：提供get_tool_definitions函数，返回所有注册工具的定义，供OpenAI function calling使用。
3. 执行工具：提供execute_tool函数，统一执行指定工具，并处理输入参数和运行态。
4. 默认工具注册：register_default_tools函数预注册了一些常用工具，如EDA、FE、KG构建等，方便快速使用。

升级和维护指南：    
- 兼容性：保持接口稳定，确保已注册工具的调用方式不变。新增工具时只需调用register_tool，无需修改现有代码。
- 错误处理：在execute_tool中增加异常捕获，确保工具执行错误能被捕获并反馈给模型，而不会中断整个交互流程。
- 扩展性：未来可以在get_tool_definitions中动态加载更多工具，并在execute_tool中统一管理工具调用逻辑，支持权限控制、工具版本等高级功能。
- 文档和示例：提供详细的文档说明和使用示例，帮助开发者理解如何使用工具注册和调用接口，以及如何编写符合规范的工具函数。

"""

from typing import Callable, Dict, Any, Tuple

TOOL_REGISTRY: Dict[str, Dict[str, Callable]] = {}


def register_tool(
    name: str,
    definition_fn: Callable[[], Dict[str, Any]],
    invoke_fn: Callable[[Dict[str, Any], Dict[str, Any]], Tuple[Dict[str, Any], Dict[str, Any]]],
):
    if not name:
        raise ValueError("Tool name cannot be empty.")
    if not callable(definition_fn):
        raise TypeError(f"definition_fn for tool '{name}' must be callable.")
    if not callable(invoke_fn):
        raise TypeError(f"invoke_fn for tool '{name}' must be callable.")

    TOOL_REGISTRY[name] = {
        "definition": definition_fn,
        "invoke": invoke_fn,
    }


def unregister_tool(name: str):
    TOOL_REGISTRY.pop(name, None)


def clear_tools():
    TOOL_REGISTRY.clear()


def list_tools():
    return list(TOOL_REGISTRY.keys())


def get_tool_definitions():
    """
    返回给 OpenAI function calling 的 tools 列表
    """
    tools = []
    for name, spec in TOOL_REGISTRY.items():
        definition = spec["definition"]()

        # 保险检查：function.name 与注册名一致
        if isinstance(definition, dict) and "function" in definition:
            fn_name = definition["function"].get("name")
            if fn_name and fn_name != name:
                definition["function"]["name"] = name

        tools.append(definition)

    return tools


def execute_tool(name: str, params: Dict[str, Any], state: Dict[str, Any]):
    """
    统一工具执行入口
    """
    if name not in TOOL_REGISTRY:
        raise ValueError(f"Tool '{name}' is not registered. Current tools: {list_tools()}")

    invoke_fn = TOOL_REGISTRY[name]["invoke"]
    tool_result, new_state = invoke_fn(params or {}, state)

    if not isinstance(tool_result, dict):
        tool_result = {"result": tool_result}
    if not isinstance(new_state, dict):
        raise TypeError(f"Tool '{name}' must return new_state as dict.")

    return tool_result, new_state


# =========================
# 默认注册 
# =========================
def register_default_tools():
    """
    启动时调用一次：
    from src.tools.registry import register_default_tools
    register_default_tools()
    """
    # 延迟导入，避免循环依赖
    from src.tools import eda_tool
    from src.tools import fe_tool
    from src.tools import model_tool
    from src.tools import advisor_tool
    from src.tools import evaluate_tool
    from src.tools import report_tool
    from src.kg import kg_builder
    from src.kg import kg_agent

    # EDA
    register_tool(
        name="run_eda",
        definition_fn=eda_tool.get_tool_definition,
        invoke_fn=eda_tool.invoke,
    )

    # FE
    register_tool(
        name="run_fe",
        definition_fn=fe_tool.get_tool_definition,
        invoke_fn=fe_tool.invoke,
    )


    # Model
    register_tool(
        name="run_model",
        definition_fn=model_tool.get_tool_definition,
        invoke_fn=model_tool.invoke,
    )

    # Advisor
    register_tool(
        name="run_advisor",
        definition_fn=advisor_tool.get_tool_definition,
        invoke_fn=advisor_tool.invoke,
    )

    # Evaluate
    register_tool(
        name="run_evaluate",
        definition_fn=evaluate_tool.get_tool_definition,
        invoke_fn=evaluate_tool.invoke,
    )

    # Report
    register_tool(
        name="run_report",
        definition_fn=report_tool.get_tool_definition,
        invoke_fn=report_tool.invoke,
    )

    # KG build
    register_tool(
        name="build_kg",
        definition_fn=kg_builder.get_tool_definition,
        invoke_fn=kg_builder.invoke,
    )

    # KG reasoning
    register_tool(
        name="reason_with_kg",
        definition_fn=kg_agent.get_tool_definition,
        invoke_fn=kg_agent.invoke,
    )