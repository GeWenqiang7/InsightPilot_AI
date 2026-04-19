"""
KG Builder是一个专门设计用于从EDA结果中抽取结构化关系并构建知识图谱的工具，旨在为数据科学家和机器学习工程师提供更深入的数据理解和智能化的特征工程支持。
它不仅从EDA结果中抽取KG候选关系，还基于这些关系构建轻量级的知识图谱，并提供推理功能，帮助用户识别关键特征、特征聚类、推理路径等信息，提升数据分析的智能化水平。

核心功能：
1. 从EDA结果中抽取KG候选关系，包含特征间的相关性、重要特征等信息
2. 构建KG结构（节点+边），支持简单的查询和可视化接口
3. 提供统一的run函数，供Agent调用，输出KG结构   
4. 基于KG进行推理，输出关键特征、特征聚类、推理路径等信息
5. 兼容旧调用方式，同时支持OpenAI function-calling接口

输入：
- state["kg_candidates"]：从EDA结果中抽取的KG候选关系，包含特征间的相关性、重要特征等信息
输出：  
- state["knowledge_graph"]：构建的KG结构，包含节点和边
- state["kg_result"]：基于KG的推理结果，包含关键特征、特征聚类、推理路径等信息

"""

from typing import Dict, Any, Tuple


class KnowledgeGraph:
    """轻量级知识图谱结构"""

    def __init__(self):
        self.nodes = set()
        self.edges = []

    def add_node(self, node: str):
        self.nodes.add(node)

    def add_edge(self, source: str, target: str, relation_type: str, weight: float = 1.0):
        self.edges.append({
            "source": source,
            "target": target,
            "type": relation_type,
            "weight": weight
        })
        self.add_node(source)
        self.add_node(target)

    def to_dict(self):
        return {
            "nodes": list(self.nodes),
            "edges": self.edges
        }


# =========================
# 核心构建函数
# =========================
def build_kg(kg_candidates: Dict[str, Any]) -> KnowledgeGraph:
    kg = KnowledgeGraph()

    relations = kg_candidates.get("relations", [])
    important_features = kg_candidates.get("important_features", [])

    # 1) 关系边
    for r in relations:
        source = r.get("source")
        target = r.get("target")
        if not source or not target:
            continue

        relation_type = r.get("type", "related_to")
        strength = abs(float(r.get("strength", 0.0)))

        kg.add_edge(
            source=source,
            target=target,
            relation_type=relation_type,
            weight=strength
        )

    # 2) 重要特征节点
    for f in important_features:
        if f:
            kg.add_node(str(f))

    return kg


# =========================
# 兼容旧逻辑
# =========================
def run(state: Dict[str, Any]) -> Dict[str, Any]:
    print("🧠 [KG BUILDER] Building Knowledge Graph...")

    kg_candidates = state.get("kg_candidates", {})
    if not kg_candidates:
        raise ValueError("No kg_candidates found in state")

    kg = build_kg(kg_candidates)
    kg_dict = kg.to_dict()

    state["knowledge_graph"] = kg
    state["knowledge_graph_dict"] = kg_dict

    print(f"✅ KG built: {len(kg.nodes)} nodes, {len(kg.edges)} edges")
    return state


# =========================
# Function Calling: 工具定义
# =========================
def get_tool_definition():
    return {
        "type": "function",
        "function": {
            "name": "build_kg",
            "description": "Build a lightweight knowledge graph from kg_candidates in state.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
                "additionalProperties": False
            }
        }
    }


# =========================
# Function Calling: 执行入口
# =========================
def invoke(params: Dict[str, Any], state: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    params: 保留扩展（当前不需要参数）
    state : 上下文（需包含 kg_candidates）
    returns: (tool_result, new_state)
    """
    local_state = dict(state)
    local_state = run(local_state)

    kg_dict = local_state.get("knowledge_graph_dict", {"nodes": [], "edges": []})

    tool_result = {
        "nodes_count": len(kg_dict.get("nodes", [])),
        "edges_count": len(kg_dict.get("edges", [])),
        "knowledge_graph_dict": kg_dict
    }

    return tool_result, local_state