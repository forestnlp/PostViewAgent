---
name: postal-knowledge-qa
description: 邮政业务知识问答技能 - 基于语义检索回答业务规则、指标定义、判定标准等知识类问题
---
# 邮政业务知识问答技能 (postal-knowledge-qa)

## 概述

本技能用于回答邮政经营分析中的**业务知识类问题**，如业务规则、指标定义、客户分档标准、流失判定逻辑等。通过语义检索已向量化的业务知识库（规则 + 术语表），返回最相关的知识块供 LLM 生成带依据的回答。

## 适用场景

当用户提出以下类型的问题时，应使用本技能：

- **规则类**："什么算客户流失？""VIP客户的标准是什么？"
- **定义类**："什么是法定客户？""件均单价怎么算？"
- **判定类**："月收入8000元的客户属于哪一档？"
- **流程类**："客户注销要走什么审批流程？"
- **指标类**："减收预警的触发条件是什么？"

## 数据源

- **语义检索接口**: `http://localhost:8001/api/knowledge-search/search`
- **知识库统计**: `http://localhost:8001/api/knowledge-search/stats`
- 知识库包含 18 个业务规则文件 + 术语表，共 76 条知识块，由 bge-m3 嵌入到 ChromaDB

## 工作流程

### 步骤 1: 判断是否适用

识别用户问题是否为**业务知识类**（规则/定义/判定/流程/指标）。若是数据分析类（查数、排名、趋势），应改用 postal-data-query / postal-station-profit-loss 等技能。

### 步骤 2: 语义检索

调用检索接口获取最相关的知识块：

```bash
# 检索相关规则（返回 top 5）
curl -s "http://localhost:8001/api/knowledge-search/search?q=<URL编码的问题>&n_results=5"

# 只检索规则类型
curl -s "http://localhost:8001/api/knowledge-search/search?q=<URL编码的问题>&type_filter=rule&n_results=5"

# 只检索术语
curl -s "http://localhost:8001/api/knowledge-search/search?q=<URL编码的问题>&type_filter=glossary&n_results=5"
```

**注意**：`q` 参数必须进行 URL 编码（中文需转义）。

### 步骤 3: 生成回答

基于检索到的知识块，结合用户问题生成回答。回答要求：

- **引用依据**：说明答案来自哪条规则/术语
- **给出判定逻辑**：如涉及计算，展示公式和示例
- **标注置信度**：若检索结果相关性低（score > 0.6），说明"知识库中未找到直接匹配，以下为推断"

## 检索结果解读

每个结果包含：
- `text`: 知识块全文（规则或术语定义）
- `metadata.type`: `rule`（业务规则）或 `glossary`（术语）
- `metadata.name`: 规则/术语名称
- `score`: 距离分数（越小越相关，通常 < 0.4 为高相关）

## 完整示例

用户询问："什么算客户流失？"

```bash
# 步骤 1: 语义检索
curl -s "http://localhost:8001/api/knowledge-search/search?q=%E4%BB%80%E4%B9%88%E7%AE%97%E5%AE%A2%E6%88%B7%E6%B5%81%E5%A4%B1&n_results=3"
```

返回最相关的 `减收与流失判定` 规则，其中定义了：
- **月流失**: 今年当月无收入 AND 去年当月有收入
- **年流失**: 今年 1~N 月无收入 AND 去年 1~N 月有收入
- **预流失**: 当月累计收入 > 1000 元 AND 同比下降 >= 25%

基于此生成回答。

## 注意事项

- 本技能只做**知识检索与问答**，不执行数据计算
- 若问题涉及具体网点/客户的数据，需结合 postal-data-query 等数据查询技能
- 检索接口需要后端服务运行在 localhost:8001
- 知识库由 `scripts/build_knowledge_vector_db.py` 构建，新增规则后需重新构建
