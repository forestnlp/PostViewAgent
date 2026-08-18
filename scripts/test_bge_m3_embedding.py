#!/usr/bin/env python3
"""
测试本地 7.88 Ollama bge-m3 嵌入模型
验证：连通性、向量维度、语义相似度
"""
import json
import time

import requests

OLLAMA_URL = "http://192.168.7.88:11434"
MODEL = "bge-m3:latest"


def embed(texts, timeout=180):
    """调用 Ollama /api/embed 获取向量（批量）"""
    payload = {"model": MODEL, "input": texts}
    resp = requests.post(f"{OLLAMA_URL}/api/embed", json=payload, timeout=timeout)
    resp.raise_for_status()
    return resp.json()


def cosine_sim(a, b):
    """计算余弦相似度"""
    dot = sum(x * y for x, y in zip(a, b))
    na = sum(x * x for x in a) ** 0.5
    nb = sum(y * y for y in b) ** 0.5
    return dot / (na * nb + 1e-9)


if __name__ == "__main__":
    print(f"=== 测试 bge-m3 嵌入模型 ({OLLAMA_URL}) ===\n")

    # 1. 连通性测试
    try:
        tags = requests.get(f"{OLLAMA_URL}/api/tags", timeout=10).json()
        models = [m["name"] for m in tags.get("models", [])]
        has_bge = any("bge" in m for m in models)
        print(f"[OK] Ollama 服务可达，已加载 {len(models)} 个模型")
        print(f"     bge-m3 存在: {'是' if has_bge else '否'}")
    except Exception as e:
        print(f"[FAIL] 无法连接 Ollama: {e}")
        exit(1)

    # 2. 嵌入测试（首次可能需加载模型，超时设长）
    texts = [
        "武昌区水果湖支局营业利润",
        "网点亏损预警分析",
        "邮政寄递业务收入增长",
        "今天天气很好",
    ]
    t0 = time.time()
    result = embed(texts)
    embeddings = result["embeddings"]
    dim = len(embeddings[0])
    print(f"\n[OK] 成功生成 {len(texts)} 条向量，维度: {dim}，耗时 {time.time()-t0:.1f}s")

    # 3. 语义相似度验证
    print("\n=== 语义相似度 ===")
    pairs = [(0, 1), (0, 2), (0, 3)]
    labels = ["损益 vs 预警", "损益 vs 寄递", "损益 vs 天气"]
    for (i, j), label in zip(pairs, labels):
        sim = cosine_sim(embeddings[i], embeddings[j])
        print(f"  {label}: {sim:.4f}")

    print("\n=== 测试完成 ===")
