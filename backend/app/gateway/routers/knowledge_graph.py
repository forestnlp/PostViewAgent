"""
知识图谱 API 接口

提供行业、经理、客户数据的查询接口
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List
import sqlite3
import os

router = APIRouter(prefix="/api/knowledge-graph", tags=["knowledge-graph"])

# 使用绝对路径
DB_PATH = "/home/bigmodel/deeplab/PostViewAgent/deer-flow/.deer-flow/data/knowledge_graph.db"


def get_db_connection():
    """获取数据库连接"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# 免认证中间件 - 知识图谱数据公开访问
def skip_auth():
    """跳过认证"""
    return True


# === 响应模型 ===

class Industry(BaseModel):
    id: int
    name: str
    revenue: float
    customer_count: int
    manager_count: int


class Team(BaseModel):
    id: int
    name: str
    leader: Optional[str]
    team_type: Optional[str]
    org: Optional[str]
    revenue: float


class Manager(BaseModel):
    id: int
    name: str
    industry_id: int
    industry_name: Optional[str]
    revenue: float
    customer_count: int
    teams: List[str] = []


class Customer(BaseModel):
    id: int
    name: str
    industry_id: int
    industry_name: Optional[str]
    revenue: float
    managers: List[str] = []
    teams: List[str] = []


# === API 接口 ===

@router.get("/industries", response_model=List[Industry])
async def list_industries():
    """获取所有行业"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM industries ORDER BY revenue DESC")
    rows = cursor.fetchall()
    conn.close()
    
    return [Industry(**dict(row)) for row in rows]


@router.get("/industries/{industry_name}/managers", response_model=List[Manager])
async def get_industry_managers(industry_name: str):
    """获取某行业下的所有经理"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 检查行业是否存在
    cursor.execute("SELECT id, name FROM industries WHERE name = ?", (industry_name,))
    industry = cursor.fetchone()
    if not industry:
        conn.close()
        raise HTTPException(status_code=404, detail="行业不存在")
    
    industry_id = industry["id"]
    
    # 获取经理列表
    cursor.execute("""
        SELECT m.id, m.name, m.industry_id, i.name as industry_name, 
               m.revenue, m.customer_count
        FROM managers m
        JOIN industries i ON m.industry_id = i.id
        WHERE m.industry_id = ?
        ORDER BY m.revenue DESC
    """, (industry_id,))
    rows = cursor.fetchall()
    
    # 获取每个经理的团队（从 manager_teams 关联表查询）
    result = []
    for row in rows:
        cursor.execute("""
            SELECT DISTINCT team_name FROM manager_teams
            WHERE manager_name = ?
        """, (row["name"],))
        teams = [t["team_name"] for t in cursor.fetchall()]
        
        result.append(Manager(
            id=row["id"],
            name=row["name"],
            industry_id=row["industry_id"],
            industry_name=row["industry_name"],
            revenue=row["revenue"],
            customer_count=row["customer_count"],
            teams=teams
        ))
    
    conn.close()
    return result


@router.get("/industries/{industry_name}/customers", response_model=List[Customer])
async def get_industry_customers(industry_name: str):
    """获取某行业下的所有客户"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, name FROM industries WHERE name = ?", (industry_name,))
    industry = cursor.fetchone()
    if not industry:
        conn.close()
        raise HTTPException(status_code=404, detail="行业不存在")
    
    industry_id = industry["id"]
    
    cursor.execute("""
        SELECT c.id, c.name, c.industry_id, i.name as industry_name, c.revenue
        FROM customers c
        JOIN industries i ON c.industry_id = i.id
        WHERE c.industry_id = ?
        ORDER BY c.revenue DESC
        LIMIT 500
    """, (industry_id,))
    rows = cursor.fetchall()
    
    result = []
    for row in rows:
        # 从 customer_relations 表获取经理
        cursor.execute("""
            SELECT manager_name FROM customer_relations WHERE customer_name = ?
        """, (row["name"],))
        managers = [m["manager_name"] for m in cursor.fetchall()]
        
        # 从 customer_teams 关联表获取团队
        cursor.execute("""
            SELECT DISTINCT team_name FROM customer_teams
            WHERE customer_name = ?
        """, (row["name"],))
        teams = [t["team_name"] for t in cursor.fetchall()]
        
        result.append(Customer(
            id=row["id"],
            name=row["name"],
            industry_id=row["industry_id"],
            industry_name=row["industry_name"],
            revenue=row["revenue"],
            managers=managers,
            teams=teams
        ))
    
    conn.close()
    return result


@router.get("/managers/{manager_name}", response_model=Manager)
async def get_manager_detail(manager_name: str):
    """获取经理详情"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT m.id, m.name, m.industry_id, i.name as industry_name,
               m.revenue, m.customer_count
        FROM managers m
        LEFT JOIN industries i ON m.industry_id = i.id
        WHERE m.name = ?
    """, (manager_name,))
    row = cursor.fetchone()
    
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="经理不存在")
    
    cursor.execute("""
        SELECT team_name FROM manager_teams WHERE manager_name = ?
    """, (manager_name,))
    teams = [t["team_name"] for t in cursor.fetchall()]
    
    conn.close()
    
    return Manager(
        id=row["id"],
        name=row["name"],
        industry_id=row["industry_id"],
        industry_name=row["industry_name"],
        revenue=row["revenue"],
        customer_count=row["customer_count"],
        teams=teams
    )


@router.get("/managers/{manager_name}/customers", response_model=List[Customer])
async def get_manager_customers(manager_name: str):
    """获取经理负责的客户"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT name FROM managers WHERE name = ?", (manager_name,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="经理不存在")
    
    cursor.execute("""
        SELECT c.id, c.name, c.industry_id, i.name as industry_name, c.revenue
        FROM customers c
        JOIN industries i ON c.industry_id = i.id
        JOIN customer_relations cr ON c.name = cr.customer_name
        WHERE cr.manager_name = ?
        ORDER BY c.revenue DESC
        LIMIT 100
    """, (manager_name,))
    rows = cursor.fetchall()
    
    result = []
    for row in rows:
        result.append(Customer(
            id=row["id"],
            name=row["name"],
            industry_id=row["industry_id"],
            industry_name=row["industry_name"],
            revenue=row["revenue"]
        ))
    
    conn.close()
    return result


@router.get("/customers/search", response_model=List[Customer])
async def search_customers(q: str, limit: int = 50):
    """搜索客户"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT c.id, c.name, c.industry_id, i.name as industry_name, c.revenue
        FROM customers c
        LEFT JOIN industries i ON c.industry_id = i.id
        WHERE c.name LIKE ?
        ORDER BY c.revenue DESC
        LIMIT ?
    """, (f"%{q}%", limit))
    rows = cursor.fetchall()
    
    result = []
    for row in rows:
        # 从 customer_relations 和 customers 表获取经理和团队信息
        cursor.execute("""
            SELECT manager_name FROM customer_relations WHERE customer_name = ?
        """, (row["name"],))
        managers = [m["manager_name"] for m in cursor.fetchall()]
        
        # 从 customers 表获取 team_name
        cursor.execute("""
            SELECT team_name FROM customers WHERE name = ?
        """, (row["name"],))
        cust_row = cursor.fetchone()
        teams = [cust_row["team_name"]] if cust_row and cust_row.get("team_name") else []
        
        result.append(Customer(
            id=row["id"],
            name=row["name"],
            industry_id=row["industry_id"],
            industry_name=row["industry_name"],
            revenue=row["revenue"],
            managers=managers,
            teams=teams
        ))
    
    conn.close()
    return result


@router.get("/teams", response_model=List[Team])
async def list_teams():
    """获取所有团队（从 managers 表的 team_name 聚合）"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 从 managers 表聚合团队数据
    cursor.execute("""
        SELECT 
            team_name as name,
            COUNT(DISTINCT name) as manager_count,
            SUM(revenue) as revenue
        FROM managers
        WHERE team_name IS NOT NULL
        GROUP BY team_name
        ORDER BY revenue DESC
    """)
    rows = cursor.fetchall()
    conn.close()
    
    # 转换为 Team 对象（简化版，缺少部分字段）
    result = []
    for row in rows:
        result.append(Team(
            id=0,  # 团队没有独立 ID
            name=row["name"],
            leader=None,
            team_type=None,
            org=None,
            revenue=row["revenue"] or 0
        ))
    
    return result


@router.get("/stats/summary")
async def get_summary_stats():
    """获取统计摘要"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM industries")
    industry_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM managers")
    manager_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM customers")
    customer_count = cursor.fetchone()[0]
    
    # 统计唯一团队数
    cursor.execute("""
        SELECT COUNT(DISTINCT team_name) FROM managers WHERE team_name IS NOT NULL
    """)
    team_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT SUM(revenue) FROM industries")
    total_revenue = cursor.fetchone()[0] or 0
    
    conn.close()
    
    return {
        "industry_count": industry_count,
        "manager_count": manager_count,
        "customer_count": customer_count,
        "team_count": team_count,
        "total_revenue": total_revenue
    }
