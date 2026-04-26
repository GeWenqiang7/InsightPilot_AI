import os
import re
from collections import defaultdict
from typing import Dict, List

from src.knowledge.embedder import HashingEmbedder
from src.knowledge.retriever import InMemoryVectorStore


class KnowledgeManager:
    """
    升级版 Knowledge Manager：
    1) 文档加载 -> chunking -> embedding -> 向量库入库
    2) query 向量化 -> 向量检索 + 关键词检索
    3) hybrid 融合 -> rerank 重排序
    4) 返回增强 prompt 所需上下文与 debug 信息
    """

    def __init__(self, knowledge_dir=None, llm_client=None, embedding_dim: int = 256):
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        if knowledge_dir is None:
            knowledge_dir = os.path.join(base_dir, "src", "knowledge", "knowledge_base")

        self.knowledge_dir = knowledge_dir
        self.llm_client = llm_client
        self.documents: List[Dict] = []
        self.chunks: List[Dict] = []
        self.keyword_index = defaultdict(list)
        self.embedder = HashingEmbedder(dim=embedding_dim)
        self.vector_store = InMemoryVectorStore()

        print(f"📂 Knowledge path: {self.knowledge_dir}")
        self._load_documents()
        self._chunk_documents()
        self._build_keyword_index()
        self._build_vector_index()

    def _tokenize(self, text: str) -> List[str]:
        english_words = re.findall(r"[a-zA-Z0-9]+", text.lower())
        chinese_chars = [ch for ch in text if "\u4e00" <= ch <= "\u9fff"]
        return english_words + chinese_chars

    def _translate_query(self, query: str) -> str:
        if not self.llm_client:
            return ""
        prompt = f"""
Translate the following user query into concise English search keywords.
Rules:
- Keep only important terms
- Output only keywords
Query:
{query}
"""
        try:
            return (self.llm_client.generate(prompt) or "").strip()
        except Exception as exc:
            print("⚠️ Translation failed:", exc)
            return ""

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
            self.documents.append(
                {
                    "doc_id": topic,
                    "name": file,
                    "content": content,
                    "topic": topic,
                    "path": path,
                }
            )
        print(f"✅ Loaded {len(self.documents)} documents")

    def _chunk_documents(self, chunk_size: int = 300):
        chunk_id = 0
        for doc in self.documents:
            paragraphs = doc["content"].split("\n")
            buffer = ""
            for para in paragraphs:
                if len(buffer) + len(para) < chunk_size:
                    buffer += " " + para
                else:
                    self.chunks.append(
                        {
                            "chunk_id": f"{doc['doc_id']}_{chunk_id}",
                            "doc_id": doc["doc_id"],
                            "topic": doc["topic"],
                            "path": doc["path"],
                            "text": buffer.strip(),
                        }
                    )
                    chunk_id += 1
                    buffer = para

            if buffer:
                self.chunks.append(
                    {
                        "chunk_id": f"{doc['doc_id']}_{chunk_id}",
                        "doc_id": doc["doc_id"],
                        "topic": doc["topic"],
                        "path": doc["path"],
                        "text": buffer.strip(),
                    }
                )
                chunk_id += 1
        print(f"✅ Created {len(self.chunks)} chunks")

    def _build_keyword_index(self):
        for chunk in self.chunks:
            for token in self._tokenize(chunk["text"]):
                self.keyword_index[token].append(chunk)
        print(f"✅ Built keyword index with {len(self.keyword_index)} terms")

    def _build_vector_index(self):
        for chunk in self.chunks:
            vector = self.embedder.embed(chunk["text"])
            self.vector_store.upsert(
                item_id=chunk["chunk_id"],
                vector=vector,
                metadata={
                    "chunk_id": chunk["chunk_id"],
                    "doc_id": chunk["doc_id"],
                    "topic": chunk["topic"],
                    "source_path": chunk["path"],
                    "text": chunk["text"],
                },
            )
        print(f"✅ Built vector index with {len(self.vector_store.items)} vectors")

    def _keyword_retrieve(self, query: str, top_k: int = 8) -> List[Dict]:
        terms = self._tokenize(query)
        translated = self._translate_query(query)
        if translated:
            terms += self._tokenize(translated)

        scores = defaultdict(float)
        chunk_map = {chunk["chunk_id"]: chunk for chunk in self.chunks}
        for t in terms:
            for chunk in self.keyword_index.get(t, []):
                scores[chunk["chunk_id"]] += 1.0

        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
        out = []
        for chunk_id, score in ranked:
            chunk = chunk_map.get(chunk_id)
            if not chunk:
                continue
            out.append(
                {
                    "chunk_id": chunk["chunk_id"],
                    "doc_id": chunk["doc_id"],
                    "topic": chunk["topic"],
                    "text": chunk["text"],
                    "source_path": chunk["path"],
                    "keyword_score": float(score),
                }
            )
        return out

    def _vector_retrieve(self, query: str, top_k: int = 8) -> List[Dict]:
        q_vec = self.embedder.embed(query)
        hits = self.vector_store.query(q_vec, top_k=top_k)
        out = []
        for item, score in hits:
            meta = item["metadata"]
            out.append(
                {
                    "chunk_id": meta["chunk_id"],
                    "doc_id": meta["doc_id"],
                    "topic": meta["topic"],
                    "text": meta["text"],
                    "source_path": meta["source_path"],
                    "vector_score": float(score),
                }
            )
        return out

    def _hybrid_and_rerank(self, query: str, top_k: int = 5) -> Dict[str, List[Dict]]:
        kw = self._keyword_retrieve(query, top_k=max(top_k * 3, 8))
        vec = self._vector_retrieve(query, top_k=max(top_k * 3, 8))

        merged = {}
        for item in kw:
            cid = item["chunk_id"]
            merged[cid] = dict(item)
            merged[cid].setdefault("keyword_score", 0.0)
            merged[cid].setdefault("vector_score", 0.0)
        for item in vec:
            cid = item["chunk_id"]
            if cid not in merged:
                merged[cid] = dict(item)
                merged[cid].setdefault("keyword_score", 0.0)
            else:
                merged[cid]["vector_score"] = item.get("vector_score", 0.0)

        terms = set(self._tokenize(query))
        pre_rerank = []
        for item in merged.values():
            k = item.get("keyword_score", 0.0)
            v = item.get("vector_score", 0.0)
            item["hybrid_score"] = 0.45 * k + 0.55 * v
            pre_rerank.append(item)
        pre_rerank.sort(key=lambda x: x.get("hybrid_score", 0.0), reverse=True)

        # rerank：在 hybrid 分数基础上增加 query-term overlap
        post_rerank = []
        for item in pre_rerank:
            chunk_terms = set(self._tokenize(item.get("text", "")))
            overlap = len(terms & chunk_terms)
            item["rerank_score"] = item.get("hybrid_score", 0.0) + 0.2 * overlap
            post_rerank.append(item)
        post_rerank.sort(key=lambda x: x.get("rerank_score", 0.0), reverse=True)

        return {
            "pre_rerank_topk": pre_rerank[:top_k],
            "post_rerank_topk": post_rerank[:top_k],
        }

    def _build_evidence_items(self, reranked: List[Dict], max_items: int = 3) -> List[Dict]:
        evidence_items = []
        for item in reranked[:max_items]:
            snippet = (item.get("text", "") or "").replace("\n", " ").strip()[:220]
            evidence_items.append(
                {
                    "chunk_id": item.get("chunk_id"),
                    "topic": item.get("topic"),
                    "score": item.get("rerank_score", item.get("hybrid_score", 0.0)),
                    "source_path": item.get("source_path", ""),
                    "snippet": snippet,
                }
            )
        return evidence_items

    def _estimate_retrieval_confidence(self, reranked: List[Dict]) -> float:
        if not reranked:
            return 0.0
        top_score = float(reranked[0].get("rerank_score", 0.0))
        if top_score >= 6:
            return 0.9
        if top_score >= 3:
            return 0.75
        if top_score >= 1.5:
            return 0.6
        return 0.45

    def get_knowledge(self, query: str, top_k: int = 5) -> Dict:
        retrieval_debug = self._hybrid_and_rerank(query, top_k=top_k)
        reranked = retrieval_debug["post_rerank_topk"]
        topics = list({item.get("topic") for item in reranked if item.get("topic")})
        evidence_items = self._build_evidence_items(reranked)
        context_text = "\n\n".join([f"[{i['topic']}]\n{i['text']}" for i in reranked])
        retrieval_confidence = self._estimate_retrieval_confidence(reranked)

        print(f"🔍 Retrieved {len(reranked)} chunks after rerank")
        return {
            "context_text": context_text,
            "topics": topics,
            "items": reranked,
            "evidence_items": evidence_items,
            "retrieval_confidence": retrieval_confidence,
            "retrieval_debug": retrieval_debug,
        }

