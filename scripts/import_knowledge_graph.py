#!/usr/bin/env python3
"""
客户关系图谱数据导入 Neo4j 脚本
基于 CSV 数据重构干净的知识图谱
"""

import pandas as pd
from neo4j import GraphDatabase
from collections import defaultdict
import json

# Neo4j 连接配置
NEO4J_URI = "bolt://192.168.7.88:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "neo4j123"

# CSV 文件路径
CSV_PATH = "skills/public/postal-data-query/data/商企客户业务数据_演示版.csv"

# 客户等级映射
LEVEL_MAP = {
    '钻石': '钻石级',
    '黄金': '金牌',
    '铂金': '金牌',
    '白银': '普通',
    '普通': '普通',
    None: '普通',
    '': '普通'
}

def load_and_clean_data():
    """加载并清洗 CSV 数据"""
    print("=" * 60)
    print("步骤 1: 加载和清洗数据")
    print("=" * 60)
    
    df = pd.read_csv(CSV_PATH)
    print(f"原始数据：{len(df)} 行")
    
    # 1. 只取最新月份的数据（2026-07）
    latest_month = df['月份'].max()
    df = df[df['月份'] == latest_month]
    print(f"最新月份 ({latest_month}) 数据：{len(df)} 行")
    
    # 2. 聚合同一客户的多行数据
    print("\n聚合客户数据...")
    
    customer_data = defaultdict(lambda: {
        'rows': [],
        'managers': set(),
        'teams': set(),
        'service_points': set(),
        'business_scenarios': set(),
        'total_revenue': 0,
        'total_volume': 0,
        'level': None,
        'industry二级': set(),
        'industry三级': set()
    })
    
    for _, row in df.iterrows():
        customer_id = row['主码']
        if pd.isna(customer_id):
            continue
            
        cd = customer_data[customer_id]
        cd['rows'].append(row)
        
        # 收集经理（处理逗号分隔）
        if pd.notna(row['客户经理名称']) and row['客户经理名称']:
            for mgr in str(row['客户经理名称']).split(','):
                mgr = mgr.strip()
                if mgr and mgr != 'nan':
                    cd['managers'].add(mgr)
        
        # 收集团队
        if pd.notna(row['团队名称']) and row['团队名称']:
            team = str(row['团队名称']).strip()
            if team and team != 'nan':
                cd['teams'].add(team)
        
        # 收集服务网点
        if pd.notna(row['网点机构名称']) and row['网点机构名称']:
            sp = str(row['网点机构名称']).strip()
            if sp and sp != 'nan':
                cd['service_points'].add(sp)
        
        # 收集业务场景
        if pd.notna(row['业务关系名称']) and row['业务关系名称']:
            bs = str(row['业务关系名称']).strip()
            if bs and bs != 'nan':
                cd['business_scenarios'].add(bs)
        
        # 累加收入和业务量
        cd['total_revenue'] += float(row['统计期收入_万元'] or 0)
        cd['total_volume'] += float(row['统计期业务量_万件'] or 0)
        
        # 收集行业
        if pd.notna(row['行业二级']) and row['行业二级']:
            cd['industry二级'].add(row['行业二级'])
        if pd.notna(row['行业三级']) and row['行业三级']:
            cd['industry三级'].add(row['行业三级'])
        
        # 客户等级（取最高等级）
        current_level = LEVEL_MAP.get(row['客户等级'], '普通')
        level_priority = {'钻石级': 4, '金牌': 3, '普通': 2, '未知': 1}
        if level_priority.get(current_level, 0) > level_priority.get(cd['level'] or '普通', 0):
            cd['level'] = current_level
    
    print(f"唯一客户数：{len(customer_data)}")
    
    # 3. 构建最终数据结构
    customers = []
    all_managers = set()
    all_teams = set()
    all_industry2 = set()
    all_industry3 = set()
    
    for customer_id, cd in customer_data.items():
        # 获取客户名称（取第一行的法定客户名称）
        customer_name = cd['rows'][0]['法定客户名称'] if cd['rows'] else customer_id
        
        # 获取行业一级（取第一行）
        industry1 = cd['rows'][0]['行业一级'] if cd['rows'] else '未知'
        
        # 主要行业二级（按收入占比最大的）
        industry2_list = list(cd['industry二级'])
        industry2 = industry2_list[0] if industry2_list else '其他'
        
        # 主要行业三级
        industry3_list = list(cd['industry三级'])
        industry3 = industry3_list[0] if industry3_list else ''
        
        # 主要经理（第一个）
        managers_list = list(cd['managers'])
        primary_manager = managers_list[0] if managers_list else ''
        
        customer = {
            'id': customer_id,
            'name': customer_name,
            'industry1': industry1,
            'industry2': industry2,
            'industry3': industry3,
            'level': cd['level'] or '普通',
            'revenue': round(cd['total_revenue'], 2),
            'volume': round(cd['total_volume'], 4),
            'managers': managers_list,
            'teams': list(cd['teams']),
            'service_points': list(cd['service_points']),
            'business_scenarios': list(cd['business_scenarios']),
            'primary_manager': primary_manager
        }
        customers.append(customer)
        
        all_managers.update(managers_list)
        all_teams.update(cd['teams'])
        all_industry2.add(industry2)
        all_industry3.add(industry3)
    
    print(f"收集到经理数：{len(all_managers)}")
    print(f"收集到团队数：{len(all_teams)}")
    
    # 4. 构建经理数据
    managers = []
    manager_customers = defaultdict(list)
    manager_orgs = defaultdict(set)  # 经理 -> 地市机构集合
    
    for customer in customers:
        for mgr in customer['managers']:
            manager_customers[mgr].append(customer)
    
    # 从原始行收集经理的地市机构
    for _, row in df.iterrows():
        if pd.notna(row['客户经理名称']) and row['客户经理名称']:
            for mgr in str(row['客户经理名称']).split(','):
                mgr = mgr.strip()
                if mgr and mgr != 'nan' and pd.notna(row['地市机构名称']):
                    manager_orgs[mgr].add(str(row['地市机构名称']).strip())
    
    for mgr_name, cust_list in manager_customers.items():
        total_revenue = sum(c['revenue'] for c in cust_list)
        # 所属机构（取第一个地市机构）
        org = next(iter(manager_orgs.get(mgr_name, set())), '')
        managers.append({
            'name': mgr_name,
            'customer_count': len(cust_list),
            'revenue': round(total_revenue, 2),
            'org': org,
            'customers': [c['name'] for c in cust_list[:10]]  # 只存前 10 个客户名
        })
    
    managers.sort(key=lambda x: x['revenue'], reverse=True)
    print(f"经理数据构建完成：{len(managers)} 个")
    
    return {
        'customers': customers,
        'managers': managers,
        'teams': list(all_teams),
        'industry1': list(set(c['industry1'] for c in customers)),
        'industry2': list(all_industry2),
        'industry3': list(all_industry3),
        'month': latest_month
    }


def import_to_neo4j(data):
    """导入 Neo4j"""
    print("\n" + "=" * 60)
    print("步骤 2: 导入 Neo4j")
    print("=" * 60)
    
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    
    try:
        with driver.session() as session:
            # 清空旧数据（可选）
            print("清空旧数据...")
            session.run("MATCH (n) DETACH DELETE n")
            
            # 1. 导入行业
            print("导入行业节点...")
            industry1_set = set()
            for customer in data['customers']:
                industry1_set.add(customer['industry1'])
            
            for ind1 in industry1_set:
                session.run(
                    "CREATE (:Industry {name: $name, level: 1})",
                    name=ind1
                )
            
            for ind2 in data['industry2']:
                session.run(
                    "CREATE (:Industry {name: $name, level: 2})",
                    name=ind2
                )
            
            for ind3 in data['industry3']:
                session.run(
                    "CREATE (:Industry {name: $name, level: 3})",
                    name=ind3
                )
            print(f"  行业节点：{len(industry1_set)} 个一级，{len(data['industry2'])} 个二级，{len(data['industry3'])} 个三级")
            
            # 2. 导入团队
            print("导入团队节点...")
            for team in data['teams']:
                session.run(
                    "CREATE (:Team {name: $name})",
                    name=team
                )
            print(f"  团队节点：{len(data['teams'])} 个")
            
            # 3. 导入经理
            print("导入经理节点...")
            for mgr in data['managers']:
                session.run(
                    "CREATE (:Manager {name: $name, customer_count: $count, revenue: $revenue, org: $org})",
                    name=mgr['name'],
                    count=mgr['customer_count'],
                    revenue=mgr['revenue'],
                    org=mgr.get('org', '')
                )
            print(f"  经理节点：{len(data['managers'])} 个")
            
            # 4. 导入客户并建立关系
            print("导入客户节点并建立关系...")
            batch_size = 100
            for i, customer in enumerate(data['customers']):
                # 创建客户节点
                session.run(
                    """
                    CREATE (c:Customer {
                        id: $id,
                        name: $name,
                        level: $level,
                        revenue: $revenue,
                        volume: $volume,
                        industry2: $industry2,
                        industry3: $industry3
                    })
                    """,
                    id=customer['id'],
                    name=customer['name'],
                    level=customer['level'],
                    revenue=customer['revenue'],
                    volume=customer['volume'],
                    industry2=customer['industry2'],
                    industry3=customer['industry3']
                )
                
                # 建立与行业的关系
                session.run(
                    """
                    MATCH (c:Customer {id: $id})
                    MATCH (i:Industry {name: $ind2})
                    CREATE (c)-[:IN_INDUSTRY]->(i)
                    """,
                    id=customer['id'],
                    ind2=customer['industry2']
                )
                
                # 建立与经理的关系
                for mgr in customer['managers']:
                    session.run(
                        """
                        MATCH (c:Customer {id: $id})
                        MATCH (m:Manager {name: $mgr})
                        CREATE (c)-[:ASSIGNED_TO]->(m)
                        """,
                        id=customer['id'],
                        mgr=mgr
                    )
                
                # 建立与团队的关系
                for team in customer['teams']:
                    session.run(
                        """
                        MATCH (c:Customer {id: $id})
                        MATCH (t:Team {name: $team})
                        CREATE (c)-[:BELONGS_TO]->(t)
                        """,
                        id=customer['id'],
                        team=team
                    )
                
                if (i + 1) % 500 == 0:
                    print(f"  已导入 {i + 1}/{len(data['customers'])} 个客户")
            
            print(f"  客户节点：{len(data['customers'])} 个")
            
            # 创建索引
            print("\n创建索引...")
            session.run("CREATE INDEX IF NOT EXISTS FOR (c:Customer) ON (c.id)")
            session.run("CREATE INDEX IF NOT EXISTS FOR (c:Customer) ON (c.name)")
            session.run("CREATE INDEX IF NOT EXISTS FOR (m:Manager) ON (m.name)")
            session.run("CREATE INDEX IF NOT EXISTS FOR (i:Industry) ON (i.name)")
            session.run("CREATE INDEX IF NOT EXISTS FOR (t:Team) ON (t.name)")
            
            print("\n导入完成!")
            
            # 验证
            print("\n验证导入结果...")
            result = session.run("""
                RETURN 
                    count(DISTINCT c) as customers,
                    count(DISTINCT m) as managers,
                    count(DISTINCT i) as industries,
                    count(DISTINCT t) as teams,
                    count(r) as relationships
                FROM (c:Customer)
                OPTIONAL MATCH (c)-[r]->()
                OPTIONAL MATCH (m:Manager)
                OPTIONAL MATCH (i:Industry)
                OPTIONAL MATCH (t:Team)
            """)
            record = result.single()
            if record:
                print(f"  客户：{record['customers']}")
                print(f"  经理：{record['managers']}")
    
    finally:
        driver.close()


def update_api_data():
    """更新 API 数据文件"""
    print("\n" + "=" * 60)
    print("步骤 3: 更新 API 缓存数据")
    print("=" * 60)
    
    # 这里可以生成 JSON 文件供 API 使用
    # 或者直接让 API 查询 Neo4j
    
    print("API 将直接查询 Neo4j，无需缓存文件")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("客户关系图谱数据重构")
    print("=" * 60)
    
    # 步骤 1: 加载和清洗数据
    data = load_and_clean_data()
    
    # 步骤 2: 导入 Neo4j
    import_to_neo4j(data)
    
    # 步骤 3: 更新 API
    update_api_data()
    
    print("\n" + "=" * 60)
    print("全部完成!")
    print("=" * 60)
    print(f"\n数据摘要:")
    print(f"  月份：{data['month']}")
    print(f"  客户：{len(data['customers'])}")
    print(f"  经理：{len(data['managers'])}")
    print(f"  团队：{len(data['teams'])}")
    print(f"  行业二级：{len(data['industry2'])}")
    print(f"  行业三级：{len(data['industry3'])}")
