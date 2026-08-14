"use client";

import ReactECharts, { type EChartsOption } from "echarts-for-react";
import { Loader2Icon, SearchIcon, ArrowLeftIcon } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import { cn } from "@/lib/utils";

type CategoryKey = "industry" | "team" | "servicePoint" | "manager" | "customer";

interface GraphNode {
  id: string;
  name: string;
  category: CategoryKey;
  categoryIndex: number;  // ECharts 需要的数字索引
  value: number;
  customerCount?: number;
  industry?: string;
  industryDetail?: string;  // 二级行业
  businessScenario?: string;  // 业务场景
  level?: string;  // 客户等级
  team?: string;
  manager?: string;
  servicePoint?: string;
  revenue?: number;
}

interface GraphLink {
  source: string;
  target: string;
}

interface GraphData {
  categories: Array<{ name: string; key: CategoryKey }>;
  nodes: GraphNode[];
  links: GraphLink[];
}

interface DrillState {
  type: "industry" | "manager";
  id: string;
  name: string;
}

// 6 个一级行业的调和色系（邮政绿主题下的分类色）
const INDUSTRY_COLORS: Record<string, string> = {
  "商企类": "#0b9444",
  "政务类": "#2563eb",
  "电商类": "#f97316",
  "国际类": "#7c3aed",
  "散户类": "#0891b2",
  "物流类": "#ca8a04",
};
const FALLBACK_COLOR = "#6b7280";

function colorByIndustry(industry?: string): string {
  if (!industry) return FALLBACK_COLOR;
  return INDUSTRY_COLORS[industry] ?? FALLBACK_COLOR;
}

function fmtRevenue(v: number | undefined | null): string {
  if (v == null || Number.isNaN(v)) return "未知";
  if (v >= 10000) return `${(v / 10000).toFixed(2)}亿`;
  return `${v.toLocaleString("zh-CN", { maximumFractionDigits: 1 })}万`;
}

// 节点大小：收入做开方缩放
function nodeSymbolSize(value: number, category: string): number {
  if (category === "industry") return 50;
  if (category === "team") {
    return Math.max(22, Math.min(52, 20 + Math.sqrt(value) * 2));
  }
  if (category === "servicePoint") {
    return Math.max(20, Math.min(40, 18 + Math.sqrt(value) * 1.5));
  }
  if (category === "customer") {
    return Math.max(6, Math.min(16, 5 + Math.sqrt(value) * 0.5));
  }
  return Math.max(10, Math.min(28, 12 + Math.sqrt(value) * 0.6));
}

export function KnowledgeGraph() {
  const [data, setData] = useState<GraphData | null>(null);
  const [stats, setStats] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [activeIndustry, setActiveIndustry] = useState<string | null>(null);
  const [query, setQuery] = useState("");
  const [drill, setDrill] = useState<DrillState | null>(null);

  useEffect(() => {
    // 并行加载行业数据和统计信息
    Promise.all([
      fetch("/api/knowledge-graph/industries").then(r => r.json()),
      fetch("/api/knowledge-graph/stats/summary").then(r => r.json())
    ]).then(([industries, statsData]) => {
      console.log('【知识图谱】加载行业数据:', industries);
      console.log('【知识图谱】加载统计数据:', statsData);
      
      // 转换数据格式
      const nodes: GraphNode[] = industries.map((ind: any) => ({
        id: `industry:${ind.name}`,
        name: ind.name,
        category: "industry",
        categoryIndex: 0,
        value: ind.revenue,
        customerCount: ind.customer_count,
        revenue: ind.revenue,
      }));

      console.log('【知识图谱】创建节点:', nodes);
      setData({
        categories: [
          { name: "行业", key: "industry" },
          { name: "团队", key: "team" },
          { name: "服务网点", key: "servicePoint" },
          { name: "客户经理", key: "manager" },
          { name: "客户", key: "customer" },
        ],
        nodes,
        links: [],
      });
      setStats(statsData);
    }).catch((e) => {
      console.error('【知识图谱】加载失败:', e);
      setError(e instanceof Error ? e.message : "加载失败");
    });
  }, []);

  const industries = useMemo(() => {
    if (!data) return [];
    return data.nodes
      .filter((n) => n.category === "industry")
      .map((n) => n.name);
  }, [data]);

  // 过滤节点和边
  const filteredData = useMemo(() => {
    if (!data) return null;

    let nodes = [...data.nodes];
    let links = [...data.links];

    // 行业筛选
    if (activeIndustry) {
      nodes = nodes.filter((n) => {
        if (n.category === "industry") return n.name === activeIndustry;
        if (n.category === "manager") return n.industry === activeIndustry;
        if (n.category === "customer") return n.industry === activeIndustry;
        return true;
      });
    }

    // 搜索过滤
    if (query.trim()) {
      const q = query.toLowerCase();
      nodes = nodes.filter((n) => n.name.toLowerCase().includes(q));
    }

    return { nodes, links };
  }, [data, activeIndustry, query]);

  // 下钻到行业
  const handleIndustryClick = async (industryName: string) => {
    setActiveIndustry(industryName);
    try {
      // 并行加载经理和客户
      const [managersRes, customersRes] = await Promise.all([
        fetch(`/api/knowledge-graph/industries/${encodeURIComponent(industryName)}/managers`),
        fetch(`/api/knowledge-graph/industries/${encodeURIComponent(industryName)}/customers?limit=100`)
      ]);
      
      if (!managersRes.ok || !customersRes.ok) throw new Error("加载失败");
      
      const [managers, customers] = await Promise.all([
        managersRes.json(),
        customersRes.json()
      ]);

      if (!data) return;

      // 添加经理节点
      const newManagerNodes: GraphNode[] = managers
        .filter((m: any) => !data.nodes.some((n) => n.id === `manager:${m.name}`))
        .map((m: any) => ({
          id: `manager:${m.name}`,
          name: m.name,
          category: "manager",
          categoryIndex: 3,
          value: m.revenue,
          customerCount: m.customer_count,
          industry: m.industry_detail,
          team: m.teams?.[0] || undefined,
          revenue: m.revenue,
        }));

      // 添加客户节点（包含更多属性）
      const newCustomerNodes: GraphNode[] = customers
        .filter((c: any) => !data.nodes.some((n) => n.id === `customer:${c.name}`))
        .map((c: any) => ({
          id: `customer:${c.name}`,
          name: c.name,
          category: "customer",
          categoryIndex: 4,
          value: c.revenue,
          industry: c.industry_detail,
          industryDetail: c.industry_detail,
          businessScenario: c.business_scenario,
          level: c.level,
          manager: c.managers?.[0],
          servicePoint: c.service_point,
          revenue: c.revenue,
        }));

      // 构建新边（避免重复）
      const existingLinks = new Set(data.links.map((l) => `${l.source}-${l.target}`));
      const newLinks = [
        ...newManagerNodes.map((m) => ({
          source: `industry:${industryName}`,
          target: m.id,
        })).filter((l) => !existingLinks.has(`${l.source}-${l.target}`)),
        ...newCustomerNodes
          .filter((c) => c.manager)
          .map((c) => ({
            source: `manager:${c.manager}`,
            target: c.id,
          })).filter((l) => !existingLinks.has(`${l.source}-${l.target}`)),
      ];

      // 只添加新节点
      if (newManagerNodes.length > 0 || newCustomerNodes.length > 0) {
        setData({
          ...data,
          nodes: [...data.nodes, ...newManagerNodes, ...newCustomerNodes],
          links: [...data.links, ...newLinks],
        });
      }
    } catch (e) {
      console.error("下钻失败:", e);
    }
  };

  // 返回总览
  const handleBack = () => {
    setActiveIndustry(null);
    setDrill(null);
  };

  const option: EChartsOption = {
    tooltip: {
      show: true,
      formatter: (params: any) => {
        if (!params.data) return "";
        const node = params.data.data as GraphNode;
        let content = `<b>${node.name}</b><br/>`;
        content += `类型：${node.category}<br/>`;
        content += `收入：${fmtRevenue(node.revenue || node.value)}<br/>`;
        if (node.customerCount) {
          content += `客户数：${node.customerCount}<br/>`;
        }
        if (node.industry) {
          content += `行业：${node.industry}<br/>`;
        }
        if (node.industryDetail) {
          content += `细分行业：${node.industryDetail}<br/>`;
        }
        if (node.businessScenario) {
          content += `业务场景：${node.businessScenario}<br/>`;
        }
        if (node.level) {
          content += `客户等级：${node.level}<br/>`;
        }
        if (node.team) {
          content += `团队：${node.team}<br/>`;
        }
        if (node.servicePoint) {
          content += `服务网点：${node.servicePoint}<br/>`;
        }
        if (node.manager) {
          content += `经理：${node.manager}<br/>`;
        }
        return content;
      },
    },
    legend: {
      show: true,
      data: ["行业", "团队", "服务网点", "客户经理", "客户"],
      top: 10,
    },
    series: [
      {
        type: "graph",
        layout: "force",
        data: filteredData?.nodes || [],
        links: filteredData?.links || [],
        categories: [
          { name: "行业", symbol: "circle", itemStyle: { color: "#0b9444" } },
          { name: "团队", symbol: "circle", itemStyle: { color: "#7c3aed" } },
          { name: "服务网点", symbol: "circle", itemStyle: { color: "#0891b2" } },
          { name: "客户经理", symbol: "circle", itemStyle: { color: "#2563eb" } },
          { name: "客户", symbol: "circle", itemStyle: { color: "#f97316" } },
        ],
        roam: true,
        label: {
          show: true,
          position: "right",
          formatter: (params: any) => {
            if (!params || !params.data) return "";
            return params.data.name;
          },
          fontSize: 12,
          color: "#333",
        },
        labelLayout: {
          hideOverlap: true,
        },
        lineStyle: {
          color: "source",
          curveness: 0.1,
        },
        emphasis: {
          focus: "adjacency",
          lineStyle: {
            width: 4,
          },
        },
        force: {
          repulsion: activeIndustry ? 1000 : 2000,
          edgeLength: activeIndustry ? 200 : 300,
          gravity: 0.1,
        },
        symbolSize: (params: any) => {
          if (!params || !params.data) return 10;
          const node = params.data as GraphNode;
          if (node.categoryIndex === 0) return 50;  // 行业
          if (node.categoryIndex === 1) {
            return Math.max(22, Math.min(52, 20 + Math.sqrt(node.value) * 2));  // 团队
          }
          if (node.categoryIndex === 2) {
            return Math.max(20, Math.min(40, 18 + Math.sqrt(node.value) * 1.5));  // 服务网点
          }
          if (node.categoryIndex === 3) {
            return Math.max(15, Math.min(35, 15 + Math.sqrt(node.value) * 0.5));  // 经理
          }
          if (node.categoryIndex === 4) {
            return Math.max(6, Math.min(14, 6 + Math.sqrt(node.value) * 0.3));  // 客户
          }
          return 10;
        },
        itemStyle: {
          color: (params: any) => {
            if (!params || !params.data) return FALLBACK_COLOR;
            const node = params.data as GraphNode;
            // 使用 categoryIndex 匹配 colors 数组
            const colors = ["#0b9444", "#7c3aed", "#0891b2", "#2563eb", "#f97316"];  // 行业、团队、服务网点、经理、客户
            if (node.categoryIndex >= 0 && node.categoryIndex < colors.length) {
              return colors[node.categoryIndex];
            }
            return FALLBACK_COLOR;
          },
        },
        draggable: true,
        click: (params: any) => {
          if (!params.data) return;
          const node = params.data as GraphNode;
          if (node.category === "industry") {
            handleIndustryClick(node.name);
          }
        },
      },
    ],
  };

  if (error) {
    return (
      <div className="flex size-full items-center justify-center">
        <div className="text-center">
          <p className="text-lg font-medium text-red-600">加载失败</p>
          <p className="text-sm text-muted-foreground">{error}</p>
        </div>
      </div>
    );
  }

  if (!filteredData) {
    return (
      <div className="flex size-full items-center justify-center">
        <Loader2Icon className="size-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  return (
    <div className="flex size-full flex-col gap-4 p-4">
      {/* 顶部控制栏 */}
      <div className="flex shrink-0 items-center gap-4">
        {/* 返回按钮 */}
        {activeIndustry && (
          <button
            onClick={handleBack}
            className="flex items-center gap-1 rounded-md border px-3 py-1.5 text-sm hover:bg-accent"
          >
            <ArrowLeftIcon className="size-4" />
            返回总览
          </button>
        )}

        {/* 行业筛选 */}
        <div className="flex items-center gap-2">
          {industries.map((ind) => (
            <button
              key={ind}
              onClick={() => {
                if (activeIndustry === ind) {
                  setActiveIndustry(null);
                } else {
                  handleIndustryClick(ind);
                }
              }}
              className={cn(
                "rounded-full px-3 py-1 text-sm transition-colors",
                activeIndustry === ind
                  ? "bg-[#0b9444] text-white"
                  : "bg-muted hover:bg-accent"
              )}
              style={{
                backgroundColor: activeIndustry === ind ? colorByIndustry(ind) : undefined,
              }}
            >
              {ind}
            </button>
          ))}
        </div>

        {/* 搜索框 */}
        <div className="ml-auto flex items-center gap-2">
          <div className="relative">
            <SearchIcon className="absolute left-2.5 top-2.5 size-4 text-muted-foreground" />
            <input
              type="text"
              placeholder="搜索客户..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              className="h-9 w-64 rounded-md border pl-9 pr-3 text-sm focus:outline-none focus:ring-2 focus:ring-[#0b9444]"
            />
          </div>
        </div>
      </div>

      {/* 图谱画布 */}
      <div className="flex-1 min-h-0 rounded-lg border bg-card">
        <ReactECharts 
          option={option} 
          style={{ height: "100%", width: "100%" }}
          onChartReady={(chart) => {
            console.log('【ECharts】图表初始化成功');
            chart.resize();
          }}
        />
      </div>

      {/* 统计信息 */}
      <div className="shrink-0 text-sm text-muted-foreground">
        节点：{filteredData.nodes.length} 个 | 关系：{filteredData.links.length} 条
        {activeIndustry && ` | 当前：${activeIndustry}`}
        {stats && (
          <span className="ml-4">
            | 总客户：{stats.customer_count} | 总经理：{stats.manager_count} | 总行业：{stats.industry_count} | 总服务网点：{stats.service_point_count}
          </span>
        )}
      </div>
    </div>
  );
}
