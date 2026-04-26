"""
Goal Generation Demo API (FastAPI)

定位：
- 给当前分析系统提供一个轻量展示层（可视化交互）
- 不侵入核心 pipeline，只复用 src/goal + src/knowledge 现有能力
"""

import os
import uuid
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel

from src.goal.goal_manager import (
    display_goals,
    handle_goal_generation,
    init_goal_state,
    regenerate_goals,
    select_goal,
)
from src.knowledge.knowledge_manager import KnowledgeManager
from app.goal_ui_utils import (
    MockInteractiveLLM,
    build_kg_context_from_query,
    load_csv_schema,
)


@dataclass
class SessionRuntime:
    state: Dict[str, Any]
    llm_client: Any


class CreateSessionRequest(BaseModel):
    data_path: str
    user_query: str
    use_real_llm: bool = True


class RefineRequest(BaseModel):
    new_query: str


class SelectGoalRequest(BaseModel):
    goal_id: int


app = FastAPI(title="InsightPilot Goal Demo API", version="0.1.0")
SESSION_STORE: Dict[str, SessionRuntime] = {}


def _resolve_llm(use_real_llm: bool):
    if not use_real_llm:
        return MockInteractiveLLM()
    try:
        from src.llm.client import LLMClient

        return LLMClient()
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail="failed to init real LLM client. Check OPENAI_API_KEY and openai package. error={0}".format(str(exc)),
        )


def _session_or_404(session_id: str) -> SessionRuntime:
    runtime = SESSION_STORE.get(session_id)
    if runtime is None:
        raise HTTPException(status_code=404, detail="session not found")
    return runtime


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.get("/", response_class=HTMLResponse)
def index() -> Any:
    html_path = os.path.join(os.path.dirname(__file__), "static", "goal_demo.html")
    if not os.path.exists(html_path):
        raise HTTPException(status_code=404, detail="demo html not found")
    return FileResponse(html_path)


@app.post("/sessions")
def create_session(req: CreateSessionRequest) -> Dict[str, Any]:
    columns, rows = load_csv_schema(req.data_path)
    schema_summary = {"rows": rows, "columns": columns}

    llm_client = _resolve_llm(req.use_real_llm)
    km = KnowledgeManager(llm_client=None)
    state = init_goal_state(df=None, user_query=req.user_query, knowledge_manager=km)
    state["schema"] = schema_summary
    state["data_path"] = req.data_path
    state["rag_context"] = km.get_knowledge(req.user_query, top_k=5)
    state["kg_context"] = build_kg_context_from_query(req.user_query, km, top_k=5)

    session_id = uuid.uuid4().hex
    SESSION_STORE[session_id] = SessionRuntime(state=state, llm_client=llm_client)

    return {
        "session_id": session_id,
        "rows": rows,
        "columns": columns,
        "rag_context": state["rag_context"],
        "kg_context": state["kg_context"],
        "message": "session created",
    }


@app.post("/sessions/{session_id}/generate")
def generate_goals(session_id: str) -> Dict[str, Any]:
    runtime = _session_or_404(session_id)
    full_query = "\n".join([item.get("content", "") for item in runtime.state.get("conversation_history", [])]).strip()
    km = runtime.state.get("knowledge_manager")
    if km and full_query:
        runtime.state["rag_context"] = km.get_knowledge(full_query, top_k=5)
        runtime.state["kg_context"] = build_kg_context_from_query(full_query, km, top_k=5)
    runtime.state = handle_goal_generation(runtime.state, runtime.llm_client)
    goals = display_goals(runtime.state)
    return {
        "session_id": session_id,
        "goals": goals,
        "rag_context": runtime.state.get("rag_context", {}),
        "kg_context": runtime.state.get("kg_context", {}),
    }


@app.post("/sessions/{session_id}/refine")
def refine_goals(session_id: str, req: RefineRequest) -> Dict[str, Any]:
    runtime = _session_or_404(session_id)
    runtime.state = regenerate_goals(runtime.state, req.new_query, runtime.llm_client)
    full_query = "\n".join([item.get("content", "") for item in runtime.state.get("conversation_history", [])]).strip()
    km = runtime.state.get("knowledge_manager")
    if km and full_query:
        runtime.state["rag_context"] = km.get_knowledge(full_query, top_k=5)
        runtime.state["kg_context"] = build_kg_context_from_query(full_query, km, top_k=5)
    goals = display_goals(runtime.state)
    return {
        "session_id": session_id,
        "goals": goals,
        "rag_context": runtime.state.get("rag_context", {}),
        "kg_context": runtime.state.get("kg_context", {}),
    }


@app.post("/sessions/{session_id}/select")
def select_goal_api(session_id: str, req: SelectGoalRequest) -> Dict[str, Any]:
    runtime = _session_or_404(session_id)
    runtime.state = select_goal(runtime.state, req.goal_id)
    selected = runtime.state["selected_goal"].to_dict()
    return {"session_id": session_id, "selected_goal": selected}


@app.get("/sessions/{session_id}")
def get_session_state(session_id: str) -> Dict[str, Any]:
    runtime = _session_or_404(session_id)
    selected = runtime.state.get("selected_goal")
    return {
        "session_id": session_id,
        "data_path": runtime.state.get("data_path"),
        "conversation_history": runtime.state.get("conversation_history", []),
        "rag_context": runtime.state.get("rag_context", {}),
        "kg_context": runtime.state.get("kg_context", {}),
        "candidate_goals": [g.to_dict() for g in runtime.state.get("candidate_goals", [])],
        "selected_goal": selected.to_dict() if selected else None,
    }
