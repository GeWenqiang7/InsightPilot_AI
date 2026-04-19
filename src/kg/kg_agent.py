"""
KG Reasoning Agent是一个基于EDA结果构建知识图谱并进行推理的智能模块，旨在帮助用户从数据中挖掘关键特征、识别特征间的关系，并提供可解释的分析结果。
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

from collections import defaultdict
from typing import Dict, Any, Tuple


def find_target_node(kg):
    return "TARGET"


def build_adjacency_list(kg):
    graph = defaultdict(list)
    for edge in kg.edges:
        graph[edge["source"]].append(edge)
    return graph


def compute_feature_importance(kg, target_node):
    importance = []

    for edge in kg.edges:
        if edge["target"] == target_node:
            importance.append({
                "feature": edge["source"],
                "importance": edge["weight"],
                "relation": edge["type"]
            })

    return sorted(importance, key=lambda x: x["importance"], reverse=True)


def compute_node_scores(kg):
    scores = defaultdict(float)

    for edge in kg.edges:
        scores[edge["source"]] += edge["weight"]
        scores[edge["target"]] += edge["weight"]

    return sorted(
        [{"node": k, "score": v} for k, v in scores.items()],
        key=lambda x: x["score"],
        reverse=True
    )


def build_feature_clusters(kg):
    clusters = []
    visited = set()

    for edge in kg.edges:
        f1 = edge["source"]
        f2 = edge["target"]

        if f1 == "TARGET" or f2 == "TARGET":
            continue

        if f1 not in visited and f2 not in visited:
            cluster = set([f1, f2])

            for e in kg.edges:
                if e["source"] in cluster or e["target"] in cluster:
                    cluster.add(e["source"])
                    cluster.add(e["target"])

            clusters.append(list(cluster))
            visited.update(cluster)

    return clusters


def build_reasoning_paths(kg, target_node):
    paths = []

    for edge in kg.edges:
        if edge["target"] == target_node:
            paths.append({
                "path": [edge["source"], target_node],
                "strength": edge["weight"]
            })

    return sorted(paths, key=lambda x: x["strength"], reverse=True)


def export_graph_structure(kg):
    return {
        "nodes": [{"id": n} for n in kg.nodes],
        "edges": [
            {
                "source": e["source"],
                "target": e["target"],
                "weight": e["weight"],
                "type": e["type"]
            }
            for e in kg.edges
        ]
    }


# =========================
# 兼容旧逻辑
# =========================
def run(state: Dict[str, Any]) -> Dict[str, Any]:
    print("🧠 [KG AGENT] Running advanced reasoning...")

    kg = state.get("knowledge_graph")
    if kg is None:
        raise ValueError("Knowledge graph not found")

    target_node = find_target_node(kg)

    feature_importance = compute_feature_importance(kg, target_node)
    node_scores = compute_node_scores(kg)
    clusters = build_feature_clusters(kg)
    paths = build_reasoning_paths(kg, target_node)
    graph_data = export_graph_structure(kg)

    key_features = [f["feature"] for f in feature_importance[:5]]

    result = {
        "key_features": key_features,
        "feature_importance": feature_importance,
        "node_scores": node_scores,
        "clusters": clusters,
        "reasoning_paths": paths,
        "graph": graph_data
    }

    state["kg_result"] = result

    print("✅ KG reasoning done")
    print(f"   - key_features: {len(key_features)}")
    print(f"   - clusters: {len(clusters)}")

    return state


# =========================
# Function Calling: 工具定义
# =========================
def get_tool_definition():
    return {
        "type": "function",
        "function": {
            "name": "reason_with_kg",
            "description": "Run reasoning over existing knowledge graph and return key features, clusters and reasoning paths.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
                "additionalProperties": False
            }
        }
    }


# =========================
# Function Calling
# =========================
def invoke(params: Dict[str, Any], state: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    local_state = dict(state)
    local_state = run(local_state)

    kg_result = local_state.get("kg_result", {})

    tool_result = {
        "key_features": kg_result.get("key_features", []),
        "clusters_count": len(kg_result.get("clusters", [])),
        "reasoning_paths_count": len(kg_result.get("reasoning_paths", [])),
        "kg_result": kg_result
    }

    return tool_result, local_state