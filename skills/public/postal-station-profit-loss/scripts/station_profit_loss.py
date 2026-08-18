#!/usr/bin/env python3
"""
邮政网点损益分析脚本
====================
支持：query（数据查询）、ranking（红黑榜）、alert（亏损预警）

数据源：station_profit_loss_202501_202606.csv（18个月×13区×263网点）
"""
import argparse
import sys
from pathlib import Path

import pandas as pd

# 数据文件路径
DATA_FILE = Path(__file__).parent.parent / "data" / "station_profit_loss_202501_202606.csv"

# 关键指标列
REVENUE_COLS = ["业务总收入", "代理金融收入", "寄递业务收入", "函件收入", "报刊收入", "集邮收入"]
COST_COLS = ["业务总成本", "主营业务成本", "管理费用", "人工成本", "租赁成本", "运输成本"]
PROFIT_COLS = ["营业利润", "利润总额"]


def load_data() -> pd.DataFrame:
    """加载网点损益数据"""
    if not DATA_FILE.exists():
        print(f"❌ 数据文件不存在：{DATA_FILE}")
        sys.exit(1)
    df = pd.read_csv(DATA_FILE)
    # 数值列转数值类型
    for col in REVENUE_COLS + COST_COLS + PROFIT_COLS + ["营业利润_单月", "利润总额_单月", "业务总收入_单月"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    return df


def action_query(df: pd.DataFrame, region=None, station=None, period=None, company=None):
    """数据查询：按区/网点/月份/区公司筛选"""
    result = df.copy()
    if region:
        result = result[result["region"] == region]
    if station:
        result = result[result["网点名称"] == station]
    if period:
        result = result[result["period"] == period]
    if company:
        result = result[result["company"] == company]

    if result.empty:
        print("⚠️ 未找到匹配数据")
        return []

    # 选择展示列
    show_cols = ["period", "company", "region", "网点代码", "网点名称", "业务总收入", "营业利润", "利润总额"]
    show_cols = [c for c in show_cols if c in result.columns]
    result = result[show_cols].sort_values(["period", "营业利润"], ascending=[True, False])

    print(f"\n查询结果（{len(result)} 条记录）")
    print("=" * 70)
    pd.set_option("display.max_columns", None)
    pd.set_option("display.width", None)
    print(result.to_string(index=False))
    return result.to_dict("records")


def action_ranking(df: pd.DataFrame, region=None, period=None, rank_type="both", top_n=10, company=None):
    """红黑榜：基于单月营业利润排名"""
    # 使用单月营业利润
    profit_col = "营业利润_单月" if "营业利润_单月" in df.columns else "营业利润"
    result = df.copy()
    if region:
        result = result[result["region"] == region]
    if period:
        result = result[result["period"] == period]
    if company:
        result = result[result["company"] == company]

    if result.empty:
        print("⚠️ 未找到匹配数据")
        return {}

    # 按单月营业利润排序
    result = result.sort_values(profit_col, ascending=False)

    output = {}
    if rank_type in ("red", "both"):
        # 红榜：只显示盈利网点，利润最高的排最前
        red = result[result[profit_col] > 0].sort_values(profit_col, ascending=False).head(top_n)
        print(f"\n🔴 红榜（盈利 TOP{top_n}）")
        print("=" * 70)
        if red.empty:
            print("（该范围无盈利网点）")
        else:
            print(red[["period", "company", "region", "网点名称", profit_col]].to_string(index=False))
        output["red"] = red[["period", "company", "region", "网点名称", profit_col]].to_dict("records")

    if rank_type in ("black", "both"):
        # 黑榜：只显示亏损网点，最亏损的排最前（营业利润升序取前N）
        black = result[result[profit_col] < 0].sort_values(profit_col, ascending=True).head(top_n)
        print(f"\n⚫ 黑榜（亏损 TOP{top_n}）")
        print("=" * 70)
        if black.empty:
            print("（该范围无亏损网点）")
        else:
            print(black[["period", "company", "region", "网点名称", profit_col]].to_string(index=False))
        output["black"] = black[["period", "company", "region", "网点名称", profit_col]].to_dict("records")

    # 智能洞察（基于实际显示的红黑榜）
    if rank_type in ("red", "both") and not red.empty:
        red_avg = red[profit_col].mean()
        print(f"\n💡 洞察：红榜网点平均单月营业利润 {red_avg:.0f} 元")
    if rank_type in ("black", "both") and not black.empty:
        black_avg = black[profit_col].mean()
        print(f"💡 洞察：黑榜网点平均单月营业利润 {black_avg:.0f} 元")

    return output


def action_alert(df: pd.DataFrame, region=None, months=3, company=None):
    """亏损预警：连续N月单月营业利润为负"""
    profit_col = "营业利润_单月" if "营业利润_单月" in df.columns else "营业利润"
    result = df.copy()
    if region:
        result = result[result["region"] == region]
    if company:
        result = result[result["company"] == company]

    if result.empty:
        print("⚠️ 未找到匹配数据")
        return []

    # 按网点分组，检查连续亏损
    alerts = []
    for code, group in result.groupby("网点代码"):
        group = group.sort_values("period")
        name = group["网点名称"].iloc[0]
        region_name = group["region"].iloc[0]
        profits = group[profit_col].tolist()
        periods = group["period"].tolist()

        # 从最新月份往前数连续亏损月数
        consecutive = 0
        for p in reversed(profits):
            if p < 0:
                consecutive += 1
            else:
                break

        if consecutive >= 2:
            # 累计亏损（最近连续亏损月的累计）
            cum_loss = sum(p for p in profits[-consecutive:] if p < 0)
            if consecutive >= 3 and cum_loss < -100000:
                level = "高危"
            elif consecutive >= 3:
                level = "中危"
            else:
                level = "低危"
            # 按最小连续亏损月数过滤
            if consecutive >= months:
                alerts.append({
                    "网点代码": code,
                    "网点名称": name,
                    "region": region_name,
                    "连续亏损月数": consecutive,
                    "累计亏损": round(cum_loss, 2),
                    "预警等级": level,
                    "最新月份": periods[-1],
                })

    if not alerts:
        print(f"✅ 无连续 {months} 个月亏损的网点")
        return []

    # 按等级排序
    level_order = {"高危": 0, "中危": 1, "低危": 2}
    alerts.sort(key=lambda x: level_order.get(x["预警等级"], 3))

    print(f"\n⚠️ 亏损预警（至少连续 {months} 个月亏损）")
    print("=" * 70)
    for a in alerts:
        icon = {"高危": "🔴", "中危": "🟠", "低危": "🟡"}.get(a["预警等级"], "🟢")
        print(f"{icon} [{a['预警等级']}] {a['网点名称']}（{a['region']}）"
              f"连续{a['连续亏损月数']}月亏损，累计亏损{a['累计亏损']:.0f}元")
    return alerts


def action_trend(df: pd.DataFrame, region=None, company=None, station=None, metric="营业利润"):
    """趋势分析：展示指定指标的单月月度趋势 + 环比变化"""
    # 单月指标列
    metric_month = f"{metric}_单月"
    if metric_month not in df.columns:
        print(f"⚠️ 指标 {metric} 无单月差分值，可用：业务总收入/营业利润/利润总额")
        return []

    result = df.copy()
    if region:
        result = result[result["region"] == region]
    if company:
        result = result[result["company"] == company]
    if station:
        result = result[result["网点名称"] == station]

    if result.empty:
        print("⚠️ 未找到匹配数据")
        return []

    # 按期间聚合单月指标
    trend = result.groupby("period")[metric_month].sum().reset_index()
    trend = trend.sort_values("period")

    # 计算环比变化
    trend["环比变化"] = trend[metric_month].diff()
    trend["环比变化率%"] = (trend[metric_month].pct_change() * 100).round(1)

    print(f"\n📈 {metric} 月度趋势（单月值）")
    print("=" * 70)
    pd.set_option("display.max_columns", None)
    pd.set_option("display.width", None)
    print(trend.to_string(index=False))

    # 趋势判断
    if len(trend) >= 3:
        recent = trend[metric_month].tail(3).tolist()
        if recent[2] > recent[1] > recent[0]:
            trend_dir = "上升（连续增长）"
        elif recent[2] < recent[1] < recent[0]:
            trend_dir = "下降（连续下滑）"
        elif recent[2] > recent[1]:
            trend_dir = "上升"
        elif recent[2] < recent[1]:
            trend_dir = "下降"
        else:
            trend_dir = "持平"
        print(f"\n💡 趋势判断：{trend_dir}")

    return trend.to_dict("records")


def action_simulation(df: pd.DataFrame, region=None, company=None, period=None,
                      cost_type=None, cost_reduction=None, revenue_growth=None):
    """What-if仿真：成本降低/收入增长对利润的影响"""
    result = df.copy()
    if region:
        result = result[result["region"] == region]
    if company:
        result = result[result["company"] == company]
    if period:
        result = result[result["period"] == period]

    if result.empty:
        print("⚠️ 未找到匹配数据")
        return {}

    # 使用累计口径（成本项只有累计值，统一用累计口径保证一致）
    profit_col = "营业利润"
    revenue_col = "业务总收入"

    total_profit = result[profit_col].sum()
    total_revenue = result[revenue_col].sum()

    print(f"\n🔮 What-if 仿真分析（累计口径）")
    print("=" * 70)
    print(f"基准：{len(result)} 个网点")
    print(f"  累计营业利润合计：{total_profit:.0f} 元")
    print(f"  累计业务总收入合计：{total_revenue:.0f} 元")

    output = {"基准营业利润": round(total_profit, 2), "基准收入": round(total_revenue, 2)}

    # 场景1：成本降低
    if cost_type and cost_reduction is not None:
        if cost_type not in result.columns:
            print(f"⚠️ 成本项 {cost_type} 不存在，可用：人工成本/租赁成本/运输成本/管理费用/业务总成本")
            return output
        cost_total = result[cost_type].sum()
        cost_save = cost_total * cost_reduction
        new_profit = total_profit + cost_save
        print(f"\n【场景1：{cost_type} 降低 {cost_reduction*100:.0f}%】")
        print(f"  {cost_type}合计：{cost_total:.0f} 元")
        print(f"  成本节省：{cost_save:.0f} 元")
        print(f"  仿真后营业利润：{new_profit:.0f} 元（+{cost_save:.0f}）")
        output["成本降低"] = {
            "成本项": cost_type,
            "降低比例": cost_reduction,
            "成本节省": round(cost_save, 2),
            "仿真后利润": round(new_profit, 2),
        }

    # 场景2：收入增长
    if revenue_growth is not None:
        revenue_gain = total_revenue * revenue_growth
        new_profit = total_profit + revenue_gain
        print(f"\n【场景2：业务总收入增长 {revenue_growth*100:.0f}%】")
        print(f"  收入增加：{revenue_gain:.0f} 元")
        print(f"  仿真后营业利润：{new_profit:.0f} 元（+{revenue_gain:.0f}）")
        output["收入增长"] = {
            "增长比例": revenue_growth,
            "收入增加": round(revenue_gain, 2),
            "仿真后利润": round(new_profit, 2),
        }

    if cost_type is None and revenue_growth is None:
        print("\n⚠️ 请指定仿真场景：--cost-type + --cost-reduction 或 --revenue-growth")

    return output


def main():
    parser = argparse.ArgumentParser(description="邮政网点损益分析")
    parser.add_argument("--action", required=True,
                        choices=["query", "ranking", "alert", "trend", "simulation"],
                        help="操作类型：query/ranking/alert/trend/simulation")
    parser.add_argument("--region", type=str, help="区名（如'武昌区'）")
    parser.add_argument("--station", type=str, help="网点名称（如'吴家山支局'）")
    parser.add_argument("--company", type=str, help="区公司（如'13武汉东西湖区'）")
    parser.add_argument("--period", type=str, help="月份（如'2026-06'）")
    parser.add_argument("--type", type=str, default="both", choices=["red", "black", "both"],
                        help="红黑榜类型")
    parser.add_argument("--top-n", type=int, default=10, help="TOP数量")
    parser.add_argument("--months", type=int, default=3, help="连续亏损月数")
    # trend 参数
    parser.add_argument("--metric", type=str, default="营业利润",
                        help="趋势指标（业务总收入/营业利润/利润总额）")
    # simulation 参数
    parser.add_argument("--cost-type", type=str, help="成本项（人工成本/租赁成本/运输成本等）")
    parser.add_argument("--cost-reduction", type=float, help="成本降低比例（0~1）")
    parser.add_argument("--revenue-growth", type=float, help="收入增长比例（0~1）")
    args = parser.parse_args()

    df = load_data()

    if args.action == "query":
        action_query(df, region=args.region, station=args.station, period=args.period, company=args.company)
    elif args.action == "ranking":
        action_ranking(df, region=args.region, period=args.period, rank_type=args.type, top_n=args.top_n, company=args.company)
    elif args.action == "alert":
        action_alert(df, region=args.region, months=args.months, company=args.company)
    elif args.action == "trend":
        action_trend(df, region=args.region, company=args.company, station=args.station, metric=args.metric)
    elif args.action == "simulation":
        action_simulation(df, region=args.region, company=args.company, period=args.period,
                          cost_type=args.cost_type, cost_reduction=args.cost_reduction,
                          revenue_growth=args.revenue_growth)


if __name__ == "__main__":
    main()
