'''
知识图谱构建器（KG Builder）：
- 作用：从EDA结果中抽取结构化关系，构建轻量级知识图谱
- 输入：EDA结果中的相关性分析、重要特征等信息
- 输出：KG结构（节点+边），存入state供Agent后续使用

核心功能：
1. 关系抽取：从EDA结果中识别特征间的相关性、重要特征等信息，构建边和节点
2. KG构建：将抽取的信息组织成KG结构，支持简单的查询和可视化接口
3. 对外接口：提供统一的run函数，供Agent调用，输出KG结构

'''

class KnowledgeGraph:
    """
    轻量级知识图谱结构
    """

    def __init__(self):
        self.nodes = set()
        self.edges = []

    def add_node(self, node):
        self.nodes.add(node)

    def add_edge(self, source, target, relation_type, weight=1.0):
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
# 🔥 构建 KG（核心函数）
# =========================
def build_kg(kg_candidates):

    kg = KnowledgeGraph()

    relations = kg_candidates.get("relations", [])
    important_features = kg_candidates.get("important_features", [])

    # =========================
    # 1️⃣ 加入关系边
    # =========================
    for r in relations:
        source = r["source"]
        target = r["target"]
        relation_type = r.get("type", "related_to")
        strength = abs(r.get("strength", 0.0))

        kg.add_edge(
            source=source,
            target=target,
            relation_type=relation_type,
            weight=strength
        )

    # =========================
    # 2️⃣ 加入重要特征节点（标记）
    # =========================
    for f in important_features:
        kg.add_node(f)

    return kg


# =========================
# 🔥 对外接口（Agent调用）
# =========================
def run(state):

    print("🧠 [KG BUILDER] Building Knowledge Graph...")

    kg_candidates = state.get("kg_candidates", {})

    if not kg_candidates:
        raise ValueError("No kg_candidates found in state")

    kg = build_kg(kg_candidates)

    kg_dict = kg.to_dict()

    # 存入state
    state["knowledge_graph"] = kg
    state["knowledge_graph_dict"] = kg_dict

    print(f"✅ KG built: {len(kg.nodes)} nodes, {len(kg.edges)} edges")

    return state