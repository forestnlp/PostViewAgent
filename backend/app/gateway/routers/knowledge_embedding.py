"""
bge-m3 嵌入函数封装（ChromaDB 兼容）

通过本地 Ollama 服务调用 bge-m3:latest 生成 1024 维向量。
供知识库向量化脚本与 /api/knowledge-search 接口复用。
"""
import requests

OLLAMA_URL = "http://192.168.7.88:11434"
MODEL = "bge-m3:latest"


class BgeM3EmbeddingFunction:
    """ChromaDB EmbeddingFunction 兼容实现，基于本地 Ollama bge-m3"""

    def __init__(self, url: str = OLLAMA_URL, model: str = MODEL):
        self.url = f"{url}/api/embed"
        self.model = model

    def _embed(self, texts):
        if isinstance(texts, str):
            texts = [texts]
        # 展平嵌套列表（ChromaDB 可能传入 [[...]]）
        if texts and isinstance(texts[0], list):
            texts = texts[0]
        resp = requests.post(
            self.url,
            json={"model": self.model, "input": list(texts)},
            timeout=180,
        )
        resp.raise_for_status()
        return resp.json()["embeddings"]

    def __call__(self, input):
        return self._embed(input)

    def embed_query(self, input):
        return self._embed(input)[0]

    def embed_documents(self, input):
        return self._embed(input)

    def name(self):
        return "bge-m3"
