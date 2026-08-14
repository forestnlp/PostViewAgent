"""
知识图谱 API 接口 (Neo4j 版本 - 重构版)

基于干净的 CSV 数据导入的 Neo4j 知识图谱
数据层级：行业 -> 经理 -> 客户
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from neo4j import GraphDatabase

router = APIRouter(prefix="/api/knowledge-graph", tags=["knowledge-graph"])

# Neo4j 配置
NEO4J_URI = "bolt://192.168.7.88:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "neo4j123"

# 创建 Neo4j 驱动实例
neo4j_driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))


def get_neo4j_result(cypher_query, params=None):
    """执行 Cypher 查询并返回结果"""
    with neo4j_driver.session() as session:
        result = session.run(cypher_query, params or {})
        return [dict(record) for record in result]


# === 响应模型 ===

class Industry(BaseModel):
    name: str
    revenue: float
    customer_count: int
    manager_count: Optional[int] = 0


class Manager(BaseModel):
    name: str
    revenue: float
    customer_count: int
    teams: Optional[List[str]] = []
    org: Optional[str] = None


class Customer(BaseModel):
    name: str
    revenue: float
    level: str
    industry2: Optional[str] = None
    industry3: Optional[str] = None
    managers: Optional[List[str]] = []
    teams: Optional[List[str]] = []
    service_point: Optional[str] = None


# === API 接口 ===

@router.get("/industries", response_model=List[Industry])
def list_industries():
    """获取所有行业列表（按二级行业）"""
    cypher = """
    MATCH (c:Customer)-[:IN_INDUSTRY]->(i:Industry {level: 2})
    RETURN 
        i.name as name,
        sum(c.revenue) as revenue,
        count(DISTINCT c) as customer_count
    ORDER BY revenue DESC
    """
    result = get_neo4j_result(cypher)
    
    industries = []
    for r in result:
        # 查询该行业下的经理数
        industry_name = r['name']
        mgr_cypher = """
        MATCH (i:Industry {name: $name})<-[:IN_INDUSTRY]-(c:Customer)-[:ASSIGNED_TO]->(m:Manager)
        RETURN count(DISTINCT m) as count
        """
        mgr_result = get_neo4j_result(mgr_cypher, {"name": industry_name})
        mgr_count = mgr_result[0]['count'] if mgr_result else 0
        
        industries.append(Industry(
            name=r['name'],
            revenue=round(r['revenue'] or 0, 2),
            customer_count=r['customer_count'] or 0,
            manager_count=mgr_count
        ))
    
    return industries


@router.get("/industries/{industry_name}/managers", response_model=List[Manager])
def list_industry_managers(industry_name: str):
    """获取指定行业下的所有经理"""
    cypher = """
    MATCH (i:Industry {name: $name})<-[:IN_INDUSTRY]-(c:Customer)-[:ASSIGNED_TO]->(m:Manager)
    RETURN 
        m.name as name,
        m.org as org,
        sum(c.revenue) as revenue,
        count(DISTINCT c) as customer_count
    ORDER BY revenue DESC
    """
    result = get_neo4j_result(cypher, {"name": industry_name})
    
    managers = []
    for r in result:
        # 查询经理所属团队
        team_cypher = """
        MATCH (m:Manager {name: $mgr_name})<-[:ASSIGNED_TO]-(c:Customer)-[:BELONGS_TO]->(t:Team)
        RETURN DISTINCT t.name as team
        """
        team_result = get_neo4j_result(team_cypher, {"mgr_name": r['name']})
        teams = [t['team'] for t in team_result if t['team']]
        
        managers.append(Manager(
            name=r['name'],
            revenue=round(r['revenue'] or 0, 2),
            customer_count=r['customer_count'] or 0,
            teams=teams,
            org=r.get('org')
        ))
    
    return managers


@router.get("/industries/{industry_name}/customers", response_model=List[Customer])
def list_industry_customers(industry_name: str):
    """获取指定行业下的所有客户"""
    cypher = """
    MATCH (i:Industry {name: $name})<-[:IN_INDUSTRY]-(c:Customer)
    OPTIONAL MATCH (c)-[:ASSIGNED_TO]->(m:Manager)
    OPTIONAL MATCH (c)-[:BELONGS_TO]->(t:Team)
    OPTIONAL MATCH (c)-[:SERVED_BY]->(sp:ServicePoint)
    RETURN 
        c.name as name,
        c.revenue as revenue,
        c.level as level,
        c.industry3 as industry3,
        collect(DISTINCT m.name) as managers,
        collect(DISTINCT t.name) as teams,
        collect(DISTINCT sp.name) as service_points
    ORDER BY c.revenue DESC
    """
    result = get_neo4j_result(cypher, {"name": industry_name})
    
    customers = []
    for r in result:
        # 处理服务网点（取第一个非空的）
        service_points = [sp for sp in r['service_points'] if sp]
        service_point = service_points[0] if service_points else None
        
        customers.append(Customer(
            name=r['name'],
            revenue=round(r['revenue'] or 0, 2),
            level=r['level'] or '普通',
            industry2=industry_name,
            industry3=r['industry3'],
            managers=[m for m in r['managers'] if m],
            teams=[t for t in r['teams'] if t],
            service_point=service_point
        ))
    
    return customers


@router.get("/managers/{manager_name}/customers", response_model=List[Customer])
def list_manager_customers(manager_name: str):
    """获取指定经理负责的所有客户"""
    cypher = """
    MATCH (m:Manager {name: $name})<-[:ASSIGNED_TO]-(c:Customer)-[:IN_INDUSTRY]->(i:Industry)
    OPTIONAL MATCH (c)-[:BELONGS_TO]->(t:Team)
    RETURN 
        c.name as name,
        c.revenue as revenue,
        c.level as level,
        i.name as industry2,
        c.industry3 as industry3,
        collect(DISTINCT t.name) as teams
    ORDER BY c.revenue DESC
    """
    result = get_neo4j_result(cypher, {"name": manager_name})
    
    customers = []
    for r in result:
        customers.append(Customer(
            name=r['name'],
            revenue=round(r['revenue'] or 0, 2),
            level=r['level'] or '普通',
            industry2=r['industry2'],
            industry3=r['industry3'],
            teams=[t for t in r['teams'] if t],
            managers=[manager_name]
        ))
    
    return customers


@router.get("/customers/{customer_name}", response_model=Customer)
def get_customer_detail(customer_name: str):
    """获取客户详情"""
    cypher = """
    MATCH (c:Customer {name: $name})
    OPTIONAL MATCH (c)-[:IN_INDUSTRY]->(i:Industry)
    OPTIONAL MATCH (c)-[:ASSIGNED_TO]->(m:Manager)
    OPTIONAL MATCH (c)-[:BELONGS_TO]->(t:Team)
    RETURN 
        c.name as name,
        c.revenue as revenue,
        c.level as level,
        c.industry2 as industry2,
        c.industry3 as industry3,
        collect(DISTINCT m.name) as managers,
        collect(DISTINCT t.name) as teams
    """
    result = get_neo4j_result(cypher, {"name": customer_name})
    
    if not result:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    r = result[0]
    return Customer(
        name=r['name'],
        revenue=round(r['revenue'] or 0, 2),
        level=r['level'] or '普通',
        industry2=r['industry2'],
        industry3=r['industry3'],
        managers=[m for m in r['managers'] if m],
        teams=[t for t in r['teams'] if t]
    )


@router.get("/teams", response_model=List[dict])
def list_teams():
    """获取所有团队列表"""
    cypher = """
    MATCH (t:Team)
    OPTIONAL MATCH (t)<-[:BELONGS_TO]-(c:Customer)
    RETURN 
        t.name as name,
        count(DISTINCT c) as customer_count,
        sum(c.revenue) as revenue
    ORDER BY revenue DESC
    """
    result = get_neo4j_result(cypher)
    
    teams = []
    for r in result:
        teams.append({
            "name": r['name'],
            "customer_count": r['customer_count'] or 0,
            "revenue": round(r['revenue'] or 0, 2)
        })
    
    return teams
