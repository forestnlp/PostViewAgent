"""
网点损益分析 API 接口
=====================
基于清洗后的网点损益 CSV 数据，提供查询、红黑榜、预警、趋势、仿真接口。
数据源：deer-flow/skills/public/postal-station-profit-loss/data/station_profit_loss_202501_202606.csv
"""
from pathlib import Path
from typing import List, Optional

import pandas as pd
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/api/station-profit-loss", tags=["station-profit-loss"])

# 数据文件路径（相对后端目录）
DATA_FILE = Path(__file__).resolve().parents[4] / "skills" / "public" / "postal-station-profit-loss" / "data" / "station_profit_loss_202501_202606.csv"

# 缓存数据
_df_cache = None


def get_df() -> pd.DataFrame:
    """加载并缓存网点损益数据"""
    global _df_cache
    if _df_cache is not None:
        return _df_cache
    if not DATA_FILE.exists():
        raise HTTPException(status_code=500, detail=f"数据文件不存在：{DATA_FILE}")
    df = pd.read_csv(DATA_FILE)
    # 数值列转数值类型
    for col in ["业务总收入", "营业利润", "利润总额", "业务总收入_单月", "营业利润_单月", "利润总额_单月"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    _df_cache = df
    return df


def _filter(df: pd.DataFrame, region=None, company=None, station=None, period=None) -> pd.DataFrame:
    """通用筛选"""
    result = df.copy()
    if region:
        result = result[result["region"] == region]
    if company:
        result = result[result["company"] == company]
    if station:
        result = result[result["网点名称"] == station]
    if period:
        result = result[result["period"] == period]
    return result


@router.get("/regions")
def list_regions():
    """获取所有区公司列表"""
    df = get_df()
    regions = df[["company", "region"]].drop_duplicates().to_dict("records")
    return regions


@router.get("/query")
def query(region: Optional[str] = None, company: Optional[str] = None,
          station: Optional[str] = None, period: Optional[str] = None):
    """数据查询：按区/区公司/网点/月份筛选"""
    df = get_df()
    result = _filter(df, region=region, company=company, station=station, period=period)
    if result.empty:
        return []
    show_cols = ["period", "company", "region", "网点代码", "网点名称", "业务总收入", "营业利润", "利润总额"]
    show_cols = [c for c in show_cols if c in result.columns]
    result = result[show_cols].sort_values(["period", "营业利润"], ascending=[True, False])
    return result.to_dict("records")


@router.get("/ranking")
def ranking(region: Optional[str] = None, company: Optional[str] = None,
            period: Optional[str] = None, type: str = "both", top_n: int = 10):
    """红黑榜：基于单月营业利润"""
    df = get_df()
    result = _filter(df, region=region, company=company, period=period)
    if result.empty:
        return {}
    profit_col = "营业利润_单月"
    output = {}
    if type in ("red", "both"):
        red = result[result[profit_col] > 0].sort_values(profit_col, ascending=False).head(top_n)
        output["red"] = red[["period", "company", "region", "网点名称", profit_col]].to_dict("records")
    if type in ("black", "both"):
        black = result[result[profit_col] < 0].sort_values(profit_col, ascending=True).head(top_n)
        output["black"] = black[["period", "company", "region", "网点名称", profit_col]].to_dict("records")
    return output


@router.get("/alert")
def alert(region: Optional[str] = None, company: Optional[str] = None, months: int = 3):
    """亏损预警：连续N月单月营业利润为负"""
    df = get_df()
    result = _filter(df, region=region, company=company)
    if result.empty:
        return []
    profit_col = "营业利润_单月"
    alerts = []
    for code, group in result.groupby("网点代码"):
        group = group.sort_values("period")
        name = group["网点名称"].iloc[0]
        region_name = group["region"].iloc[0]
        profits = group[profit_col].tolist()
        periods = group["period"].tolist()
        consecutive = 0
        for p in reversed(profits):
            if p < 0:
                consecutive += 1
            else:
                break
        if consecutive >= 2:
            cum_loss = sum(p for p in profits[-consecutive:] if p < 0)
            if consecutive >= 3 and cum_loss < -100000:
                level = "高危"
            elif consecutive >= 3:
                level = "中危"
            else:
                level = "低危"
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
    level_order = {"高危": 0, "中危": 1, "低危": 2}
    alerts.sort(key=lambda x: level_order.get(x["预警等级"], 3))
    return alerts


@router.get("/trend")
def trend(region: Optional[str] = None, company: Optional[str] = None,
          station: Optional[str] = None, metric: str = "营业利润"):
    """趋势分析：指定指标的单月月度趋势"""
    df = get_df()
    metric_month = f"{metric}_单月"
    if metric_month not in df.columns:
        raise HTTPException(status_code=400, detail=f"指标 {metric} 无单月差分值")
    result = _filter(df, region=region, company=company, station=station)
    if result.empty:
        return []
    trend_data = result.groupby("period")[metric_month].sum().reset_index()
    trend_data = trend_data.sort_values("period")
    trend_data["环比变化"] = trend_data[metric_month].diff()
    trend_data["环比变化率%"] = (trend_data[metric_month].pct_change() * 100).round(1)
    # 替换 NaN 为 None（JSON 不支持 NaN）
    records = trend_data.to_dict("records")
    for rec in records:
        for k, v in rec.items():
            if isinstance(v, float) and (v != v):  # NaN 检测
                rec[k] = None
    return records


@router.get("/simulation")
def simulation(region: Optional[str] = None, company: Optional[str] = None,
               period: Optional[str] = None, cost_type: Optional[str] = None,
               cost_reduction: Optional[float] = None, revenue_growth: Optional[float] = None):
    """What-if仿真：成本降低/收入增长对利润的影响"""
    df = get_df()
    result = _filter(df, region=region, company=company, period=period)
    if result.empty:
        return {}
    total_profit = result["营业利润"].sum()
    total_revenue = result["业务总收入"].sum()
    output = {"基准营业利润": round(total_profit, 2), "基准收入": round(total_revenue, 2)}
    if cost_type and cost_reduction is not None:
        if cost_type not in result.columns:
            raise HTTPException(status_code=400, detail=f"成本项 {cost_type} 不存在")
        cost_total = result[cost_type].sum()
        cost_save = cost_total * cost_reduction
        output["成本降低"] = {
            "成本项": cost_type,
            "降低比例": cost_reduction,
            "成本节省": round(cost_save, 2),
            "仿真后利润": round(total_profit + cost_save, 2),
        }
    if revenue_growth is not None:
        revenue_gain = total_revenue * revenue_growth
        output["收入增长"] = {
            "增长比例": revenue_growth,
            "收入增加": round(revenue_gain, 2),
            "仿真后利润": round(total_profit + revenue_gain, 2),
        }
    return output
