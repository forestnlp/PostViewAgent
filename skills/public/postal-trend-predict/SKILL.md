---
name: postal-trend-predict
description: 邮政经营趋势预测技能 - 流失风险预警、What-if仿真分析、收入趋势预测
---
# 邮政趋势预测技能 (postal-trend-predict)

## 概述

本技能用于对邮政寄递业务进行预测性分析，包括客户流失风险预警、What-if仿真分析和收入趋势预测。

## 核心能力

- **流失风险预警**：识别连续减收的高危客户，按风险等级分类
- **What-if仿真分析**：模拟行业下滑/客户挽回等场景，评估收入影响和客户等级变化
- **趋势预测**：基于同比增速和环比趋势，预测下月收入区间

## 数据源

- **数据文件**: `/mnt/skills/public/postal-data-query/data/商企客户业务数据_演示版.csv`
- **客户分档规则**: `/mnt/postal-knowledge/rules/customer_tier.yaml`
- 数据包含3个月（2026-05/06/07）、6个行业、14,363条记录

## 工作流程

### 步骤 1: 理解预测需求

当用户询问趋势预测、风险预警、仿真分析时，识别：

- **分析类型**: 流失预警 / 仿真分析 / 趋势预测
- **分析维度**: 行业 / 地区 / 客户等级
- **仿真参数**: 下滑比例 / 挽回客户数 / 增长目标

### 步骤 2: 执行预测分析

#### 流失风险预警

```bash
# 全量流失风险预警
python /mnt/skills/public/postal-trend-predict/scripts/predict.py \
  --action churn_risk

# 按行业筛选
python /mnt/skills/public/postal-trend-predict/scripts/predict.py \
  --action churn_risk \
  --filter "行业一级 = '电商类'"

# 按地区筛选
python /mnt/skills/public/postal-trend-predict/scripts/predict.py \
  --action churn_risk \
  --filter "地市区划名称 = '武汉市'"
```

#### What-if仿真分析

```bash
# 行业下滑仿真：电商类下滑10%
python /mnt/skills/public/postal-trend-predict/scripts/predict.py \
  --action what_if \
  --scenario industry_decline \
  --industry "电商类" \
  --decline-rate 0.10

# 客户挽回仿真：挽回TOP10减收客户
python /mnt/skills/public/postal-trend-predict/scripts/predict.py \
  --action what_if \
  --scenario customer_recover \
  --top-n 10

# 增长目标仿真：国际类增长20%
python /mnt/skills/public/postal-trend-predict/scripts/predict.py \
  --action what_if \
  --scenario growth_target \
  --industry "国际类" \
  --growth-rate 0.20
```

#### 趋势预测

```bash
# 全量趋势预测
python /mnt/skills/public/postal-trend-predict/scripts/predict.py \
  --action trend_forecast

# 按行业预测
python /mnt/skills/public/postal-trend-predict/scripts/predict.py \
  --action trend_forecast \
  --filter "行业一级 = '电商类'"
```

## 参数说明

| 参数 | 必填 | 说明 |
|------|------|------|
| `--action` | 是 | 操作类型：`churn_risk`, `what_if`, `trend_forecast` |
| `--filter` | 否 | 筛选条件（SQL WHERE语法） |
| `--scenario` | what_if必填 | 仿真场景：`industry_decline`, `customer_recover`, `growth_target` |
| `--industry` | 场景参数 | 行业名称 |
| `--decline-rate` | 场景参数 | 下滑比例（0~1） |
| `--growth-rate` | 场景参数 | 增长比例（0~1） |
| `--top-n` | 场景参数 | TOP数量 |

## 输出说明

### 流失风险预警输出

- 🔴 高危：连续3月减收且7月收入=0（已流失）
- 🟠 中危：连续3月减收且减收幅度>50%
- 🟡 低危：连续2月减收
- 🟢 正常：无连续减收

### What-if仿真输出

- 场景描述
- 收入影响金额
- 影响客户数
- 客户等级迁移情况（升级/降级/持平）
- 整体收入影响百分比

### 趋势预测输出

- 下月收入预测区间（乐观/中性/保守）
- 预测置信度（低/中/高）
- 趋势判断（上升/持平/下降）
- 预测依据

## 注意事项

- **数据仅3个月，趋势预测置信度标注为"低"或"中"，不可作为精确预测**
- 流失预警基于真实减收数据，可靠性最高
- What-if仿真是确定性数学计算，结果100%准确
- 对比期是去年同期数据（同比），不是上个月（环比）
- 客户分档规则来自 customer_tier.yaml（5档：钻石/一级/二级/三级/小微）

## 与其他技能的协同

```
用户提问："预测8月电商类收入，并模拟下滑10%的影响"

智能体编排：
  1. postal-data-query → 查5/6/7月电商类数据
  2. postal-trend-predict --action trend_forecast → 预测8月
  3. postal-trend-predict --action what_if → 仿真下滑10%
  4. read_file customer_tier.yaml → 判断客户等级影响
  5. 生成综合分析报告
```
