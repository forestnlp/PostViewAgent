---
name: postal-station-profit-loss
description: 邮政网点损益分析技能 - 网点经营数据查询、盈利红黑榜、亏损预警
---
# 邮政网点损益分析技能 (postal-station-profit-loss)

## 概述

本技能用于对邮政营业网点进行损益分析，包括网点经营数据查询、盈利红黑榜排名、连续亏损预警。

## 核心能力

- **数据查询**：按区/网点/月份查询网点收入、成本、利润
- **红黑榜**：基于营业利润/利润总额，输出盈利 TOP10 和亏损 TOP10
- **亏损预警**：识别连续亏损网点，按风险等级分类（高危/中危/低危）
- **趋势分析**：展示指定指标的单月月度趋势 + 环比变化
- **What-if仿真**：成本降低/收入增长对利润的影响

## 数据源

- **数据文件**: `/mnt/skills/public/postal-station-profit-loss/data/station_profit_loss_202501_202606.csv`
- 数据包含 18 个月（2025-01 ~ 2026-06）、13 个区公司、263 个网点、4717 条记录
- 字段：网点代码、网点名称、company（区公司）、region（区名）、period、收入14项、成本19项、营业利润、利润总额、单月差分值

## 工作流程

### 步骤 1: 理解查询需求

当用户询问网点损益时，识别：

- **操作类型**: query（查询）/ ranking（红黑榜）/ alert（预警）
- **分析维度**: 区 / 网点 / 月份
- **指标**: 收入 / 成本 / 营业利润 / 利润总额

### 步骤 2: 执行分析

#### 数据查询

```bash
# 查询某区某月网点数据
python /mnt/skills/public/postal-station-profit-loss/scripts/station_profit_loss.py \
  --action query \
  --region "武昌区" \
  --period "2026-06"

# 查询某网点全部月份
python /mnt/skills/public/postal-station-profit-loss/scripts/station_profit_loss.py \
  --action query \
  --station "吴家山支局"
```

#### 红黑榜

```bash
# 某月盈利 TOP10 / 亏损 TOP10
python /mnt/skills/public/postal-station-profit-loss/scripts/station_profit_loss.py \
  --action ranking \
  --period "2026-06" \
  --type both \
  --top-n 10

# 某区某月红黑榜
python /mnt/skills/public/postal-station-profit-loss/scripts/station_profit_loss.py \
  --action ranking \
  --region "武昌区" \
  --period "2026-06" \
  --type both
```

#### 亏损预警

```bash
# 连续3个月亏损预警
python /mnt/skills/public/postal-station-profit-loss/scripts/station_profit_loss.py \
  --action alert \
  --months 3

# 某区连续亏损预警
python /mnt/skills/public/postal-station-profit-loss/scripts/station_profit_loss.py \
  --action alert \
  --region "武昌区" \
  --months 3
```

#### 趋势分析

```bash
# 某区公司营业利润月度趋势
python /mnt/skills/public/postal-station-profit-loss/scripts/station_profit_loss.py \
  --action trend \
  --company "13武汉东西湖区" \
  --metric "营业利润"

# 某网点收入趋势
python /mnt/skills/public/postal-station-profit-loss/scripts/station_profit_loss.py \
  --action trend \
  --station "吴家山支局" \
  --metric "业务总收入"
```

#### What-if仿真

```bash
# 人工成本降10%对利润的影响
python /mnt/skills/public/postal-station-profit-loss/scripts/station_profit_loss.py \
  --action simulation \
  --company "13武汉东西湖区" \
  --period "2026-06" \
  --cost-type "人工成本" \
  --cost-reduction 0.1

# 收入增长20%对利润的影响
python /mnt/skills/public/postal-station-profit-loss/scripts/station_profit_loss.py \
  --action simulation \
  --region "武昌区" \
  --period "2026-06" \
  --revenue-growth 0.2
```

## 参数说明

| 参数 | 必填 | 说明 |
|------|------|------|
| `--action` | 是 | 操作类型：`query`, `ranking`, `alert`, `trend`, `simulation` |
| `--region` | 否 | 区名（如"武昌区"） |
| `--company` | 否 | 区公司（如"13武汉东西湖区"） |
| `--station` | 否 | 网点名称（如"吴家山支局"） |
| `--period` | 否 | 月份（如"2026-06"） |
| `--type` | ranking | 红黑榜类型：`red`（盈利）/ `black`（亏损）/ `both` |
| `--top-n` | 否 | TOP 数量（默认 10） |
| `--months` | alert | 连续亏损月数（默认 3） |
| `--metric` | trend | 趋势指标（业务总收入/营业利润/利润总额） |
| `--cost-type` | simulation | 成本项（人工成本/租赁成本/运输成本等） |
| `--cost-reduction` | simulation | 成本降低比例（0~1） |
| `--revenue-growth` | simulation | 收入增长比例（0~1） |

## 输出说明

### 红黑榜输出

- 红榜：营业利润排名 TOP10（盈利）
- 黑榜：营业利润排名后 10（亏损最多）
- 附带智能洞察（红榜平均利润、黑榜平均利润）

### 亏损预警输出

- 🔴 高危：连续3个月亏损且累计亏损 > 10万
- 🟠 中危：连续3个月亏损
- 🟡 低危：连续2个月亏损

## 注意事项

- **累计口径**：原始数据为"本年累计"，已差分出单月值（`营业利润_单月`）
- 红黑榜基于**单月营业利润**（`营业利润_单月`），反映当月经营
- 亏损预警基于**单月营业利润**连续为负
- 数据为静态数据，不包含实时更新

## 与其他技能的协同

```
用户提问："2026年6月哪些网点连续3个月亏损？"

智能体编排：
  1. postal-station-profit-loss --action alert --months 3 → 亏损预警
  2. postal-station-profit-loss --action ranking --period 2026-06 → 红黑榜
  3. 生成综合分析报告
```
