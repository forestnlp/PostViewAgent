---
name: postal-data-query
description: 邮政经营数据查询技能 - 查询寄递业务商企客户数据、行业指标、区域统计等经营分析数据
---
# 邮政数据查询技能 (postal-data-query)

## 概述

本技能用于查询邮政寄递业务的商企客户经营数据，支持按区域、行业、客户等级等多维度查询业务量、收入、重量等核心指标。

## 核心能力

- 查询商企客户业务数据（业务量、收入、重量）
- 按区域（省/市/县）统计汇总
- 按行业分类（一级/二级/三级）分析
- 按客户等级筛选
- 对比期与统计期数据对比
- 导出查询结果为 CSV/JSON 格式

## 数据源

数据存储在以下位置：

- **演示数据**: `/mnt/skills/custom/postal-data-query/data/商企客户业务数据_演示版.csv`
- **字段说明**: `/mnt/skills/custom/postal-data-query/data/字段说明.md`
- **指标知识库**: `/mnt/skills/custom/postal-data-query/data/metrics_catalog.yaml`

## 工作流程

### 步骤 1: 理解查询需求

当用户询问邮政经营数据时，识别：

- **查询维度**: 区域/行业/客户等级
- **指标类型**: 业务量/收入/重量
- **时间范围**: 统计期/对比期
- **输出格式**: 表格/CSV/JSON

### 步骤 2: 执行查询

使用查询脚本执行数据查询：

```bash
python /mnt/skills/custom/postal-data-query/scripts/query_data.py \
  --action list_columns
```

查看可用列和数据结构。

### 步骤 3: 进行数据分析

#### 查询所有列

```bash
python /mnt/skills/custom/postal-data-query/scripts/query_data.py \
  --action list_columns
```

#### 按省份查询

```bash
python /mnt/skills/custom/postal-data-query/scripts/query_data.py \
  --action query \
  --filter "省份区划名称='江苏省'" \
  --columns "地市区划名称，统计期业务量_万件，统计期收入_万元"
```

#### 按行业统计

```bash
python /mnt/skills/custom/postal-data-query/scripts/query_data.py \
  --action aggregate \
  --group-by "行业一级" \
  --metrics "统计期业务量_万件:sum,统计期收入_万元:sum"
```

#### 按区域汇总

```bash
python /mnt/skills/custom/postal-data-query/scripts/query_data.py \
  --action aggregate \
  --group-by "地市区划名称" \
  --metrics "统计期业务量_万件:sum,统计期收入_万元:sum" \
  --order-by "统计期业务量_万件:desc" \
  --limit 10
```

#### 查询前 10 客户

```bash
python /mnt/skills/custom/postal-data-query/scripts/query_data.py \
  --action query \
  --columns "客户名称，行业一级，统计期业务量_万件，统计期收入_万元" \
  --order-by "统计期业务量_万件:desc" \
  --limit 10
```

#### 导出数据

```bash
python /mnt/skills/custom/postal-data-query/scripts/query_data.py \
  --action query \
  --filter "省份区划名称='浙江省'" \
  --export-to "/mnt/user-data/outputs/浙江商企数据.csv"
```

## 参数说明

| 参数            | 必填 | 说明                                                 |
| --------------- | ---- | ---------------------------------------------------- |
| `--action`    | 是   | 操作类型：`list_columns`, `query`, `aggregate` |
| `--filter`    | 否   | 过滤条件（Python 表达式）                            |
| `--columns`   | 否   | 查询列（逗号分隔）                                   |
| `--group-by`  | 否   | 分组字段（aggregate 模式）                           |
| `--metrics`   | 否   | 聚合指标（格式：`字段：聚合函数`）                 |
| `--order-by`  | 否   | 排序（格式：`字段:asc/desc`）                      |
| `--limit`     | 否   | 返回行数限制                                         |
| `--export-to` | 否   | 导出文件路径                                         |

## 可用字段

### 区划信息

- `省份区划编码`, `地市区划编码`, `区县区划编码`
- `地市区划名称`, `区县区划名称`

### 客户信息

- `客户名称`, `客户等级`
- `行业一级`, `行业二级`, `行业三级`

### 业务指标（统计期）

- `统计期业务量_万件`
- `统计期收入_万元`
- `统计期重量_kg`

### 业务指标（对比期）

- `对比期业务量_万件`
- `对比期收入_万元`
- `对比期重量_kg`

## 查询示例

### 示例 1: 查看数据结构

```bash
python /mnt/skills/custom/postal-data-query/scripts/query_data.py \
  --action list_columns
```

### 示例 2: 江苏省各市区业务量排名

```bash
python /mnt/skills/custom/postal-data-query/scripts/query_data.py \
  --action query \
  --filter "省份区划名称='江苏省'" \
  --columns "地市区划名称，统计期业务量_万件，统计期收入_万元" \
  --order-by "统计期业务量_万件:desc"
```

### 示例 3: 各行业业务量汇总

```bash
python /mnt/skills/custom/postal-data-query/scripts/query_data.py \
  --action aggregate \
  --group-by "行业一级" \
  --metrics "统计期业务量_万件:sum,统计期收入_万元:sum" \
  --order-by "统计期业务量_万件:desc"
```

### 示例 4:  top 10 客户

```bash
python /mnt/skills/custom/postal-data-query/scripts/query_data.py \
  --action query \
  --columns "客户名称，地市区划名称，统计期业务量_万件，统计期收入_万元" \
  --order-by "统计期业务量_万件:desc" \
  --limit 10
```

### 示例 5: 电商行业分析

```bash
python /mnt/skills/custom/postal-data-query/scripts/query_data.py \
  --action query \
  --filter "行业一级='电商'" \
  --columns "客户名称，区县区划名称，统计期业务量_万件，统计期收入_万元，统计期重量_kg" \
  --order-by "统计期业务量_万件:desc"
```

## 注意事项

- 数据为预计算的静态数据，不包含实时更新
- 业务量单位为"万件"，收入单位为"万元"，重量单位为"kg"
- 过滤条件使用 Python 表达式语法
- 聚合函数支持：`sum`, `avg`, `count`, `max`, `min`

## 完整示例

用户询问："请帮我查询江苏省前 10 名城市的业务量排名"

```bash
# 步骤 1: 查看数据结构
python /mnt/skills/custom/postal-data-query/scripts/query_data.py \
  --action list_columns

# 步骤 2: 执行查询
python /mnt/skills/custom/postal-data-query/scripts/query_data.py \
  --action query \
  --filter "省份区划名称='江苏省'" \
  --columns "地市区划名称，统计期业务量_万件，统计期收入_万元" \
  --order-by "统计期业务量_万件:desc" \
  --limit 10
```
