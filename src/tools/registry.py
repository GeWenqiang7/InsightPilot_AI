"""
Tool Registry
- 统一注册所有可被 function calling 调用的工具
- 提供 tool definitions 给 LLM
- 提供统一执行入口 execute_tool
- 设计为轻量级、易扩展的工具管理系统
- 每个工具包含 definition_fn 和 invoke_fn
- 未来可扩展权限控制、工具版本管理等功能

"""

from typing import Callable, Dict, Any, Tuple

# 每个工具的规范：
# {
#   "definition": Callable[[], dict],          # 返回 OpenAI tool definition
#   "invoke": Callable[[dict, dict], (dict, dict)]  # (params, state) -> (tool_result, new_state)
# }
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


def get_tool_definitions():
    """
    返回给 OpenAI function calling 的 tools 列表
    """
    tools = []
    for name, spec in TOOL_REGISTRY.items():
        definition = spec["definition"]()
        # 保险检查：function.name 与注册名一致
        fn_name = (
            definition.get("function", {}).get("name")
            if isinstance(definition, dict)
            else None
        )
        if fn_name and fn_name != name:
            # 不强制报错，自动对齐，减少人为错误
            definition["function"]["name"] = name
        tools.append(definition)
    return tools


def execute_tool(name: str, params: Dict[str, Any], state: Dict[str, Any]):
    """
    统一工具执行入口
    """
    if name not in TOOL_REGISTRY:
        raise ValueError(f"Tool '{name}' is not registered.")

    invoke_fn = TOOL_REGISTRY[name]["invoke"]
    tool_result, new_state = invoke_fn(params or {}, state)

    if not isinstance(tool_result, dict):
        tool_result = {"result": tool_result}
    if not isinstance(new_state, dict):
        raise TypeError(f"Tool '{name}' must return new_state as dict.")

    return tool_result, new_state


def list_tools():
    return list(TOOL_REGISTRY.keys())


# =========================
# 默认注册（按需扩展）
# =========================
def register_default_tools():
    """
    在系统启动时调用一次：
    from src.tools.registry import register_default_tools
    register_default_tools()
    """
    # 延迟导入，避免循环依赖
    from src.tools import eda_tool

    # EDA
    register_tool(
        name="run_eda",
        definition_fn=eda_tool.get_tool_definition,
        invoke_fn=eda_tool.invoke,
    )

    # 未来加更多工具时，在这里继续注册：
    # from src.tools import fe_tool
    # register_tool("run_fe", fe_tool.get_tool_definition, fe_tool.invoke)
    #
    # from src.kg import kg_builder
    # register_tool("build_kg", kg_builder.get_tool_definition, kg_builder.invoke)