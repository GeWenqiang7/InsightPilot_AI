"""
Knowledge Tool (for KnowledgeManager)
- 基于 state["knowledge_manager"] 或自动创建 KnowledgeManager
- 提供 query_knowledge function-calling 接口
"""

from typing import Dict, Any, Tuple
from src.knowledge.knowledge_manager import KnowledgeManager


def get_tool_definition():
    return {
        "type": "function",
        "function": {
            "name": "query_knowledge",
            "description": "Retrieve domain knowledge chunks from local knowledge base by query.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "top_k": {"type": "integer", "minimum": 1, "maximum": 20}
                },
                "required": ["query"],
                "additionalProperties": False
            }
        }
    }


def run_query(state: Dict[str, Any], query: str, top_k: int = 5):
    km = state.get("knowledge_manager")
    if km is None:
        # 自动挂载（可复用）
        km = KnowledgeManager(llm_client=state.get("llm_client"))
        state["knowledge_manager"] = km

    result = km.get_knowledge(query=query, top_k=top_k)
    state["knowledge_result"] = result
    return result, state


def invoke(params: Dict[str, Any], state: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    query = (params or {}).get("query")
    top_k = (params or {}).get("top_k", 5)

    if not query:
        raise ValueError("query_knowledge requires 'query'.")

    local_state = dict(state)
    result, local_state = run_query(local_state, query=query, top_k=top_k)

    tool_result = {
        "topics": result.get("topics", []),
        "items_count": len(result.get("items", [])),
        "context_text": result.get("context_text", "")
    }
    return tool_result, local_state