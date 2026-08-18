"""
邮政业务知识库语义检索 API

基于 ChromaDB + bge-m3 嵌入，对已结构化的业务规则与术语表做语义检索。
用于支撑"业务规则问答"场景：用户用自然语言提问，返回最相关的知识块。
"""
from pathlib import Path
from typing import List, Optional

import chromadb
from fastapi import APIRouter, HTTPException, Query

from app.gateway.routers.knowledge_embedding import BgeM3EmbeddingFunction

router = APIRouter(prefix="/api/knowledge-search", tags=["knowledge-search"])

# ChromaDB 持久化目录（与向量化脚本一致）
CHROMA_DIR = (
    Path(__file__).resolve().parents[4] / "data" / "chroma"
)
COLLECTION_NAME = "postal_knowledge"

_client = None
_collection = None


def _get_collection():
    """懒加载 ChromaDB 集合"""
    global _client, _collection
    if _collection is not None:
        return _collection
    _client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    ef = BgeM3EmbeddingFunction()
    try:
        _collection = _client.get_collection(COLLECTION_NAME, embedding_function=ef)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"知识库未初始化，请先运行 scripts/build_knowledge_vector_db.py: {e}",
        )
    return _collection


@router.get("/search")
def search_knowledge(
    q: str = Query(..., description="查询问题"),
    n_results: int = Query(5, ge=1, le=20, description="返回结果数"),
    type_filter: Optional[str] = Query(None, description="过滤类型：rule/glossary"),
):
    """语义检索知识库，返回最相关的规则或术语"""
    if not q.strip():
        raise HTTPException(status_code=400, detail="查询内容不能为空")

    collection = _get_collection()
    ef = BgeM3EmbeddingFunction()

    where = {"type": type_filter} if type_filter else None

    result = collection.query(
        query_embeddings=[ef.embed_query(q)],
        n_results=n_results,
        where=where,
    )

    items = []
    for doc, meta, dist in zip(
        result["documents"][0], result["metadatas"][0], result["distances"][0]
    ):
        items.append({
            "text": doc,
            "metadata": meta,
            "score": round(dist, 4),
        })

    return {
        "query": q,
        "count": len(items),
        "results": items,
    }


@router.get("/stats")
def knowledge_stats():
    """查看知识库统计信息"""
    collection = _get_collection()
    return {
        "collection": COLLECTION_NAME,
        "total": collection.count(),
        "chroma_dir": str(CHROMA_DIR),
    }
