import math
from typing import Dict, List, Tuple


def cosine_similarity(a: List[float], b: List[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


class InMemoryVectorStore:
    """
    轻量向量库（内存版）：
    - upsert: 写入 chunk 向量
    - query: 返回 top-k 相似 chunk
    """

    def __init__(self):
        self.items: List[Dict] = []

    def upsert(self, item_id: str, vector: List[float], metadata: Dict):
        self.items.append(
            {
                "id": item_id,
                "vector": vector,
                "metadata": metadata,
            }
        )

    def query(self, query_vector: List[float], top_k: int = 5) -> List[Tuple[Dict, float]]:
        scored = []
        for item in self.items:
            score = cosine_similarity(query_vector, item["vector"])
            scored.append((item, score))
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_k]
