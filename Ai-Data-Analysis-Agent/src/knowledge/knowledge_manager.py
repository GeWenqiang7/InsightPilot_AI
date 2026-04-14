import os
import re
from collections import defaultdict


class KnowledgeManager:
    """
    可扩展 Knowledge Manager（支持未来 embedding / vector）

    层级设计：
    1. load_documents
    2. chunk_documents
    3. build_index
    4. retrieve（keyword MVP）
    5. format_context（给LLM）
    """

    def __init__(self, knowledge_dir="src/knowledge/knowledge_base"):
        self.knowledge_dir = knowledge_dir

        self.documents = []
        self.chunks = []
        self.index = defaultdict(list)

        self._load_documents()
        self._chunk_documents()
        self._build_index()

    # =========================
    # 1. 文档加载层
    # =========================
    def _load_documents(self):
        if not os.path.exists(self.knowledge_dir):
            print(f"⚠️ Knowledge directory not found: {self.knowledge_dir}")
            return

        for file in os.listdir(self.knowledge_dir):
            if not file.endswith(".txt"):
                continue

            path = os.path.join(self.knowledge_dir, file)

            with open(path, "r", encoding="utf-8") as f:
                content = f.read()

            topic = file.replace(".txt", "")

            doc = {
                "doc_id": topic,
                "name": file,
                "content": content,
                "topic": topic,
                "path": path,
            }

            self.documents.append(doc)

    # =========================
    # 2. chunk 层
    # =========================
    def _chunk_documents(self, chunk_size=300):
        """
        简单chunk：
        - 先按段落分
        - 再按长度切
        """

        chunk_id = 0

        for doc in self.documents:
            paragraphs = doc["content"].split("\n")

            buffer = ""

            for para in paragraphs:
                if len(buffer) + len(para) < chunk_size:
                    buffer += " " + para
                else:
                    self.chunks.append({
                        "chunk_id": f"{doc['doc_id']}_{chunk_id}",
                        "doc_id": doc["doc_id"],
                        "topic": doc["topic"],
                        "text": buffer.strip(),
                        "chunk_index": chunk_id
                    })
                    chunk_id += 1
                    buffer = para

            if buffer:
                self.chunks.append({
                    "chunk_id": f"{doc['doc_id']}_{chunk_id}",
                    "doc_id": doc["doc_id"],
                    "topic": doc["topic"],
                    "text": buffer.strip(),
                    "chunk_index": chunk_id
                })
                chunk_id += 1

    # =========================
    # 3. index 层（keyword）
    # =========================
    def _build_index(self):
        """
        倒排索引（简单版本）
        """
        for chunk in self.chunks:
            words = re.findall(r"\w+", chunk["text"].lower())

            for word in words:
                self.index[word].append(chunk)

    # =========================
    # 4. 检索层（keyword MVP）
    # =========================
    def retrieve(self, query, top_k=5):
        """
        返回结构化 chunk，而不是字符串
        """

        query_words = re.findall(r"\w+", query.lower())

        scores = defaultdict(float)

        for word in query_words:
            for chunk in self.index.get(word, []):
                scores[chunk["chunk_id"]] += 1

        # 排序
        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)

        results = []

        for chunk_id, score in ranked[:top_k]:
            chunk = next(c for c in self.chunks if c["chunk_id"] == chunk_id)

            results.append({
                "chunk_id": chunk["chunk_id"],
                "doc_id": chunk["doc_id"],
                "topic": chunk["topic"],
                "text": chunk["text"],
                "score": score
            })

        return results

    # =========================
    # 5. context组装层
    # =========================
    def format_context(self, retrieved_chunks):
        """
        转成LLM prompt可用格式
        """

        context_blocks = []
        topics = set()

        for chunk in retrieved_chunks:
            topics.add(chunk["topic"])

            context_blocks.append(
                f"[{chunk['topic']}]\n{chunk['text']}"
            )

        context_text = "\n\n".join(context_blocks)

        return {
            "context_text": context_text,
            "topics": list(topics),
            "items": retrieved_chunks
        }

    # =========================
    # 对外接口（稳定API）
    # =========================
    def get_knowledge(self, query, top_k=5):
        retrieved = self.retrieve(query, top_k)
        return self.format_context(retrieved)