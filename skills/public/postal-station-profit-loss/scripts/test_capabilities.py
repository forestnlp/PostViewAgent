#!/usr/bin/env python3
"""
网点损益分析技能 - 能力测试
============================
验证 query / ranking / alert 三个核心功能，10 个典型问题。
"""
import sys
from pathlib import Path

# 确保能导入脚本
SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR))

from station_profit_loss import load_data, action_query, action_ranking, action_alert, action_trend, action_simulation

PASS = 0
FAIL = 0


def check(name, condition, detail=""):
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  ✅ {name}")
    else:
        FAIL += 1
        print(f"  ❌ {name} {detail}")


def main():
    print("=" * 60)
    print("网点损益分析技能 - 能力测试")
    print("=" * 60)

    df = load_data()
    print(f"\n数据加载：{len(df)} 条记录，{df['period'].nunique()} 个月，{df['region'].nunique()} 个区\n")

    # ===== query 测试 =====
    print("【query 数据查询】")
    # 测试1: 按区查询
    r = action_query(df, region="武昌区", period="2026-06")
    check("按区查询武昌区2026-06", len(r) == 27, f"实际{len(r)}")

    # 测试2: 按网点查询
    r = action_query(df, station="吴家山支局")
    check("按网点查询吴家山支局", len(r) == 18, f"实际{len(r)}")

    # 测试3: 按区公司查询
    r = action_query(df, company="13武汉东西湖区", period="2026-06")
    check("按区公司查询东西湖区", len(r) == 11, f"实际{len(r)}")

    # 测试4: 查询不存在
    r = action_query(df, region="不存在区")
    check("查询不存在区返回空", len(r) == 0)

    # ===== ranking 测试 =====
    print("\n【ranking 红黑榜】")
    # 测试5: 全量红黑榜
    r = action_ranking(df, period="2026-06", rank_type="both", top_n=5)
    check("全量红黑榜", "red" in r and "black" in r)
    check("红榜5个", len(r["red"]) == 5, f"实际{len(r['red'])}")
    check("黑榜5个", len(r["black"]) == 5, f"实际{len(r['black'])}")
    check("红榜全部盈利", all(x["营业利润_单月"] > 0 for x in r["red"]))
    check("黑榜全部亏损", all(x["营业利润_单月"] < 0 for x in r["black"]))

    # 测试6: 东西湖区红黑榜（亏损网点不足5个）
    r = action_ranking(df, company="13武汉东西湖区", period="2026-06", rank_type="both", top_n=5)
    check("东西湖区黑榜只显示亏损", all(x["营业利润_单月"] < 0 for x in r["black"]))
    check("东西湖区黑榜1个", len(r["black"]) == 1, f"实际{len(r['black'])}")

    # ===== alert 测试 =====
    print("\n【alert 亏损预警】")
    # 测试7: 连续3月预警
    r = action_alert(df, months=3)
    check("连续3月预警有结果", len(r) > 0, f"实际{len(r)}")
    check("预警含高危", any(x["预警等级"] == "高危" for x in r))

    # 测试8: 连续2月含低危
    r = action_alert(df, months=2)
    check("连续2月含低危", any(x["预警等级"] == "低危" for x in r))

    # 测试9: 按区公司预警
    r = action_alert(df, company="13武汉东西湖区", months=3)
    check("东西湖区预警", len(r) >= 1, f"实际{len(r)}")

    # 测试10: 武昌区无连续3月亏损
    r = action_alert(df, region="武昌区", months=3)
    check("武昌区无连续3月亏损", len(r) == 0, f"实际{len(r)}")

    # ===== trend 测试 =====
    print("\n【trend 趋势分析】")
    # 测试11: 东西湖区营业利润趋势
    r = action_trend(df, company="13武汉东西湖区", metric="营业利润")
    check("东西湖区趋势18个月", len(r) == 18, f"实际{len(r)}")
    check("趋势含环比变化", "环比变化" in r[0] if r else False)

    # 测试12: 吴家山支局收入趋势
    r = action_trend(df, station="吴家山支局", metric="业务总收入")
    check("吴家山趋势18个月", len(r) == 18, f"实际{len(r)}")

    # 测试13: 无效指标
    r = action_trend(df, metric="不存在指标")
    check("无效指标返回空", len(r) == 0)

    # ===== simulation 测试 =====
    print("\n【simulation What-if仿真】")
    # 测试14: 成本降低
    r = action_simulation(df, company="13武汉东西湖区", period="2026-06",
                          cost_type="人工成本", cost_reduction=0.1)
    check("成本降低仿真", "成本降低" in r)
    check("成本节省>0", r["成本降低"]["成本节省"] > 0)

    # 测试15: 收入增长
    r = action_simulation(df, region="武昌区", period="2026-06", revenue_growth=0.2)
    check("收入增长仿真", "收入增长" in r)
    check("收入增加>0", r["收入增长"]["收入增加"] > 0)

    # 测试16: 无场景参数
    r = action_simulation(df, region="武昌区", period="2026-06")
    check("无场景参数返回基准", "基准营业利润" in r)

    print("\n" + "=" * 60)
    print(f"测试结果：{PASS} 通过，{FAIL} 失败")
    print("=" * 60)
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
