import csv
import os
from typing import Any, Dict, List, Tuple


def _infer_type(values: List[str]) -> str:
    non_empty = [v for v in values if v not in ("", None)]
    if not non_empty:
        return "string"

    def _is_int(x: str) -> bool:
        try:
            int(x)
            return True
        except ValueError:
            return False

    def _is_float(x: str) -> bool:
        try:
            float(x)
            return True
        except ValueError:
            return False

    if all(_is_int(v) for v in non_empty[:30]):
        return "int"
    if all(_is_float(v) for v in non_empty[:30]):
        return "float"
    return "string"


def load_csv_schema(data_path: str, sample_size: int = 200) -> Tuple[List[Dict[str, str]], int]:
    if not data_path:
        raise ValueError("data_path is required")
    if not os.path.exists(data_path):
        raise FileNotFoundError("Data file not found: {0}".format(data_path))
    if not data_path.lower().endswith(".csv"):
        raise ValueError("Only CSV is supported in demo API.")

    with open(data_path, "r", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        fieldnames = reader.fieldnames or []
        samples: Dict[str, List[str]] = {name: [] for name in fieldnames}
        row_count = 0
        for row in reader:
            row_count += 1
            if row_count <= sample_size:
                for name in fieldnames:
                    samples[name].append(row.get(name, ""))

    columns = [{"name": name, "type": _infer_type(samples.get(name, []))} for name in fieldnames]
    return columns, row_count


class MockInteractiveLLM:
    def generate(self, prompt: str) -> str:
        low = prompt.lower()
        if "new:" in low or "new requirement" in low or "控制误报" in prompt:
            return """
[
  {
    "goal_id": 2,
    "goal_name": "控制误报并提升召回",
    "target": "label",
    "problem_type": "classification",
    "analysis_perspective": "风险-收益平衡",
    "business_value": "高",
    "model_candidates": [
      {"name":"XGBoost","category":"tree","reason":"非线性与鲁棒性较强"},
      {"name":"LogisticRegression","category":"linear","reason":"阈值与解释性好"}
    ],
    "evaluation_suggestions": {"primary_metric":"recall","secondary_metrics":["precision","f1"]},
    "risks": ["阈值敏感", "数据漂移"],
    "score": 0.94,
    "confidence": 0.87,
    "priority_rank": 1,
    "reason": "满足你最新的误报约束与召回诉求"
  }
]
"""
        return """
[
  {
    "goal_id": 1,
    "goal_name": "预测用户流失概率",
    "target": "label",
    "problem_type": "classification",
    "analysis_perspective": "用户留存",
    "business_value": "高",
    "model_candidates": [
      {"name":"LogisticRegression","category":"linear","reason":"可解释、上线快"},
      {"name":"RandomForest","category":"tree","reason":"鲁棒性较好"}
    ],
    "evaluation_suggestions": {"primary_metric":"auc","secondary_metrics":["f1","recall"]},
    "risks": ["类别不平衡"],
    "score": 0.90,
    "confidence": 0.83,
    "priority_rank": 1,
    "reason": "可直接支持留存策略投放"
  }
]
"""


def build_kg_context_from_query(
    query: str,
    knowledge_manager: Any,
    top_k: int = 5,
) -> Dict[str, Any]:
    """
    轻量 KG 上下文构建：
    - 基于 RAG 检索结果生成 query-topic 图结构
    - 用于 goal 生成 prompt 的结构化补充
    """
    knowledge_context = knowledge_manager.get_knowledge(query, top_k=top_k)
    evidence_items = knowledge_context.get("evidence_items", [])
    topics = knowledge_context.get("topics", [])

    nodes = [{"id": "USER_QUERY", "type": "query"}]
    edges = []
    for item in evidence_items:
        topic = item.get("topic")
        if not topic:
            continue
        nodes.append({"id": topic, "type": "topic"})
        edges.append(
            {
                "source": "USER_QUERY",
                "target": topic,
                "relation": "supported_by_retrieval",
                "weight": item.get("score", 0.0),
                "chunk_id": item.get("chunk_id"),
            }
        )

    # 去重
    seen = set()
    dedup_nodes = []
    for n in nodes:
        node_id = n["id"]
        if node_id in seen:
            continue
        seen.add(node_id)
        dedup_nodes.append(n)

    return {
        "graph": {"nodes": dedup_nodes, "edges": edges},
        "topics": topics,
        "retrieval_confidence": knowledge_context.get("retrieval_confidence", 0.0),
    }
