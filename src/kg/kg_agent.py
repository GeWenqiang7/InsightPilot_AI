'''
知识图（KG）Agent
- 负责从EDA结果中构建知识图（KG）
- 通过分析特征间的关系、重要性等信息，构建KG结构
- 输出KG结构供后续分析和可视化使用

核心功能：
1. 关系抽取：从EDA结果中识别特征间的相关性、重要特征等信息，构建边和节点
2. KG构建：将抽取的信息组织成KG结构，支持简单的查询和可视化接口
3. 对外接口：提供统一的run函数，供Agent调用，输出KG结构

设计思路：
- 轻量级设计：KG结构简单，主要关注特征关系和重要性  
- 模块化：关系抽取、KG构建、推理等功能模块化，便于维护和升级
- 可扩展性：KG结构设计为可扩展，未来可以加入更多类型的关系和节点属性

作用：
- 通过KG结构更好地理解数据特征间的关系，辅助后续的特征选择、模型构建等步骤  

'''

from collections import defaultdict


# 基础工具

def find_target_node(kg):
    return "TARGET"

def build_adjacency_list(kg):
    graph = defaultdict(list)

    for edge in kg.edges:
        graph[edge["source"]].append(edge)
    
    return graph


# =========================
# Feature Importance (基于KG的特征重要性分析)
# =========================

def compute_feature_importance(kg, target_node):
    importance = []

    for edge in kg.edges:
        if edge["target"] == target_node:
            importance.append({
                "feature": edge["source"],
                "importance": edge["weight"],
                "relation": edge["type"]
            })

    importance = sorted(
        importance,
        key=lambda x: x["importance"],
        reverse=True
    )

    return importance


# =========================
#  Node Ranking（图级评分，基于边权重和连接度）
# =========================

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


# =========================
#  Feature Clusters（共线性/关系组）
# =========================

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


# =========================
#  推理路径（多路径）
# =========================

def build_reasoning_paths(kg, target_node):
    paths = []

    for edge in kg.edges:
        if edge["target"] == target_node:
            paths.append({
                "path": [edge["source"], target_node],
                "strength": edge["weight"]
            })

    return sorted(paths, key=lambda x: x["strength"], reverse=True)


# =========================
#  Graph结构导出（给可视化用）
# =========================

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
# 主接口（核心）
# =========================

def run(state):

    print("🧠 [KG AGENT] Running advanced reasoning...")

    kg = state.get("knowledge_graph")

    if kg is None:
        raise ValueError("Knowledge graph not found")

    target_node = find_target_node(kg)

    # =========================
    # 1️⃣ Feature importance
    # =========================
    feature_importance = compute_feature_importance(kg, target_node)

    # =========================
    # 2️⃣ Node ranking
    # =========================
    node_scores = compute_node_scores(kg)

    # =========================
    # 3️⃣ Feature clusters
    # =========================
    clusters = build_feature_clusters(kg)

    # =========================
    # 4️⃣ 推理路径
    # =========================
    paths = build_reasoning_paths(kg, target_node)

    # =========================
    # 5️⃣ Graph export
    # =========================
    graph_data = export_graph_structure(kg)

    # =========================
    # 6️⃣ Key features（最终输出）
    # =========================
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

    print(f"✅ KG reasoning done")
    print(f"   - key_features: {len(key_features)}")
    print(f"   - clusters: {len(clusters)}")

    return state