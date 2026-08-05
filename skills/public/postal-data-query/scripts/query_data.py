#!/usr/bin/env python3
"""
Postal Data Query Script.

查询邮政寄递业务商企客户数据，支持多维度查询、过滤、聚合和导出。
"""

import argparse
import json
import os
import sys
from pathlib import Path

try:
    import pandas as pd
except ImportError:
    subprocess = __import__('subprocess')
    subprocess.run([sys.executable, "-m", "pip", "install", "pandas", "-q"], check=True)
    import pandas as pd


# 数据文件路径
DATA_FILE = Path(__file__).parent.parent / "data" / "商企客户业务数据_演示版.csv"


def load_data():
    """加载 CSV 数据文件"""
    if not DATA_FILE.exists():
        print(f"错误：数据文件不存在：{DATA_FILE}")
        print("请确保数据文件已放置在正确位置")
        sys.exit(1)
    
    try:
        df = pd.read_csv(DATA_FILE, encoding='utf-8')
        return df
    except Exception as e:
        print(f"错误：读取数据文件失败：{e}")
        sys.exit(1)


def action_list_columns(df):
    """列出所有可用列及其数据类型"""
    print("\n" + "=" * 70)
    print("邮政商企客户数据 - 字段列表")
    print("=" * 70)
    
    print(f"\n数据总量：{len(df)} 条记录")
    print(f"字段数量：{len(df.columns)} 个")
    
    print("\n可用字段:")
    print("-" * 70)
    
    # 按类别分组显示
    categories = {
        "区划信息": ["省份区划编码", "地市区划编码", "区县区划编码", "地市区划名称", "区县区划名称", "区划层级"],
        "客户信息": ["客户名称", "客户等级"],
        "行业分类": ["行业一级", "行业二级", "行业三级"],
        "统计期指标": ["统计期业务量_万件", "统计期收入_万元", "统计期重量_kg"],
        "对比期指标": ["对比期业务量_万件", "对比期收入_万元", "对比期重量_kg"],
    }
    
    for category, columns in categories.items():
        available = [col for col in columns if col in df.columns]
        if available:
            print(f"\n【{category}】")
            for col in available:
                dtype = str(df[col].dtype)
                non_null = df[col].notna().sum()
                print(f"  - {col:<25} ({dtype}, {non_null}条非空)")
    
    # 显示示例数据
    print("\n" + "=" * 70)
    print("示例数据 (前 3 条):")
    print("=" * 70)
    print(df.head(3).to_string(index=False))
    
    return df.head(3).to_dict('records')


def action_query(df, filter_expr=None, columns=None, order_by=None, limit=None, export_to=None):
    """执行查询"""
    result = df.copy()
    
    # 应用过滤条件
    if filter_expr:
        try:
            # 使用 eval 方式解析简单过滤条件
            # 支持格式：列名='值' 或 列名>数字
            import re
            
            # 解析简单的等值过滤
            if '=' in filter_expr and '==' not in filter_expr:
                match = re.match(r"(\S+)\s*=\s*'([^']+)'", filter_expr)
                if match:
                    col_name = match.group(1)
                    value = match.group(2)
                    result = result[result[col_name] == value]
                else:
                    # 尝试数字比较
                    match = re.match(r"(\S+)\s*>\s*(\d+\.?\d*)", filter_expr)
                    if match:
                        col_name = match.group(1)
                        value = float(match.group(2))
                        result = result[result[col_name] > value]
                    else:
                        raise ValueError(f"不支持的过滤格式：{filter_expr}")
            
            print(f"过滤条件：{filter_expr}")
            print(f"过滤后记录数：{len(result)}")
        except Exception as e:
            print(f"过滤条件错误：{e}")
            sys.exit(1)
    
    # 选择列
    if columns:
        # 处理中文逗号，统一替换为英文逗号
        columns = columns.replace('，', ',')
        col_list = [c.strip() for c in columns.split(',')]
        # 检查列是否存在
        missing_cols = [c for c in col_list if c not in result.columns]
        if missing_cols:
            print(f"警告：以下列不存在，将被忽略：{missing_cols}")
        col_list = [c for c in col_list if c in result.columns]
        if col_list:
            result = result[col_list]
    
    # 排序
    if order_by:
        try:
            parts = order_by.split(':')
            col = parts[0].strip()
            ascending = parts[1].strip().lower() != 'desc' if len(parts) > 1 else True
            result = result.sort_values(by=col, ascending=ascending)
        except Exception as e:
            print(f"排序错误：{e}")
            sys.exit(1)
    
    # 限制数量
    if limit:
        try:
            limit = int(limit)
            result = result.head(limit)
        except ValueError:
            print(f"错误：limit 必须是整数")
            sys.exit(1)
    
    # 输出结果
    if export_to:
        # 导出到文件
        os.makedirs(os.path.dirname(export_to), exist_ok=True)
        if export_to.endswith('.json'):
            result.to_json(export_to, orient='records', force_ascii=False, indent=2)
        else:
            result.to_csv(export_to, index=False, encoding='utf-8-sig')
        print(f"\n查询结果已导出到：{export_to}")
        print(f"导出记录数：{len(result)}")
    else:
        # 打印到控制台
        print("\n" + "=" * 70)
        print(f"查询结果 ({len(result)} 条记录)")
        print("=" * 70)
        
        # 格式化显示
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', None)
        pd.set_option('display.max_colwidth', 30)
        
        # 限制显示行数
        display_result = result.head(50)
        print(display_result.to_string(index=False))
        
        if len(result) > 50:
            print(f"\n... (共 {len(result)} 条记录，显示前 50 条)")
    
    return result.to_dict('records')


def action_aggregate(df, group_by, metrics, order_by=None, limit=None):
    """执行聚合查询"""
    try:
        # 处理中文逗号，统一替换为英文逗号
        metrics = metrics.replace('，', ',')
        
        # 解析指标
        agg_funcs = {}
        for m in metrics.split(','):
            parts = m.strip().split(':')
            if len(parts) == 2:
                col, func = parts
                if col.strip() not in agg_funcs:
                    agg_funcs[col.strip()] = []
                agg_funcs[col.strip()].append(func.strip())
            else:
                print(f"错误：指标格式应为 '字段：聚合函数'，得到：{m}")
                sys.exit(1)
        
        # 执行聚合 - 使用简化方式
        agg_dict = {col: funcs[0] if len(funcs) == 1 else funcs for col, funcs in agg_funcs.items()}
        result = df.groupby(group_by, as_index=False).agg(agg_dict)
        
        # 重命名列 - 扁平化多级索引
        result.columns = [col[1] if isinstance(col, tuple) and col[1] else col[0] if isinstance(col, tuple) else col 
                         for col in result.columns]
        
        # 排序
        if order_by:
            parts = order_by.split(':')
            col = parts[0].strip()
            ascending = parts[1].strip().lower() != 'desc' if len(parts) > 1 else True
            result = result.sort_values(by=col, ascending=ascending)
        
        # 限制数量
        if limit:
            try:
                limit = int(limit)
                result = result.head(limit)
            except ValueError:
                print(f"错误：limit 必须是整数")
                sys.exit(1)
        
        # 输出结果
        print("\n" + "=" * 70)
        print(f"聚合结果 ({len(result)} 条记录)")
        print(f"分组字段：{group_by}")
        print(f"聚合指标：{metrics}")
        print("=" * 70)
        
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', None)
        pd.set_option('display.max_colwidth', 30)
        
        print(result.to_string(index=False))
        
        return result.to_dict('records')
        
    except Exception as e:
        print(f"聚合查询错误：{e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description='邮政商企客户数据查询工具',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--action',
        required=True,
        choices=['list_columns', 'query', 'aggregate'],
        help='操作类型：list_columns(查看列), query(查询), aggregate(聚合)'
    )
    
    parser.add_argument(
        '--filter',
        type=str,
        help='过滤条件 (Python 表达式，例如：省份区划名称=\'江苏省\')'
    )
    
    parser.add_argument(
        '--columns',
        type=str,
        help='查询列 (逗号分隔，例如：客户名称，统计期业务量_万件)'
    )
    
    parser.add_argument(
        '--group-by',
        type=str,
        help='分组字段 (aggregate 模式)'
    )
    
    parser.add_argument(
        '--metrics',
        type=str,
        help='聚合指标 (格式：字段：聚合函数，例如：统计期业务量_万件:sum，统计期收入_万元:avg)'
    )
    
    parser.add_argument(
        '--order-by',
        type=str,
        help='排序 (格式：字段:asc/desc，例如：统计期业务量_万件:desc)'
    )
    
    parser.add_argument(
        '--limit',
        type=str,
        help='返回行数限制'
    )
    
    parser.add_argument(
        '--export-to',
        type=str,
        help='导出文件路径 (.csv 或 .json)'
    )
    
    args = parser.parse_args()
    
    # 加载数据
    print(f"正在加载数据：{DATA_FILE}")
    df = load_data()
    
    # 执行操作
    if args.action == 'list_columns':
        action_list_columns(df)
    elif args.action == 'query':
        action_query(
            df,
            filter_expr=args.filter,
            columns=args.columns,
            order_by=args.order_by,
            limit=args.limit,
            export_to=args.export_to
        )
    elif args.action == 'aggregate':
        if not args.group_by:
            parser.error('--group-by 是 aggregate 模式必需的')
        if not args.metrics:
            parser.error('--metrics 是 aggregate 模式必需的')
        action_aggregate(
            df,
            group_by=args.group_by,
            metrics=args.metrics,
            order_by=args.order_by,
            limit=args.limit
        )


if __name__ == '__main__':
    main()
