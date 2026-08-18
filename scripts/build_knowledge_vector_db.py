#!/usr/bin/env python3
"""
构建邮政业务知识库向量数据库

将 /项目资料/知识库/rules/*.yaml 与 glossary/terms.yaml 转为文本块，
用本地 bge-m3 嵌入后存入 ChromaDB（持久化到 deer-flow/data/chroma）。

用法：
    python scripts/build_knowledge_vector_db.py [--rebuild]
"""
import argparse
import sys
from pathlib import Path

import yaml

# 允许直接运行脚本时导入 backend 包
BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from app.gateway.routers.knowledge_embedding import BgeM3EmbeddingFunction  # noqa: E402

# 路径配置
PROJECT_ROOT = Path(__file__).resolve().parents[2]  # PostViewAgent/
KB_DIR = PROJECT_ROOT / "项目资料" / "知识库"
RULES_DIR = KB_DIR / "rules"
GLOSSARY_FILE = KB_DIR / "glossary" / "terms.yaml"

# ChromaDB 持久化目录（放在 deer-flow/data/chroma）
CHROMA_DIR = BACKEND_DIR.parent / "data" / "chroma"
COLLECTION_NAME = "postal_knowledge"


def _extract_meta_from_text(raw: str) -> tuple[str, str, str]:
    """从原始文本中宽松提取 规则名称/适用板块/适用对象"""
    name = ""
    board = ""
    obj = ""
    for line in raw.splitlines():
        line = line.strip()
        if line.startswith("规则名称:"):
            name = line.split(":", 1)[1].strip()
        elif line.startswith("适用板块:"):
            board = line.split(":", 1)[1].strip()
        elif line.startswith("适用对象:"):
            obj = line.split(":", 1)[1].strip()
    return name, board, obj


def load_rules() -> list[dict]:
    """加载所有规则文件，每个文件作为一个文档块（解析失败时退化为纯文本）"""
    blocks = []
    for f in sorted(RULES_DIR.glob("*.yaml")):
        raw = f.read_text(encoding="utf-8")
        try:
            data = yaml.safe_load(raw)
        except Exception as e:
            print(f"[WARN] YAML 解析失败 {f.name}，退化为纯文本: {e}")
            data = None

        if isinstance(data, dict):
            rule_name = data.get("规则名称") or f.stem
            board = data.get("适用板块", "")
            obj = data.get("适用对象", "")
            text_parts = [f"规则: {rule_name}"]
            if board:
                text_parts.append(f"适用板块: {board}")
            if obj:
                text_parts.append(f"适用对象: {obj}")
            text_parts.append(yaml.dump(data, allow_unicode=True, sort_keys=False))
            text = "\n".join(text_parts)
        else:
            # 退化：直接使用原始文本
            name, board, obj = _extract_meta_from_text(raw)
            rule_name = name or f.stem
            text = raw

        blocks.append({
            "id": f"rule_{f.stem}",
            "text": text,
            "metadata": {
                "type": "rule",
                "name": rule_name,
                "file": f.name,
                "board": str(board),
                "object": str(obj),
            },
        })
    return blocks


def load_glossary() -> list[dict]:
    """加载术语表，按术语条目切分"""
    blocks = []
    try:
        data = yaml.safe_load(GLOSSARY_FILE.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"[WARN] 解析术语表失败: {e}")
        return blocks

    if not isinstance(data, dict):
        return blocks

    for category, terms in data.items():
        if not isinstance(terms, list):
            continue
        for term in terms:
            if not isinstance(term, dict):
                continue
            name = term.get("术语", "")
            explain = term.get("解释", "")
            ident = term.get("标识", "")
            if not name:
                continue
            text = f"术语: {name}\n类别: {category}\n解释: {explain}"
            if ident:
                text += f"\n标识: {ident}"
            blocks.append({
                "id": f"glossary_{category}_{name}",
                "text": text,
                "metadata": {
                    "type": "glossary",
                    "name": name,
                    "category": str(category),
                    "file": GLOSSARY_FILE.name,
                },
            })
    return blocks


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--rebuild", action="store_true", help="重建集合（清空旧数据）")
    args = parser.parse_args()

    import chromadb

    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    ef = BgeM3EmbeddingFunction()

    collection = client.get_or_create_collection(
        COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
        embedding_function=ef,
    )

    if args.rebuild:
        print("[INFO] 重建模式：清空旧集合")
        try:
            client.delete_collection(COLLECTION_NAME)
        except Exception:
            pass
        collection = client.create_collection(
            COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
            embedding_function=ef,
        )

    # 收集所有块
    blocks = load_rules() + load_glossary()
    print(f"[INFO] 共加载 {len(blocks)} 个知识块")

    # 分批写入（避免一次请求过大）
    batch_size = 20
    for i in range(0, len(blocks), batch_size):
        batch = blocks[i : i + batch_size]
        ids = [b["id"] for b in batch]
        docs = [b["text"] for b in batch]
        metas = [b["metadata"] for b in batch]
        collection.upsert(ids=ids, documents=docs, metadatas=metas)
        print(f"  已写入 {i + len(batch)}/{len(blocks)}")

    count = collection.count()
    print(f"\n[OK] 向量库构建完成，共 {count} 条记录")
    print(f"    存储位置: {CHROMA_DIR}")


if __name__ == "__main__":
    main()
