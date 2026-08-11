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

- **演示数据**: `/mnt/skills/public/postal-data-query/data/商企客户业务数据_演示版.csv`
- **字段说明**: `/mnt/skills/public/postal-data-query/data/字段说明.md`
- **指标知识库**: `/mnt/skills/public/postal-data-query/data/metrics_catalog.yaml`

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
python /mnt/skills/public/postal-data-query/scripts/query_data.py \
  --action list_columns
```

查看可用列和数据结构。

### 步骤 3: 进行数据分析

**重要：--aggregate 命令必须配合 --filter 使用筛选条件！**

#### 查询所有列

```bash
python /mnt/skills/public/postal-data-query/scripts/query_data.py \
  --action list_columns
```

#### 按省份查询

```bash
python /mnt/skills/public/postal-data-query/scripts/query_data.py \
  --action query \
  --filter "省份区划名称='江苏省'" \
  --columns "地市区划名称，统计期业务量_万件，统计期收入_万元"
```

#### 按行业统计（带筛选）

```bash
# 正确：aggregate必须配合filter传递筛选条件
python /mnt/skills/public/postal-data-query/scripts/query_data.py \
  --action aggregate \
  --filter "月份 = '2026-06' AND 地市区划名称 = '武汉市'" \
  --group-by "行业一级" \
  --metrics "统计期业务量_万件:sum,统计期收入_万元:sum"
```

#### 按区域汇总（带筛选）

```bash
python /mnt/skills/public/postal-data-query/scripts/query_data.py \
  --action aggregate \
  --filter "月份 = '2026-07'" \
  --group-by "地市区划名称" \
  --metrics "统计期业务量_万件:sum,统计期收入_万元:sum" \
  --order-by "统计期业务量_万件:desc" \
  --limit 10
```

#### 查询前 10 客户

```bash
python /mnt/skills/public/postal-data-query/scripts/query_data.py \
  --action query \
  --columns "客户名称，行业一级，统计期业务量_万件，统计期收入_万元" \
  --order-by "统计期业务量_万件:desc" \
  --limit 10
```

#### 导出数据

```bash
python /mnt/skills/public/postal-data-query/scripts/query_data.py \
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

### 时间维度

- `月份`: 统计月份，格式 YYYY-MM（如 2026-05）
- 数据包含 3 个月份（2026-05, 2026-06, 2026-07）

### 区划信息

- `省份区划编码`, `省份区划名称`
- `地市区划编码`, `地市区划名称`
- `区县区划编码`, `区县区划名称`

### 客户信息

- `主码`, `法定客户名称`, `子码`, `协议客户名称`
- `客户等级`, `注册日期`
- `行业一级`, `行业二级`, `行业三级`

### 业务指标（统计期 - 当年数据）

- `统计期业务量_万件`: 当年当月业务量
- `统计期收入_万元`: 当年当月收入
- `统计期重量_kg`: 当年当月重量

### 业务指标（对比期 - 去年同期数据）

**重要：对比期是去年同期数据（同比），不是上个月（环比）**

- `对比期业务量_万件`: 去年同期业务量
- `对比期收入_万元`: 去年同期收入
- `对比期重量_kg`: 去年同期重量

示例：
- 2026-05 的统计期 = 2026年5月数据
- 2026-05 的对比期 = 2025年5月数据（去年同期）
- 同比增长 = 统计期 > 对比期
- 同比减收 = 统计期 < 对比期

## 查询示例

### 示例 1: 查看数据结构

```bash
python /mnt/skills/public/postal-data-query/scripts/query_data.py \
  --action list_columns
```

### 示例 2: 江苏省各市区业务量排名

```bash
python /mnt/skills/public/postal-data-query/scripts/query_data.py \
  --action query \
  --filter "省份区划名称='江苏省'" \
  --columns "地市区划名称，统计期业务量_万件，统计期收入_万元" \
  --order-by "统计期业务量_万件:desc"
```

### 示例 3: 各行业业务量汇总

```bash
python /mnt/skills/public/postal-data-query/scripts/query_data.py \
  --action aggregate \
  --group-by "行业一级" \
  --metrics "统计期业务量_万件:sum,统计期收入_万元:sum" \
  --order-by "统计期业务量_万件:desc"
```

### 示例 4: 按月份筛选

```bash
# 查询2026年6月数据
python /mnt/skills/public/postal-data-query/scripts/query_data.py \
  --action query \
  --filter "月份 = '2026-06'" \
  --columns "月份, 行业一级, 地市区划名称, 统计期收入_万元, 对比期收入_万元" \
  --limit 20
```

### 示例 5: 月份+行业组合分析

```bash
# 按月份和行业分组统计
python /mnt/skills/public/postal-data-query/scripts/query_data.py \
  --action aggregate \
  --group-by "月份, 行业一级" \
  --metrics "统计期收入_万元:sum,统计期业务量_万件:sum" \
  --order-by "统计期收入_万元_sum:desc"
```

### 示例 6: 客户减收分析（同比）

```bash
# 分析区县减收情况（统计期 vs 去年同期对比期）
python /mnt/skills/public/postal-data-query/scripts/query_data.py \
  --action analyze \
  --analysis-type "loss" \
  --target "区县区划名称"
```

### 示例 7: top 10 客户

```bash
python /mnt/skills/public/postal-data-query/scripts/query_data.py \
  --action query \
  --columns "法定客户名称, 地市区划名称, 统计期业务量_万件, 统计期收入_万元" \
  --order-by "统计期业务量_万件:desc" \
  --limit 10
```

### 示例 8: 电商行业分析

```bash
python /mnt/skills/public/postal-data-query/scripts/query_data.py \
  --action query \
  --filter "行业一级 = '电商类'" \
  --columns "法定客户名称, 区县区划名称, 统计期业务量_万件, 统计期收入_万元, 统计期重量_kg" \
  --order-by "统计期业务量_万件:desc"
```

## 注意事项

- **对比期是去年同期数据（同比），不是上个月（环比）**
  - 统计期收入_万元 vs 对比期收入_万元 = 同比变化
  - 不要理解为环比变化（上个月）
- **--aggregate 命令必须配合 --filter！** 如果查询条件是"武汉市2026年6月铂金客户"，那么 aggregate 命令也必须加上相同的 filter 条件
- 数据为预计算的静态数据，不包含实时更新
- 业务量单位为"万件"，收入单位为"万元"，重量单位为"kg"
- 过滤条件使用 SQL WHERE 子句语法（DuckDB）
- 聚合函数支持：`sum`, `avg`, `count`, `max`, `min`
- 数据包含湖北省 3 个月份（2026-05/06/07），6 个行业（商企类/政务类/电商类/国际类/散户类/物流类）

## 完整示例

用户询问："请帮我查询江苏省前 10 名城市的业务量排名"

```bash
# 步骤 1: 查看数据结构
python /mnt/skills/public/postal-data-query/scripts/query_data.py \
  --action list_columns

# 步骤 2: 执行查询
python /mnt/skills/public/postal-data-query/scripts/query_data.py \
  --action query \
  --filter "省份区划名称='江苏省'" \
  --columns "地市区划名称，统计期业务量_万件，统计期收入_万元" \
  --order-by "统计期业务量_万件:desc" \
  --limit 10
```
