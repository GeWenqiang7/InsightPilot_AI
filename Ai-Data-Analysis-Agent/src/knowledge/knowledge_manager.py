import os
import re
from collections import defaultdict


class KnowledgeManager:
    """
    可扩展 Knowledge Manager（支持：
    ✔ keyword检索
    ✔ 中文query → 英文翻译（LLM）
    ✔ RAG context构建
    ✔ 未来 embedding / vector 扩展
    """

    def __init__(self, knowledge_dir=None, llm_client=None):

        # =========================
        # 🔥 自动定位项目根目录
        # =========================
        BASE_DIR = os.path.dirname(
            os.path.dirname(
                os.path.dirname(os.path.abspath(__file__))
            )
        )

        # =========================
        # 🔥 设置知识库路径
        # =========================
        if knowledge_dir is None:
            knowledge_dir = os.path.join(
                BASE_DIR,
                "src",
                "knowledge",
                "knowledge_base"
            )

        self.knowledge_dir = knowledge_dir
        self.llm_client = llm_client  # 🔥 LLM用于query翻译

        print(f"📂 Knowledge path: {self.knowledge_dir}")

        self.documents = []
        self.chunks = []
        self.index = defaultdict(list)

        # 初始化流程
        self._load_documents()
        self._chunk_documents()
        self._build_index()

    # =========================
    # 🔥 中英文 tokenization
    # =========================
    def _tokenize(self, text):
        """
        支持：
        - 中文（按字）
        - 英文（按词）
        """
        chinese_chars = list(text)
        english_words = re.findall(r"[a-zA-Z0-9]+", text.lower())
        return chinese_chars + english_words

    # =========================
    # 🔥 LLM query翻译（核心升级）
    # =========================
    def _translate_query(self, query):

        if not self.llm_client:
            return ""

        prompt = f"""
Translate the following user query into concise English search keywords.

Rules:
- Keep only important terms
- No full sentences
- Output only keywords

Query:
{query}
"""

        try:
            result = self.llm_client.generate(prompt)
            translated = result.strip()

            print(f"🌍 Translated query: {translated}")

            return translated

        except Exception as e:
            print("⚠️ Translation failed:", e)
            return ""

    # =========================
    # 1. 文档加载
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

        print(f"✅ Loaded {len(self.documents)} documents")

    # =========================
    # 2. chunk
    # =========================
    def _chunk_documents(self, chunk_size=300):

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

        print(f"✅ Created {len(self.chunks)} chunks")

    # =========================
    # 3. index
    # =========================
    def _build_index(self):

        for chunk in self.chunks:

            words = self._tokenize(chunk["text"])

            for word in words:
                self.index[word].append(chunk)

        print(f"✅ Built index with {len(self.index)} keywords")

    # =========================
    # 4. 检索（核心）
    # =========================
    def retrieve(self, query, top_k=5):

        # 原始query
        query_words = self._tokenize(query)

        # 🔥 LLM翻译
        translated_query = self._translate_query(query)

        if translated_query:
            query_words += self._tokenize(translated_query)

        scores = defaultdict(float)

        for word in query_words:
            for chunk in self.index.get(word, []):
                scores[chunk["chunk_id"]] += 1

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

        print(f"🔍 Retrieved {len(results)} chunks")

        return results

    # =========================
    # 5. context组装
    # =========================
    def format_context(self, retrieved_chunks):

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
    # 对外接口
    # =========================
    def get_knowledge(self, query, top_k=5):

        retrieved = self.retrieve(query, top_k)

        return self.format_context(retrieved)