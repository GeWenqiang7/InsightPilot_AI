import math
import re
from typing import List


class HashingEmbedder:
    """
    轻量本地向量化器（无外部依赖）：
    - 用哈希技巧把 token 投影到固定维度
    - 支持对 query / 文本做统一向量化
    """

    def __init__(self, dim: int = 256):
        self.dim = dim

    def _tokenize(self, text: str) -> List[str]:
        if not text:
            return []
        english_words = re.findall(r"[a-zA-Z0-9_]+", text.lower())
        chinese_chars = [ch for ch in text if "\u4e00" <= ch <= "\u9fff"]
        return english_words + chinese_chars

    def embed(self, text: str) -> List[float]:
        vec = [0.0] * self.dim
        tokens = self._tokenize(text)
        if not tokens:
            return vec

        for token in tokens:
            idx = hash(token) % self.dim
            vec[idx] += 1.0

        norm = math.sqrt(sum(v * v for v in vec))
        if norm == 0:
            return vec
        return [v / norm for v in vec]
