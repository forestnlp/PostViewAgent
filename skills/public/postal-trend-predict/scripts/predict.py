#!/usr/bin/env python3
"""邮政趋势预测技能 - 流失预警/What-if仿真/趋势预测"""

import argparse
import os
import sys
import duckdb
import pandas as pd
import yaml

# 数据文件路径
SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_FILE = os.path.join(SKILL_DIR, "data", "商企客户业务数据_演示版.csv")
TIER_RULE_FILE = "/mnt/postal-knowledge/rules/customer_tier.yaml"

# 本地开发时的fallback路径
if not os.path.exists(TIER_RULE_FILE):
    alt_paths = [
        "/home/bigmodel/deeplab/PostViewAgent/项目资料/知识库/rules/customer_tier.yaml",
        os.path.join(os.path.dirname(SKILL_DIR), "..", "..", "..", "..",
                     "项目资料", "知识库", "rules", "customer_tier.yaml"),
    ]
    for p in alt_paths:
        p = os.path.normpath(p)
        if os.path.exists(p):
            TIER_RULE_FILE = p
            break


def get_con():
    """获取DuckDB连接"""
    if not os.path.exists(DATA_FILE):
        print(f"错误：数据文件不存在：{DATA_FILE}")
        sys.exit(1)
    con = duckdb.connect()
    con.execute(f"CREATE OR REPLACE TABLE postal_customers AS SELECT * FROM read_csv_auto('{DATA_FILE}', header=true)")
    return con


def load_tier_rules():
    """加载客户分档规则"""
    if not os.path.exists(TIER_RULE_FILE):
        print(f"警告：客户分档规则文件不存在：{TIER_RULE_FILE}，使用默认规则")
        return [
            {"档位": "特级大客户", "收入区间下限": 50000, "简称": "钻石"},
            {"档位": "一级大客户", "收入区间下限": 10000},
            {"档位": "二级大客户", "收入区间下限": 5000},
            {"档位": "三级大客户", "收入区间下限": 1000},
            {"档位": "小微客户", "收入区间下限": 0},
        ]
    with open(TIER_RULE_FILE, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    return data.get("分档", [])


def get_tier(revenue_wan):
    """根据收入(万元)判定客户等级"""
    if pd.isna(revenue_wan):
        return "未知"
    revenue_yuan = revenue_wan * 10000  # 万元转元
    if revenue_yuan >= 50000:
        return "钻石"
    elif revenue_yuan >= 10000:
        return "铂金"
    elif revenue_yuan >= 5000:
        return "黄金"
    elif revenue_yuan >= 1000:
        return "白银"
    else:
        return "小微"


# ============================================================
# 功能1：流失风险预警
# ============================================================
def action_churn_risk(filter_expr=None):
    """流失风险预警：识别连续减收的高危客户"""
    con = get_con()

    where_clause = f"WHERE {filter_expr}" if filter_expr else ""

    print("=" * 70)
    print("邮政客户流失风险预警报告")
    print("=" * 70)

    # 1. 整体概览
    print("\n【一、整体概览】")
    overview = con.execute(f"""
        SELECT 
            COUNT(DISTINCT 法定客户名称) as 总客户数,
            COUNT(DISTINCT CASE WHEN 月份 = '2026-07' THEN 法定客户名称 END) as jul_active_customers
        FROM postal_customers
        {where_clause}
    """).df()
    print(overview.to_string(index=False))

    # 2. 高危客户：连续3月减收且7月收入=0
    print("\n【二、🔴 高危客户（连续3月同比减收且7月收入为0 — 已流失）】")
    high_risk = con.execute(f"""
        WITH churned AS (
            SELECT 法定客户名称
            FROM postal_customers
            {where_clause if where_clause else "WHERE 1=1"}
            GROUP BY 法定客户名称
            HAVING COUNT(DISTINCT 月份) = 3
               AND COUNT(DISTINCT CASE WHEN 统计期收入_万元 < 对比期收入_万元 THEN 月份 END) = 3
               AND MAX(CASE WHEN 月份 = '2026-07' THEN 统计期收入_万元 ELSE 0 END) = 0
        )
        SELECT 
            c.法定客户名称,
            c.行业一级,
            c.区县区划名称,
            ROUND(SUM(c.对比期收入_万元 - c.统计期收入_万元), 2) as 累计流失收入_万元,
            ROUND(SUM(c.对比期收入_万元), 2) as 去年同期收入_万元,
            ROUND(SUM(c.统计期收入_万元), 2) as 今年收入_万元
        FROM postal_customers c
        WHERE c.法定客户名称 IN (SELECT 法定客户名称 FROM churned)
        GROUP BY c.法定客户名称, c.行业一级, c.区县区划名称
        ORDER BY 累计流失收入_万元 DESC
        LIMIT 20
    """).df()

    if len(high_risk) > 0:
        high_count = con.execute(f"""
            WITH churned AS (
                SELECT 法定客户名称
                FROM postal_customers
                {where_clause if where_clause else "WHERE 1=1"}
                GROUP BY 法定客户名称
                HAVING COUNT(DISTINCT 月份) = 3
                   AND COUNT(DISTINCT CASE WHEN 统计期收入_万元 < 对比期收入_万元 THEN 月份 END) = 3
                   AND MAX(CASE WHEN 月份 = '2026-07' THEN 统计期收入_万元 ELSE 0 END) = 0
            )
            SELECT COUNT(*) as cnt FROM churned
        """).df()
        print(f"高危客户总数：{high_count.iloc[0, 0]}个")
        print(f"累计流失收入：{high_risk['累计流失收入_万元'].sum():.2f}万元")
        print(f"\nTOP 20 高危客户：")
        print(high_risk.to_string(index=False))
    else:
        print("无高危客户")

    # 3. 中危客户：连续3月减收且减收>50%
    print("\n【三、🟠 中危客户（连续3月同比减收且累计减收>50%）】")
    medium_risk = con.execute(f"""
        WITH medium AS (
            SELECT 法定客户名称
            FROM postal_customers
            {where_clause if where_clause else "WHERE 1=1"}
            GROUP BY 法定客户名称
            HAVING COUNT(DISTINCT 月份) = 3
               AND COUNT(DISTINCT CASE WHEN 统计期收入_万元 < 对比期收入_万元 THEN 月份 END) = 3
               AND SUM(对比期收入_万元) > 0
               AND (SUM(对比期收入_万元) - SUM(统计期收入_万元)) / SUM(对比期收入_万元) > 0.5
               AND MAX(CASE WHEN 月份 = '2026-07' THEN 统计期收入_万元 ELSE 0 END) > 0
        )
        SELECT 
            c.法定客户名称,
            c.行业一级,
            c.区县区划名称,
            ROUND(SUM(c.对比期收入_万元), 2) as 去年同期收入,
            ROUND(SUM(c.统计期收入_万元), 2) as 今年收入,
            ROUND((SUM(c.对比期收入_万元) - SUM(c.统计期收入_万元)) / SUM(c.对比期收入_万元) * 100, 1) as 减收率_pct
        FROM postal_customers c
        WHERE c.法定客户名称 IN (SELECT 法定客户名称 FROM medium)
        GROUP BY c.法定客户名称, c.行业一级, c.区县区划名称
        ORDER BY 减收率_pct DESC
        LIMIT 20
    """).df()

    if len(medium_risk) > 0:
        medium_count = con.execute(f"""
            WITH medium AS (
                SELECT 法定客户名称
                FROM postal_customers
                {where_clause if where_clause else "WHERE 1=1"}
                GROUP BY 法定客户名称
                HAVING COUNT(DISTINCT 月份) = 3
                   AND COUNT(DISTINCT CASE WHEN 统计期收入_万元 < 对比期收入_万元 THEN 月份 END) = 3
                   AND SUM(对比期收入_万元) > 0
                   AND (SUM(对比期收入_万元) - SUM(统计期收入_万元)) / SUM(对比期收入_万元) > 0.5
                   AND MAX(CASE WHEN 月份 = '2026-07' THEN 统计期收入_万元 ELSE 0 END) > 0
            )
            SELECT COUNT(*) as cnt FROM medium
        """).df()
        print(f"中危客户总数：{medium_count.iloc[0, 0]}个")
        print(f"\nTOP 20 中危客户：")
        print(medium_risk.to_string(index=False))
    else:
        print("无中危客户")

    # 4. 低危客户：连续2月减收
    print("\n【四、🟡 低危客户（连续2月同比减收）】")
    low_count = con.execute(f"""
        WITH low AS (
            SELECT 法定客户名称
            FROM postal_customers
            {where_clause if where_clause else "WHERE 1=1"}
            AND 月份 IN ('2026-06', '2026-07')
            GROUP BY 法定客户名称
            HAVING COUNT(DISTINCT CASE WHEN 统计期收入_万元 < 对比期收入_万元 THEN 月份 END) = 2
        )
        SELECT COUNT(*) as cnt FROM low
    """).df()
    print(f"低危客户总数：{low_count.iloc[0, 0]}个")

    # 5. 行业分布
    print("\n【五、风险客户行业分布】")
    industry_dist = con.execute(f"""
        WITH risk_customers AS (
            SELECT DISTINCT c.法定客户名称, c.行业一级
            FROM postal_customers c
            WHERE c.法定客户名称 IN (
                SELECT 法定客户名称
                FROM postal_customers
                {where_clause if where_clause else "WHERE 1=1"}
                GROUP BY 法定客户名称
                HAVING COUNT(DISTINCT 月份) = 3
                   AND COUNT(DISTINCT CASE WHEN 统计期收入_万元 < 对比期收入_万元 THEN 月份 END) >= 2
            )
        )
        SELECT 行业一级, COUNT(*) as 风险客户数
        FROM risk_customers
        GROUP BY 行业一级
        ORDER BY 风险客户数 DESC
    """).df()
    print(industry_dist.to_string(index=False))

    # 6. 区县分布
    print("\n【六、风险客户区县分布】")
    region_dist = con.execute(f"""
        WITH risk_customers AS (
            SELECT DISTINCT c.法定客户名称, c.区县区划名称
            FROM postal_customers c
            WHERE c.法定客户名称 IN (
                SELECT 法定客户名称
                FROM postal_customers
                {where_clause if where_clause else "WHERE 1=1"}
                GROUP BY 法定客户名称
                HAVING COUNT(DISTINCT 月份) = 3
                   AND COUNT(DISTINCT CASE WHEN 统计期收入_万元 < 对比期收入_万元 THEN 月份 END) >= 2
            )
        )
        SELECT 区县区划名称, COUNT(*) as 风险客户数
        FROM risk_customers
        GROUP BY 区县区划名称
        ORDER BY 风险客户数 DESC
        LIMIT 15
    """).df()
    print(region_dist.to_string(index=False))

    print("\n" + "=" * 70)
    print("说明：对比期为去年同期数据（同比），非上月（环比）")
    print("数据来源：邮政经营数据查询技能（2026年5-7月）")
    print("=" * 70)


# ============================================================
# 功能2：What-if仿真分析
# ============================================================
def action_what_if(scenario, industry=None, decline_rate=None,
                   growth_rate=None, top_n=10, filter_expr=None):
    """What-if仿真分析"""
    con = get_con()
    tiers = load_tier_rules()

    print("=" * 70)
    print("What-if 仿真分析报告")
    print("=" * 70)

    # 获取7月最新数据作为基准
    where_clause = f"AND {filter_expr}" if filter_expr else ""

    if scenario == "industry_decline":
        if not industry or decline_rate is None:
            print("错误：industry_decline场景需要 --industry 和 --decline-rate 参数")
            sys.exit(1)

        print(f"\n【场景：{industry}收入下滑{decline_rate*100:.0f}%】")
        print(f"基准月份：2026年7月")

        # 当前收入
        baseline = con.execute(f"""
            SELECT 
                COUNT(DISTINCT 法定客户名称) as 客户数,
                ROUND(SUM(统计期收入_万元), 2) as 当前收入_万元,
                ROUND(SUM(统计期业务量_万件), 2) as 当前业务量_万件
            FROM postal_customers
            WHERE 月份 = '2026-07' AND 行业一级 = '{industry}'
            {where_clause.replace('AND', 'AND', 1) if where_clause else ''}
        """).df()
        print(f"\n基准数据：")
        print(baseline.to_string(index=False))

        current_revenue = baseline.iloc[0, 1]
        revenue_loss = current_revenue * decline_rate
        new_revenue = current_revenue * (1 - decline_rate)

        print(f"\n仿真结果：")
        print(f"  收入减少：{revenue_loss:.2f}万元")
        print(f"  仿真后收入：{new_revenue:.2f}万元")

        # 客户等级迁移分析
        print(f"\n【客户等级迁移分析】")
        tier_migration = con.execute(f"""
            WITH customer_revenue AS (
                SELECT 
                    法定客户名称,
                    统计期收入_万元 as 当前收入,
                    统计期收入_万元 * (1 - {decline_rate}) as 仿真收入
                FROM postal_customers
                WHERE 月份 = '2026-07' AND 行业一级 = '{industry}'
            )
            SELECT 
                CASE 
                    WHEN 当前收入 * 10000 >= 50000 THEN '钻石'
                    WHEN 当前收入 * 10000 >= 10000 THEN '铂金'
                    WHEN 当前收入 * 10000 >= 5000 THEN '黄金'
                    WHEN 当前收入 * 10000 >= 1000 THEN '白银'
                    ELSE '小微'
                END as 当前等级,
                CASE 
                    WHEN 仿真收入 * 10000 >= 50000 THEN '钻石'
                    WHEN 仿真收入 * 10000 >= 10000 THEN '铂金'
                    WHEN 仿真收入 * 10000 >= 5000 THEN '黄金'
                    WHEN 仿真收入 * 10000 >= 1000 THEN '白银'
                    ELSE '小微'
                END as 仿真等级,
                COUNT(*) as 客户数,
                ROUND(SUM(当前收入), 2) as 当前收入合计,
                ROUND(SUM(仿真收入), 2) as 仿真收入合计
            FROM customer_revenue
            GROUP BY 当前等级, 仿真等级
            ORDER BY 当前等级, 仿真等级
        """).df()

        # 统计迁移情况
        upgraded = tier_migration[tier_migration['当前等级'] < tier_migration['仿真等级']]
        downgraded = tier_migration[tier_migration['当前等级'] > tier_migration['仿真等级']]
        unchanged = tier_migration[tier_migration['当前等级'] == tier_migration['仿真等级']]

        print(f"  ⬆️ 升级客户：{upgraded['客户数'].sum() if len(upgraded) > 0 else 0}个")
        print(f"  ⬇️ 降级客户：{downgraded['客户数'].sum() if len(downgraded) > 0 else 0}个")
        print(f"  ➡️ 持平客户：{unchanged['客户数'].sum() if len(unchanged) > 0 else 0}个")
        print(f"\n  等级迁移明细：")
        print(tier_migration.to_string(index=False))

        # 整体影响
        total_revenue = con.execute("""
            SELECT ROUND(SUM(统计期收入_万元), 2) as 总收入
            FROM postal_customers WHERE 月份 = '2026-07'
        """).df().iloc[0, 0]
        impact_pct = revenue_loss / total_revenue * 100
        print(f"\n【整体影响】")
        print(f"  全行业7月总收入：{total_revenue:.2f}万元")
        print(f"  仿真收入减少：{revenue_loss:.2f}万元")
        print(f"  整体收入影响：-{impact_pct:.1f}%")

    elif scenario == "customer_recover":
        print(f"\n【场景：挽回TOP{top_n}减收客户】")
        print(f"基准月份：2026年5-7月")

        # 找到TOP N减收客户
        top_loss = con.execute(f"""
            SELECT 
                法定客户名称,
                行业一级,
                ROUND(SUM(对比期收入_万元 - 统计期收入_万元), 2) as 累计减收_万元,
                ROUND(SUM(统计期收入_万元), 2) as 今年收入,
                ROUND(SUM(对比期收入_万元), 2) as 去年同期收入
            FROM postal_customers
            {where_clause if where_clause else "WHERE 1=1"}
            GROUP BY 法定客户名称, 行业一级
            HAVING 累计减收_万元 > 0
            ORDER BY 累计减收_万元 DESC
            LIMIT {int(top_n)}
        """).df()

        print(f"\nTOP{top_n}减收客户：")
        print(top_loss.to_string(index=False))

        total_recoverable = top_loss['累计减收_万元'].sum()
        print(f"\n仿真结果：")
        print(f"  可挽回收入：{total_recoverable:.2f}万元")
        print(f"  涉及客户：{len(top_loss)}个")
        print(f"  涉及行业：{top_loss['行业一级'].unique().tolist()}")

        # 行业分布
        print(f"\n【挽回收入行业分布】")
        industry_recover = top_loss.groupby('行业一级')['累计减收_万元'].sum().reset_index()
        industry_recover.columns = ['行业一级', '可挽回收入_万元']
        industry_recover = industry_recover.sort_values('可挽回收入_万元', ascending=False)
        print(industry_recover.to_string(index=False))

    elif scenario == "growth_target":
        if not industry or growth_rate is None:
            print("错误：growth_target场景需要 --industry 和 --growth-rate 参数")
            sys.exit(1)

        print(f"\n【场景：{industry}增长{growth_rate*100:.0f}%】")
        print(f"基准月份：2026年7月")

        baseline = con.execute(f"""
            SELECT 
                COUNT(DISTINCT 法定客户名称) as 客户数,
                ROUND(SUM(统计期收入_万元), 2) as 当前收入_万元,
                ROUND(AVG(统计期收入_万元), 2) as 客均收入_万元
            FROM postal_customers
            WHERE 月份 = '2026-07' AND 行业一级 = '{industry}'
        """).df()
        print(f"\n基准数据：")
        print(baseline.to_string(index=False))

        current_revenue = baseline.iloc[0, 1]
        target_revenue = current_revenue * (1 + growth_rate)
        revenue_gain = current_revenue * growth_rate
        avg_revenue = baseline.iloc[0, 2]
        customer_count = baseline.iloc[0, 0]

        print(f"\n仿真结果：")
        print(f"  目标收入：{target_revenue:.2f}万元")
        print(f"  需增加收入：{revenue_gain:.2f}万元")
        if avg_revenue > 0:
            new_customers = revenue_gain / avg_revenue
            print(f"  客均收入：{avg_revenue:.2f}万元")
            print(f"  需新增客户数（按客均计算）：{new_customers:.0f}个")
        print(f"  当前客户数：{customer_count}个")
        if customer_count > 0:
            print(f"  或每个客户需增收：{revenue_gain/customer_count:.2f}万元（+{growth_rate*100:.0f}%）")

    else:
        print(f"错误：不支持的场景：{scenario}")
        print(f"支持的场景：industry_decline, customer_recover, growth_target")
        sys.exit(1)

    print("\n" + "=" * 70)
    print("说明：What-if仿真为确定性数学计算，结果100%准确")
    print("客户分档规则来源：customer_tier.yaml")
    print("=" * 70)


# ============================================================
# 功能3：趋势预测
# ============================================================
def action_trend_forecast(filter_expr=None):
    """趋势预测：基于同比增速和环比趋势预测下月收入"""
    con = get_con()

    where_clause = f"AND {filter_expr}" if filter_expr else ""

    print("=" * 70)
    print("邮政经营趋势预测报告")
    print("=" * 70)
    print(f"预测目标：2026年8月")
    print(f"数据基础：2026年5-7月（3个月）")

    # 按行业一级统计月度收入
    print("\n【一、各行业月度收入趋势】")
    monthly = con.execute(f"""
        SELECT 
            行业一级,
            ROUND(SUM(CASE WHEN 月份 = '2026-05' THEN 统计期收入_万元 ELSE 0 END), 2) as may_revenue,
            ROUND(SUM(CASE WHEN 月份 = '2026-06' THEN 统计期收入_万元 ELSE 0 END), 2) as jun_revenue,
            ROUND(SUM(CASE WHEN 月份 = '2026-07' THEN 统计期收入_万元 ELSE 0 END), 2) as jul_revenue,
            ROUND(SUM(CASE WHEN 月份 = '2026-05' THEN 对比期收入_万元 ELSE 0 END), 2) as may_compare,
            ROUND(SUM(CASE WHEN 月份 = '2026-06' THEN 对比期收入_万元 ELSE 0 END), 2) as jun_compare,
            ROUND(SUM(CASE WHEN 月份 = '2026-07' THEN 对比期收入_万元 ELSE 0 END), 2) as jul_compare
        FROM postal_customers
        WHERE 1=1 {where_clause}
        GROUP BY 行业一级
        ORDER BY jul_revenue DESC
    """).df()

    # 计算预测值
    results = []
    for _, row in monthly.iterrows():
        industry = row['行业一级']
        may_r = row['may_revenue']
        jun_r = row['jun_revenue']
        jul_r = row['jul_revenue']

        # 环比变化率
        mom_jun = (jun_r - may_r) / may_r * 100 if may_r > 0 else 0
        mom_jul = (jul_r - jun_r) / jun_r * 100 if jun_r > 0 else 0
        mom_avg = (mom_jun + mom_jul) / 2 if (mom_jun != 0 or mom_jul != 0) else 0

        # 同比变化率
        yoy_may = (may_r - row['may_compare']) / row['may_compare'] * 100 if row['may_compare'] > 0 else 0
        yoy_jun = (jun_r - row['jun_compare']) / row['jun_compare'] * 100 if row['jun_compare'] > 0 else 0
        yoy_jul = (jul_r - row['jul_compare']) / row['jul_compare'] * 100 if row['jul_compare'] > 0 else 0
        yoy_avg = (yoy_may + yoy_jun + yoy_jul) / 3

        # 预测8月：加权平均（环比趋势权重0.6，同比趋势权重0.4）
        forecast_rate = (mom_avg * 0.6 + yoy_avg * 0.4) / 100
        forecast_neutral = jul_r * (1 + forecast_rate)
        forecast_optimistic = jul_r * (1 + forecast_rate + 0.1)
        forecast_conservative = jul_r * (1 + forecast_rate - 0.1)

        # 趋势判断
        if mom_jul < 0 and mom_jun < 0:
            trend = "下降（连续下滑）"
            confidence = "中"
        elif mom_jul < 0:
            trend = "下降"
            confidence = "中"
        elif mom_jul > 0 and mom_jun > 0:
            trend = "上升（连续增长）"
            confidence = "中"
        elif mom_jul > 0:
            trend = "上升"
            confidence = "中"
        else:
            trend = "持平"
            confidence = "低"

        results.append({
            '行业一级': industry,
            '5月收入': may_r,
            '6月收入': jun_r,
            '7月收入': jul_r,
            '6月环比%': round(mom_jun, 1),
            '7月环比%': round(mom_jul, 1),
            '平均同比%': round(yoy_avg, 1),
            '8月预测_乐观': round(forecast_optimistic, 2),
            '8月预测_中性': round(forecast_neutral, 2),
            '8月预测_保守': round(forecast_conservative, 2),
            '趋势': trend,
            '置信度': confidence,
        })

    result_df = pd.DataFrame(results)
    print(result_df.to_string(index=False))

    # 汇总预测
    print("\n【二、8月收入预测汇总】")
    total_jul = result_df['7月收入'].sum()
    total_forecast = result_df['8月预测_中性'].sum()
    total_optimistic = result_df['8月预测_乐观'].sum()
    total_conservative = result_df['8月预测_保守'].sum()

    print(f"  7月实际总收入：{total_jul:.2f}万元")
    print(f"  8月预测总收入（乐观）：{total_optimistic:.2f}万元（{(total_optimistic/total_jul-1)*100:+.1f}%）")
    print(f"  8月预测总收入（中性）：{total_forecast:.2f}万元（{(total_forecast/total_jul-1)*100:+.1f}%）")
    print(f"  8月预测总收入（保守）：{total_conservative:.2f}万元（{(total_conservative/total_jul-1)*100:+.1f}%）")

    # 关键发现
    print("\n【三、关键发现】")
    declining = result_df[result_df['趋势'].str.contains('下降')]
    growing = result_df[result_df['趋势'].str.contains('上升')]
    if len(declining) > 0:
        print(f"  📉 下滑行业：{', '.join(declining['行业一级'].tolist())}")
    if len(growing) > 0:
        print(f"  📈 增长行业：{', '.join(growing['行业一级'].tolist())}")

    print("\n【四、预测方法说明】")
    print("  预测方法：环比趋势(权重0.6) + 同比增速(权重0.4) 加权外推")
    print("  置信度说明：")
    print("    - 低：数据波动大或趋势不明确")
    print("    - 中：有连续趋势但数据仅3个月")
    print("    - 高：需要12个月以上数据（当前不支持）")
    print("  ⚠️ 注意：3个月数据预测置信度有限，仅供参考")

    print("\n" + "=" * 70)
    print("数据来源：邮政经营数据查询技能（2026年5-7月）")
    print("对比期说明：去年同期数据（同比），非上月（环比）")
    print("=" * 70)


# ============================================================
# 主函数
# ============================================================
def main():
    parser = argparse.ArgumentParser(description='邮政趋势预测技能')
    parser.add_argument('--action', type=str, required=True,
                        choices=['churn_risk', 'what_if', 'trend_forecast'],
                        help='操作类型')
    parser.add_argument('--filter', type=str, help='筛选条件（SQL WHERE语法）')

    # what_if 参数
    parser.add_argument('--scenario', type=str,
                        choices=['industry_decline', 'customer_recover', 'growth_target'],
                        help='仿真场景')
    parser.add_argument('--industry', type=str, help='行业名称')
    parser.add_argument('--decline-rate', type=float, help='下滑比例（0~1）')
    parser.add_argument('--growth-rate', type=float, help='增长比例（0~1）')
    parser.add_argument('--top-n', type=int, default=10, help='TOP数量')

    args = parser.parse_args()

    print(f"数据引擎：DuckDB")
    print(f"数据文件：{DATA_FILE}")

    if args.action == 'churn_risk':
        action_churn_risk(filter_expr=args.filter)
    elif args.action == 'what_if':
        if not args.scenario:
            print("错误：what_if 需要 --scenario 参数")
            sys.exit(1)
        action_what_if(
            scenario=args.scenario,
            industry=args.industry,
            decline_rate=args.decline_rate,
            growth_rate=args.growth_rate,
            top_n=args.top_n,
            filter_expr=args.filter
        )
    elif args.action == 'trend_forecast':
        action_trend_forecast(filter_expr=args.filter)


if __name__ == '__main__':
    main()
