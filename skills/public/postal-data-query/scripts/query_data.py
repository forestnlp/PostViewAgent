#!/usr/bin/env python3
"""
Postal Data Query Script (DuckDB Edition).

邮政寄递业务商企客户数据查询工具，基于 DuckDB 分析引擎。
支持多维度查询、过滤、聚合、导出和数据分析。
"""

import argparse
import json
import os
import sys
from pathlib import Path

try:
    import duckdb
except ImportError:
    subprocess = __import__('subprocess')
    subprocess.run([sys.executable, "-m", "pip", "install", "duckdb", "-q"], check=True)
    import duckdb


# 数据文件路径
DATA_FILE = Path(__file__).parent.parent / "data" / "商企客户业务数据_演示版.csv"

# DuckDB 连接（内存模式）
con = duckdb.connect()


def get_con():
    """获取DuckDB连接并注册CSV数据"""
    # 注册CSV为虚拟表
    con.execute(f"""
        CREATE OR REPLACE TABLE postal_customers AS 
        SELECT * FROM read_csv_auto('{DATA_FILE}', header=true)
    """)
    return con


def action_list_columns():
    """列出所有可用列及其数据类型"""
    conn = get_con()
    df = conn.execute("SELECT * FROM postal_customers LIMIT 1").df()

    print("\n" + "=" * 70)
    print("邮政寄递商企客户数据 - 字段列表（DuckDB引擎）")
    print("=" * 70)

    # 获取总行数
    total = conn.execute("SELECT COUNT(*) FROM postal_customers").fetchone()[0]
    print(f"\n数据总量：{total} 条记录")
    print(f"字段数量：{len(df.columns)} 个")

    # 获取列信息
    columns_info = conn.execute("DESCRIBE postal_customers").fetchall()

    # 按类别分组显示
    categories = {
        "时间维度": ["月份"],
        "区划信息": ["省份区划编码", "省份区划名称", "地市区划编码", "地市区划名称", "区县区划编码", "区县区划名称"],
        "机构信息": ["省份机构编码", "省份机构名称", "地市机构编码", "地市机构名称", "区县机构编码", "区县机构名称", "网点机构编码", "网点机构名称"],
        "揽收机构": ["揽收机构编码", "揽收机构名称"],
        "客户信息": ["主码", "法定客户名称", "子码", "协议客户名称", "客户等级", "注册日期"],
        "业务关系": ["业务关系码", "业务关系名称"],
        "行业分类": ["行业一级", "行业二级", "行业三级"],
        "团队信息": ["客户经理编码", "客户经理名称", "首席客户经理编码", "首席客户经理名称", "团队编码", "团队名称"],
        "统计期指标": ["统计期业务量_万件", "统计期收入_万元", "统计期重量_kg"],
        "对比期指标": ["对比期业务量_万件", "对比期收入_万元", "对比期重量_kg"],
    }

    for category, columns in categories.items():
        available = [col for col in columns if col in [c[0] for c in columns_info]]
        if available:
            print(f"\n【{category}】")
            for col_name in columns:
                # 查找列类型
                col_type = "VARCHAR"
                for c in columns_info:
                    if c[0] == col_name:
                        col_type = c[1]
                        break
                # 统计非空值
                try:
                    non_null = conn.execute(
                        f"SELECT COUNT(*) FROM postal_customers WHERE {col_name} IS NOT NULL"
                    ).fetchone()[0]
                except:
                    non_null = total
                print(f"  - {col_name:<25} ({col_type}, {non_null}条非空)")

    # 显示示例数据
    print("\n" + "=" * 70)
    print("示例数据 (前 3 条):")
    print("=" * 70)
    sample = conn.execute("SELECT * FROM postal_customers LIMIT 3").df()
    print(sample.to_string(index=False))

    # 返回可用列列表
    return [c[0] for c in columns_info]


def action_query(filter_expr=None, columns=None, order_by=None, limit=None, export_to=None):
    """执行SQL查询"""
    conn = get_con()

    # 构建SQL
    sql = "SELECT "

    # 选择列
    if columns:
        columns = columns.replace('，', ',')
        col_list = [c.strip() for c in columns.split(',')]
        sql += ', '.join(col_list)
    else:
        sql += "*"

    sql += " FROM postal_customers"

    # 过滤条件
    if filter_expr:
        sql += f" WHERE {filter_expr}"

    # 排序
    if order_by:
        parts = order_by.split(':')
        col = parts[0].strip()
        direction = parts[1].strip().upper() if len(parts) > 1 else 'ASC'
        sql += f" ORDER BY {col} {direction}"

    # 限制数量
    if limit:
        sql += f" LIMIT {int(limit)}"

    print(f"\n执行SQL: {sql}")
    result = conn.execute(sql).df()

    # 输出结果
    if export_to:
        os.makedirs(os.path.dirname(export_to) if os.path.dirname(export_to) else '.', exist_ok=True)
        if export_to.endswith('.json'):
            result.to_json(export_to, orient='records', force_ascii=False, indent=2)
        else:
            result.to_csv(export_to, index=False, encoding='utf-8-sig')
        print(f"\n查询结果已导出到：{export_to}")
        print(f"导出记录数：{len(result)}")
    else:
        print("\n" + "=" * 70)
        print(f"查询结果 ({len(result)} 条记录)")
        print("=" * 70)

        import pandas as pd
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', None)
        pd.set_option('display.max_colwidth', 30)

        display_result = result.head(50)
        print(display_result.to_string(index=False))

        if len(result) > 50:
            print(f"\n... (共 {len(result)} 条记录，显示前 50 条)")

    return result.to_dict('records')


def action_aggregate(group_by, metrics, filter_expr=None, order_by=None, limit=None):
    """执行聚合查询（SQL GROUP BY）"""
    conn = get_con()

    # 处理中文逗号
    metrics = metrics.replace('，', ',')

    # 构建聚合SQL
    agg_parts = []
    for m in metrics.split(','):
        parts = m.strip().split(':')
        if len(parts) == 2:
            col, func = parts
            func = func.upper()
            # 处理别名
            alias = f"{col}_{func.lower()}"
            agg_parts.append(f"{func}({col}) AS {alias}")
        else:
            print(f"错误：指标格式应为 '字段:聚合函数'，得到：{m}")
            sys.exit(1)

    sql = f"""
        SELECT {group_by}, {', '.join(agg_parts)}
        FROM postal_customers
    """
    
    # 添加WHERE子句（支持筛选）
    if filter_expr:
        sql += f"\n        WHERE {filter_expr}"
    
    sql += f"\n        GROUP BY {group_by}"

    # 排序
    if order_by:
        parts = order_by.split(':')
        col = parts[0].strip()
        direction = parts[1].strip().upper() if len(parts) > 1 else 'ASC'
        # 查找别名
        alias_col = None
        for m in metrics.split(','):
            p = m.strip().split(':')
            if len(p) == 2 and p[0].strip() == col:
                alias_col = f"{col}_{p[1].strip().lower()}"
                break
        if alias_col:
            sql += f" ORDER BY {alias_col} {direction}"
        else:
            sql += f" ORDER BY {col} {direction}"

    # 限制数量
    if limit:
        sql += f" LIMIT {int(limit)}"

    print(f"\n执行SQL: {sql}")
    result = conn.execute(sql).df()

    print("\n" + "=" * 70)
    print(f"聚合结果 ({len(result)} 条记录)")
    print(f"分组字段：{group_by}")
    print(f"聚合指标：{metrics}")
    print("=" * 70)

    import pandas as pd
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', None)
    pd.set_option('display.max_colwidth', 30)

    print(result.to_string(index=False))

    return result.to_dict('records')


def action_analyze(analysis_type, target=None):
    """执行高级分析（DuckDB SQL分析）"""
    conn = get_con()

    analyses = {
        "loss": f"""
            SELECT 
                {target or '地市区划名称'} as dimension,
                COUNT(*) as customer_count,
                SUM(CASE WHEN 对比期收入_万元 > 统计期收入_万元 THEN 1 ELSE 0 END) as decreasing,
                SUM(CASE WHEN 统计期收入_万元 > 对比期收入_万元 THEN 1 ELSE 0 END) as increasing,
                SUM(对比期收入_万元 - 统计期收入_万元) as total_decrease
            FROM postal_customers
            WHERE 对比期收入_万元 IS NOT NULL AND 统计期收入_万元 IS NOT NULL
            GROUP BY {target or '地市区划名称'}
            HAVING total_decrease > 0
            ORDER BY total_decrease DESC
        """,
        "tier": """
            SELECT 
                CASE 
                    WHEN 统计期收入_万元 >= 5 THEN '特级(钻石)'
                    WHEN 统计期收入_万元 >= 1 THEN '一级(铂金)'
                    WHEN 统计期收入_万元 >= 0.5 THEN '二级(黄金)'
                    WHEN 统计期收入_万元 >= 0.1 THEN '三级(白银)'
                    ELSE '小微'
                END as customer_tier,
                COUNT(*) as customer_count,
                SUM(统计期收入_万元) as total_revenue
            FROM postal_customers
            WHERE 统计期收入_万元 IS NOT NULL
            GROUP BY customer_tier
            ORDER BY customer_tier
        """,
        "top_customers": f"""
            SELECT 
                法定客户名称 as 客户名称,
                行业一级,
                {target or '地市区划名称'} as region,
                统计期业务量_万件,
                统计期收入_万元,
                (统计期收入_万元 - 对比期收入_万元) as revenue_change
            FROM postal_customers
            WHERE 统计期收入_万元 IS NOT NULL
            ORDER BY 统计期收入_万元 DESC
            LIMIT 20
        """,
    }

    if analysis_type not in analyses:
        print(f"错误：不支持的分析类型：{analysis_type}")
        print(f"支持的类型：{', '.join(analyses.keys())}")
        sys.exit(1)

    print(f"\n执行分析: {analysis_type}")
    print(f"SQL: {analyses[analysis_type]}")
    result = conn.execute(analyses[analysis_type]).df()

    print("\n" + "=" * 70)
    print(f"分析结果 ({len(result)} 条记录)")
    print("=" * 70)

    import pandas as pd
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', None)
    pd.set_option('display.max_colwidth', 40)

    print(result.to_string(index=False))

    return result.to_dict('records')


def main():
    parser = argparse.ArgumentParser(
        description='邮政寄递商企客户数据查询工具（DuckDB引擎）',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        '--action',
        required=True,
        choices=['list_columns', 'query', 'aggregate', 'analyze'],
        help='操作类型：list_columns(查看列), query(查询), aggregate(聚合), analyze(分析)'
    )

    parser.add_argument('--filter', type=str, help='过滤条件 (SQL WHERE子句)')
    parser.add_argument('--columns', type=str, help='查询列 (逗号分隔)')
    parser.add_argument('--group-by', type=str, help='分组字段 (aggregate模式)')
    parser.add_argument('--metrics', type=str, help='聚合指标 (格式：字段:聚合函数)')
    parser.add_argument('--order-by', type=str, help='排序 (格式：字段:asc/desc)')
    parser.add_argument('--limit', type=str, help='返回行数限制')
    parser.add_argument('--export-to', type=str, help='导出文件路径')
    parser.add_argument('--analysis-type', type=str, help='分析类型 (analyze模式): loss/tier/top_customers')
    parser.add_argument('--target', type=str, help='分析维度字段 (analyze模式)')

    args = parser.parse_args()

    if not DATA_FILE.exists():
        print(f"错误：数据文件不存在：{DATA_FILE}")
        sys.exit(1)

    print(f"数据引擎：DuckDB")
    print(f"数据文件：{DATA_FILE}")

    if args.action == 'list_columns':
        action_list_columns()
    elif args.action == 'query':
        action_query(
            filter_expr=args.filter,
            columns=args.columns,
            order_by=args.order_by,
            limit=int(args.limit) if args.limit else None,
            export_to=args.export_to
        )
    elif args.action == 'aggregate':
        if not args.group_by:
            parser.error('--group-by 是 aggregate 模式必需的')
        if not args.metrics:
            parser.error('--metrics 是 aggregate 模式必需的')
        action_aggregate(
            group_by=args.group_by,
            metrics=args.metrics,
            filter_expr=args.filter,
            order_by=args.order_by,
            limit=int(args.limit) if args.limit else None
        )
    elif args.action == 'analyze':
        if not args.analysis_type:
            parser.error('--analysis-type 是 analyze 模式必需的')
        action_analyze(
            analysis_type=args.analysis_type,
            target=args.target
        )


if __name__ == '__main__':
    main()
