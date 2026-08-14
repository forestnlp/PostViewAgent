"""
知识图谱 API 接口 (Neo4j 版本)

提供行业、经理、客户、服务网点数据的查询接口
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


class Team(BaseModel):
    name: str
    team_type: Optional[str]
    org: Optional[str]
    revenue: float
    manager_count: Optional[int] = 0
    customer_count: Optional[int] = 0


class ServicePoint(BaseModel):
    name: str
    code: Optional[str]
    region: Optional[str]
    revenue: float
    customer_count: Optional[int] = 0


class Manager(BaseModel):
    name: str
    code: Optional[str]
    revenue: float
    customer_count: Optional[int] = 0
    teams: List[str] = []
    industry_detail: Optional[str] = None


class Customer(BaseModel):
    name: str
    level: Optional[str]
    revenue: float
    industry_detail: Optional[str]
    business_scenario: Optional[str]
    managers: List[str] = []
    service_point: Optional[str] = None


# === API 接口 ===

@router.get("/industries", response_model=List[Industry])
async def list_industries():
    """获取所有行业"""
    cypher = """
        MATCH (i:Industry)
        RETURN i.name as name, 
               i.revenue as revenue,
               i.customer_count as customer_count,
               i.manager_count as manager_count
        ORDER BY i.revenue DESC
    """
    results = get_neo4j_result(cypher)
    return [Industry(**r) for r in results]


@router.get("/industries/{industry_name}/managers", response_model=List[Manager])
async def get_industry_managers(industry_name: str):
    """获取某行业下的所有经理"""
    cypher = """
        MATCH (i:Industry {name: $industry_name})<-[:BELONGS_TO]-(c:Customer)<-[:RESPONSIBLE_FOR]-(m:Manager)
        WITH DISTINCT m, i
        OPTIONAL MATCH (m)-[:MEMBER_OF]->(t:Team)
        RETURN m.name as name,
               m.code as code,
               m.revenue as revenue,
               m.customer_count as customer_count,
               collect(DISTINCT t.name) as teams,
               i.name as industry_detail
        ORDER BY m.revenue DESC
    """
    results = get_neo4j_result(cypher, {"industry_name": industry_name})
    return [Manager(**r) for r in results]


@router.get("/industries/{industry_name}/customers", response_model=List[Customer])
async def get_industry_customers(industry_name: str, limit: int = 100):
    """获取某行业下的所有客户"""
    cypher = """
        MATCH (i:Industry {name: $industry_name})<-[:BELONGS_TO]-(c:Customer)<-[:RESPONSIBLE_FOR]-(m:Manager)
        OPTIONAL MATCH (c)-[:SERVED_BY]->(s:ServicePoint)
        WITH c, m, s
        ORDER BY c.revenue DESC
        LIMIT $limit
        RETURN c.name as name,
               c.level as level,
               c.revenue as revenue,
               c.industry_detail as industry_detail,
               c.business_scenario as business_scenario,
               collect(DISTINCT m.name) as managers,
               collect(DISTINCT s.name)[0] as service_point
    """
    results = get_neo4j_result(cypher, {"industry_name": industry_name, "limit": limit})
    return [Customer(**r) for r in results]


@router.get("/managers/{manager_name}", response_model=Manager)
async def get_manager_detail(manager_name: str):
    """获取经理详情"""
    cypher = """
        MATCH (m:Manager {name: $manager_name})
        OPTIONAL MATCH (m)-[:MEMBER_OF]->(t:Team)
        RETURN m.name as name,
               m.code as code,
               m.revenue as revenue,
               m.customer_count as customer_count,
               collect(DISTINCT t.name) as teams
    """
    result = get_neo4j_result(cypher, {"manager_name": manager_name})
    if not result:
        raise HTTPException(status_code=404, detail="经理不存在")
    return Manager(**result[0])


@router.get("/managers/{manager_name}/customers", response_model=List[Customer])
async def get_manager_customers(manager_name: str, limit: int = 100):
    """获取经理负责的客户"""
    cypher = """
        MATCH (m:Manager {name: $manager_name})-[:RESPONSIBLE_FOR]->(c:Customer)
        OPTIONAL MATCH (c)-[:SERVED_BY]->(s:ServicePoint)
        ORDER BY c.revenue DESC
        LIMIT $limit
        RETURN c.name as name,
               c.level as level,
               c.revenue as revenue,
               c.industry_detail as industry_detail,
               c.business_scenario as business_scenario,
               collect(DISTINCT s.name)[0] as service_point
    """
    results = get_neo4j_result(cypher, {"manager_name": manager_name, "limit": limit})
    return [Customer(**r) for r in results]


@router.get("/customers/search", response_model=List[Customer])
async def search_customers(q: str, limit: int = 50):
    """搜索客户"""
    cypher = """
        MATCH (c:Customer)
        WHERE c.name CONTAINS $q
        OPTIONAL MATCH (c)<-[:RESPONSIBLE_FOR]-(m:Manager)
        OPTIONAL MATCH (c)-[:SERVED_BY]->(s:ServicePoint)
        ORDER BY c.revenue DESC
        LIMIT $limit
        RETURN c.name as name,
               c.level as level,
               c.revenue as revenue,
               c.industry_detail as industry_detail,
               c.business_scenario as business_scenario,
               collect(DISTINCT m.name) as managers,
               collect(DISTINCT s.name)[0] as service_point
    """
    results = get_neo4j_result(cypher, {"q": q, "limit": limit})
    return [Customer(**r) for r in results]


@router.get("/teams", response_model=List[Team])
async def list_teams():
    """获取所有团队"""
    cypher = """
        MATCH (t:Team)
        RETURN t.name as name,
               t.team_type as team_type,
               t.org as org,
               t.revenue as revenue,
               t.manager_count as manager_count,
               t.customer_count as customer_count
        ORDER BY t.revenue DESC
    """
    results = get_neo4j_result(cypher)
    return [Team(**r) for r in results]


@router.get("/service-points", response_model=List[ServicePoint])
async def list_service_points():
    """获取所有服务网点"""
    cypher = """
        MATCH (s:ServicePoint)
        RETURN s.name as name,
               s.code as code,
               s.region as region,
               s.revenue as revenue,
               s.customer_count as customer_count
        ORDER BY s.revenue DESC
    """
    results = get_neo4j_result(cypher)
    return [ServicePoint(**r) for r in results]


@router.get("/service-points/{region}", response_model=List[ServicePoint])
async def get_service_points_by_region(region: str):
    """获取某区域的所有服务网点"""
    cypher = """
        MATCH (s:ServicePoint {region: $region})
        RETURN s.name as name,
               s.code as code,
               s.region as region,
               s.revenue as revenue,
               s.customer_count as customer_count
        ORDER BY s.revenue DESC
    """
    results = get_neo4j_result(cypher, {"region": region})
    return [ServicePoint(**r) for r in results]


@router.get("/stats/summary")
async def get_summary_stats():
    """获取统计摘要"""
    cypher = """
        MATCH (c:Customer)
        WITH count(c) as customer_count, sum(c.revenue) as total_revenue
        OPTIONAL MATCH (m:Manager)
        WITH customer_count, total_revenue, count(m) as manager_count
        OPTIONAL MATCH (i:Industry)
        WITH customer_count, total_revenue, manager_count, count(i) as industry_count
        OPTIONAL MATCH (t:Team)
        WITH customer_count, total_revenue, manager_count, industry_count, count(t) as team_count
        OPTIONAL MATCH (s:ServicePoint)
        WITH customer_count, total_revenue, manager_count, industry_count, team_count, count(s) as service_point_count
        RETURN {
            customer_count: customer_count,
            manager_count: manager_count,
            industry_count: industry_count,
            team_count: team_count,
            service_point_count: service_point_count,
            total_revenue: total_revenue
        } as stats
    """
    result = get_neo4j_result(cypher)
    return result[0]['stats'] if result else {}


@router.get("/industries/detail")
async def get_industries_detail():
    """获取行业详细统计（按一级行业分类）"""
    cypher = """
        MATCH (i:Industry)
        RETURN i.category as category,
               count(DISTINCT i) as industry_count,
               sum(i.customer_count) as total_customers,
               sum(i.revenue) as total_revenue
        ORDER BY total_revenue DESC
    """
    results = get_neo4j_result(cypher)
    return results


@router.get("/customers/by-level")
async def get_customers_by_level():
    """按客户等级统计"""
    cypher = """
        MATCH (c:Customer)
        RETURN c.level as level,
               count(c) as customer_count,
               sum(c.revenue) as total_revenue
        ORDER BY total_revenue DESC
    """
    results = get_neo4j_result(cypher)
    return results


@router.get("/customers/{customer_name}", response_model=Customer)
async def get_customer_detail(customer_name: str):
    """获取客户详情"""
    cypher = """
        MATCH (c:Customer {name: $customer_name})
        OPTIONAL MATCH (c)<-[:RESPONSIBLE_FOR]-(m:Manager)
        OPTIONAL MATCH (c)-[:SERVED_BY]->(s:ServicePoint)
        OPTIONAL MATCH (c)-[:BELONGS_TO]->(i:Industry)
        RETURN c.name as name,
               c.level as level,
               c.revenue as revenue,
               c.industry_detail as industry_detail,
               c.business_scenario as business_scenario,
               collect(DISTINCT m.name) as managers,
               collect(DISTINCT s.name)[0] as service_point
    """
    result = get_neo4j_result(cypher, {"customer_name": customer_name})
    if not result:
        raise HTTPException(status_code=404, detail="客户不存在")
    return Customer(**result[0])


@router.get("/top-customers", response_model=List[Customer])
async def get_top_customers(limit: int = 20):
    """获取 Top 客户"""
    cypher = """
        MATCH (c:Customer)
        OPTIONAL MATCH (c)<-[:RESPONSIBLE_FOR]-(m:Manager)
        OPTIONAL MATCH (c)-[:SERVED_BY]->(s:ServicePoint)
        WITH c, m, s
        ORDER BY c.revenue DESC
        LIMIT $limit
        RETURN c.name as name,
               c.level as level,
               c.revenue as revenue,
               c.industry_detail as industry_detail,
               c.business_scenario as business_scenario,
               collect(DISTINCT m.name) as managers,
               collect(DISTINCT s.name)[0] as service_point
    """
    results = get_neo4j_result(cypher, {"limit": limit})
    return [Customer(**r) for r in results]


@router.get("/top-managers", response_model=List[Manager])
async def get_top_managers(limit: int = 20):
    """获取 Top 经理"""
    cypher = """
        MATCH (m:Manager)
        OPTIONAL MATCH (m)-[:MEMBER_OF]->(t:Team)
        WITH m, t
        ORDER BY m.revenue DESC
        LIMIT $limit
        RETURN m.name as name,
               m.code as code,
               m.revenue as revenue,
               m.customer_count as customer_count,
               collect(DISTINCT t.name) as teams
    """
    results = get_neo4j_result(cypher, {"limit": limit})
    return [Manager(**r) for r in results]
