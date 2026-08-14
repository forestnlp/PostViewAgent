"use client";

import ReactECharts, { type EChartsOption } from "echarts-for-react";
import { useEffect, useState, useRef, useCallback, useMemo } from "react";
import { Search, RefreshCw, BarChart3, Users, Building2 } from "lucide-react";

import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";

interface Industry {
  name: string;
  revenue: number;
  customer_count: number;
}

interface Manager {
  name: string;
  code: string;
  revenue: number;
  customer_count: number;
  teams: string[];
  industry_detail: string;
  org?: string;
}

interface Customer {
  name: string;
  revenue: number;
  industry_detail: string;  // 后端返回的字段名
  managers: string[];
  level: string;
  business_scenario: string;  // 后端返回的字段名
  service_point: string;
  industry3?: string;
}

function fmtRevenue(v: number | null | undefined): string {
  if (v == null || Number.isNaN(v)) return "未知";
  if (v >= 10000) return `${(v / 10000).toFixed(2)}亿`;
  return `${v.toFixed(1)}万`;
}

export default function KnowledgeGraphVisual() {
  const [industries, setIndustries] = useState<Industry[]>([]);
  const [selectedIndustry, setSelectedIndustry] = useState<string | null>(null);
  const [expandedIndustries, setExpandedIndustries] = useState<Set<string>>(new Set());
  const [expandedManagers, setExpandedManagers] = useState<Set<string>>(new Set()); // 跟踪展开的经理
  const [managers, setManagers] = useState<Manager[]>([]);
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [detailPanel, setDetailPanel] = useState<{ type: "industry" | "manager" | "customer"; data: any } | null>(null);
  const chartRef = useRef<any>(null);

  // 加载行业列表
  useEffect(() => {
    setLoading(true);
    fetch("/api/knowledge-graph/industries")
      .then((r) => r.json())
      .then((data: Industry[]) => {
        setIndustries(data.sort((a, b) => b.revenue - a.revenue));
        setLoading(false);
      })
      .catch((e) => {
        console.error("加载行业失败:", e);
        setLoading(false);
      });
  }, []);

  // 加载行业详情
  const loadIndustryDetail = useCallback(async (industryName: string) => {
    console.log("加载行业详情:", industryName);
    try {
      const [managersRes, customersRes] = await Promise.all([
        fetch(`/api/knowledge-graph/industries/${encodeURIComponent(industryName)}/managers`),
        fetch(`/api/knowledge-graph/industries/${encodeURIComponent(industryName)}/customers`),
      ]);
      const [managersData, customersData] = await Promise.all([
        managersRes.json(),
        customersRes.json(),
      ]);
      console.log("经理数据:", managersData.length, "个");
      console.log("客户数据:", customersData.length, "个");
      if (customersData.length > 0) {
        console.log("客户示例完整结构:", JSON.stringify(customersData[0], null, 2));
      }
      setManagers(managersData);
      setCustomers(customersData);
      // 一次性展开所有经理，让客户也同时显示
      setExpandedManagers(new Set(managersData.map((m: any) => m.name)));
    } catch (e) {
      console.error("加载详情失败:", e);
    }
  }, []);

  // 处理行业点击
  const handleIndustryClick = async (industryName: string) => {
    if (expandedIndustries.has(industryName)) {
      // 收起
      setExpandedIndustries(new Set([...expandedIndustries].filter((i) => i !== industryName)));
      setManagers([]);
      setCustomers([]);
      setExpandedManagers(new Set());
    } else {
      // 展开（一次只展开一个行业，避免 managers/customers 与行业错配）
      setExpandedIndustries(new Set([industryName]));
      setSelectedIndustry(industryName);
      setExpandedManagers(new Set());
      await loadIndustryDetail(industryName);
    }
  };

  // 处理经理点击
  const handleManagerClick = (managerName: string) => {
    console.log("点击经理:", managerName, "当前展开:", Array.from(expandedManagers));
    if (expandedManagers.has(managerName)) {
      // 收起该经理的客户
      const newSet = new Set([...expandedManagers].filter((m) => m !== managerName));
      console.log("收起经理，新状态:", Array.from(newSet));
      setExpandedManagers(newSet);
    } else {
      // 展开该经理的客户
      const newSet = new Set([...expandedManagers, managerName]);
      console.log("展开经理，新状态:", Array.from(newSet));
      setExpandedManagers(newSet);
    }
  };

  // 构建图谱数据
  const graphData = useMemo(() => {
    console.log("构建图谱数据，industries:", industries.length, "expandedIndustries:", expandedIndustries.size);
    const nodes: any[] = [];
    const links: any[] = [];
    const addedCustomerIds = new Set<string>();  // 去重客户节点（一个客户可能关联多个经理）

    // 添加行业节点
    industries.forEach((ind) => {
      const isExpanded = expandedIndustries.has(ind.name);
      
      nodes.push({
        id: `industry:${ind.name}`,
        name: ind.name,
        category: 0, // 行业
        value: ind.revenue,
        symbolSize: 50 + Math.min(ind.customer_count * 0.1, 30),
        itemStyle: { 
          color: ind.customer_count > 1000 ? "#0b9444" : "#22c55e",
          shadowBlur: 10,
          shadowColor: "rgba(11, 148, 68, 0.5)"
        },
        label: { 
          show: true, 
          fontSize: 13,
          fontWeight: "bold",
          color: "#1f2937"
        },
        type: "industry",
        customerCount: ind.customer_count,
        revenue: ind.revenue,
        expanded: isExpanded,
      });

      // 如果展开，添加经理
      if (isExpanded) {
        // loadIndustryDetail 只加载当前展开行业的经理/客户，直接使用即可
        const industryManagers = managers;
        const industryCustomers = customers;
        console.log(`行业${ind.name}: 经理${industryManagers.length}个，客户${industryCustomers.length}个`);
        console.log(`行业${ind.name}客户数据示例:`, industryCustomers[0]);

        // 添加经理节点
        industryManagers.forEach((mgr) => {
          const isManagerExpanded = expandedManagers.has(mgr.name);
          
          nodes.push({
            id: `manager:${mgr.name}`,
            name: mgr.name,
            category: 1, // 经理
            value: mgr.revenue,
            symbolSize: 30 + Math.min(mgr.customer_count * 0.5, 20),
            itemStyle: { 
              color: isManagerExpanded ? "#2563eb" : "#3b82f6", // 展开时颜色更深
              shadowBlur: 8,
              shadowColor: isManagerExpanded ? "rgba(37, 99, 235, 0.5)" : "rgba(59, 130, 246, 0.5)"
            },
            label: { 
              show: true, 
              fontSize: 11,
              color: "#1e3a8a"
            },
            type: "manager",
            customerCount: mgr.customer_count,
            revenue: mgr.revenue,
            teams: mgr.teams,
            industry: ind.name,
            org: mgr.org,
            expanded: isManagerExpanded,
          });

          // 经理连接到行业
          links.push({
            source: `manager:${mgr.name}`,
            target: `industry:${ind.name}`,
            lineStyle: { 
              color: "#93c5fd",
              width: 2,
              opacity: 0.6
            },
          });

          // 如果经理被展开，添加该经理的客户
            if (isManagerExpanded) {
              console.log("展开经理:", mgr.name, "查找客户...");
              console.log("该经理的客户数:", mgr.customer_count);
              // 按客户关联的经理过滤（后端返回的客户带 managers 字段）
              const managerCustomers = industryCustomers.filter((c: any) =>
                Array.isArray(c.managers) && c.managers.includes(mgr.name)
              );
              console.log("找到客户:", managerCustomers.length, "个");
              if (managerCustomers.length > 0) {
                console.log("客户列表:", managerCustomers.map((c: any) => c.name).slice(0, 10));
              }
              
              // 按营收排序，取前 30 个客户
              const topCustomers = managerCustomers.sort((a, b) => b.revenue - a.revenue).slice(0, 30);
              
              topCustomers.forEach((cust) => {
                const custId = `customer:${cust.name}`;
                // 去重：同一个客户关联多个经理时只添加一次
                if (addedCustomerIds.has(custId)) return;
                addedCustomerIds.add(custId);
                
                // 映射 level 值
                const levelMap: Record<string, string> = {
                  '钻石': '钻石级',
                  '黄金': '金牌',
                  '铂金': '金牌',
                  '白银': '普通',
                  '普通': '普通',
                };
                const displayLevel = levelMap[cust.level || ''] || cust.level || '普通';
                
                nodes.push({
                  id: custId,
                  name: cust.name,
                  category: 2, // 客户
                  value: cust.revenue,
                  symbolSize: 18 + Math.min(cust.revenue / 500, 12),
                  itemStyle: { 
                    color: displayLevel === "钻石级" ? "#ef4444" : displayLevel === "金牌" ? "#f59e0b" : "#f97316",
                    shadowBlur: 6,
                    shadowColor: displayLevel === "钻石级" ? "rgba(239, 68, 68, 0.5)" : "rgba(249, 115, 22, 0.5)"
                  },
                  label: { 
                    show: false, // 客户太多，默认不显示标签
                    fontSize: 10,
                    color: displayLevel === "钻石级" ? "#7f1d1d" : "#9a3412"
                  },
                  type: "customer",
                  level: displayLevel,
                  revenue: cust.revenue,
                  servicePoint: cust.service_point,
                  managerCount: Array.isArray(cust.managers) ? cust.managers.length : 0,
                  industry3: cust.industry3,
                });

                // 客户连接到该经理
                links.push({
                  source: `manager:${mgr.name}`,
                  target: `customer:${cust.name}`,
                  lineStyle: { 
                    color: displayLevel === "钻石级" ? "#fca5a5" : "#fdba74",
                    width: 1.5,
                    opacity: 0.5
                  },
                });
              });
            }
        });
      }
    });

    return { nodes, links };
  }, [industries, expandedIndustries, expandedManagers, managers, customers]);

  // ECharts 配置
  const option: EChartsOption = useMemo(() => ({
    tooltip: {
      show: true,
      trigger: "item",
      formatter: (params: any) => {
        // 边（关系线）的 tooltip
        if (params.dataType === "edge") {
          const edge = params.data;
          const src = edge.source?.name ?? edge.source ?? "未知";
          const tgt = edge.target?.name ?? edge.target ?? "未知";
          return `<div style="font-weight:bold;font-size:14px;margin-bottom:8px;">关系</div>
                  <div style="color:#6b7280;">${src} → ${tgt}</div>`;
        }
        if (!params.data) return "";
        const node = params.data;
        let content = `<div style="font-weight:bold;font-size:14px;margin-bottom:8px;">${node.name}</div>`;
        
        if (node.type === "industry") {
          content += `<div style="color:#059669;">● 行业分类</div>`;
          content += `<div style="margin-top:6px;">客户数：${node.customerCount || 0}</div>`;
          content += `<div>营收：${fmtRevenue(node.revenue)}</div>`;
          content += `<div style="margin-top:6px;color:#6b7280;font-size:12px;">${node.expanded ? "▼ 已展开" : "▶ 点击展开"}</div>`;
        } else if (node.type === "manager") {
          content += `<div style="color:#2563eb;">● 客户经理</div>`;
          content += `<div style="margin-top:6px;">负责客户：${node.customerCount || 0} 家</div>`;
          content += `<div>负责营收：${fmtRevenue(node.revenue)}</div>`;
          if (node.org) {
            content += `<div style="margin-top:4px;font-size:12px;color:#6b7280;">所属机构：${node.org}</div>`;
          }
          if (node.teams && node.teams[0]) {
            content += `<div style="margin-top:4px;font-size:12px;color:#6b7280;">团队：${node.teams[0]}</div>`;
          }
          if (node.industry) {
            content += `<div style="margin-top:4px;font-size:12px;color:#6b7280;">所属行业：${node.industry}</div>`;
          }
          content += `<div style="margin-top:6px;color:#6b7280;font-size:12px;">${node.expanded ? "▼ 已展开客户" : "▶ 点击展开客户"}</div>`;
        } else if (node.type === "customer") {
          const levelColor = node.level === '钻石级' ? '#ef4444' : node.level === '金牌' ? '#f59e0b' : '#f97316';
          content += `<div style="color:${levelColor};">● ${node.level || "客户"}</div>`;
          content += `<div style="margin-top:6px;">营收：${fmtRevenue(node.revenue)}</div>`;
          if (node.managerCount) {
            content += `<div>关联经理：${node.managerCount} 位</div>`;
          }
          if (node.industry3) {
            content += `<div style="margin-top:4px;font-size:12px;color:#6b7280;">三级行业：${node.industry3}</div>`;
          }
          if (node.servicePoint) {
            content += `<div style="margin-top:4px;font-size:12px;color:#6b7280;">服务网点：${node.servicePoint}</div>`;
          }
        }
        return content;
      },
      backgroundColor: "rgba(255, 255, 255, 0.95)",
      borderColor: "#e5e7eb",
      borderWidth: 1,
      padding: 12,
      textStyle: { color: "#1f2937" },
    },
    legend: {
      show: true,
      bottom: 10,
      data: ["行业", "经理", "客户"],
      textStyle: { fontSize: 12, color: "#333" },
    },
    series: [
      {
        type: "graph",
        layout: "force",
        data: graphData.nodes.filter((n: any) => {
          if (!searchQuery.trim()) return true;
          return n.name.toLowerCase().includes(searchQuery.toLowerCase());
        }),
        links: graphData.links.filter((l: any) => {
          if (!searchQuery.trim()) return true;
          const sourceNode = graphData.nodes.find((n: any) => n.id === l.source);
          const targetNode = graphData.nodes.find((n: any) => n.id === l.target);
          return sourceNode?.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                 targetNode?.name.toLowerCase().includes(searchQuery.toLowerCase());
        }),
        categories: [
          { name: "行业", icon: "circle" },
          { name: "经理", icon: "circle" },
          { name: "客户", icon: "circle" },
        ],
        roam: true,
        zoom: 1,
        label: {
          show: true,
          position: "right",
          formatter: "{b}",
        },
        lineStyle: {
          color: "source",
          curveness: 0.2,
        },
        emphasis: {
          focus: "adjacency",
          scale: true,
          lineStyle: {
            width: 3,
          },
        },
        force: {
          repulsion: 600,
          edgeLength: [80, 150],
          gravity: 0.08,
        },
        // 关闭动画：展开/收起时直接跳到新布局，避免力导向重排导致的"旋转/晕眩"
        animation: false,
        animationDurationUpdate: 0,
      },
    ],
  }), [graphData, searchQuery]);

  return (
    <div className="h-full w-full flex flex-col gap-2 p-2 bg-white">
      {/* 顶部工具栏 */}
      <div className="flex items-center justify-between px-2 py-1 flex-shrink-0">
        <div className="flex items-center gap-4">
          <div>
            <h1 className="text-xl font-bold text-gray-900">客户关系图谱</h1>
            <p className="text-xs text-gray-500 mt-0.5">
              点击行业展开经理，点击经理展开客户，滚轮缩放，拖拽移动
            </p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <div className="relative">
            <Search className="absolute left-3 top-2 h-4 w-4 text-gray-400" />
            <Input
              placeholder="搜索..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10 w-64 h-9"
            />
          </div>
          <button
            onClick={() => {
              setExpandedIndustries(new Set());
              setManagers([]);
              setCustomers([]);
              setExpandedManagers(new Set());
              setSearchQuery("");
            }}
            className="p-1.5 hover:bg-gray-200 rounded-lg transition-colors"
            title="重置"
          >
            <RefreshCw className="h-4 w-4 text-gray-600" />
          </button>
        </div>
      </div>

      {/* 主内容区 - 全屏图谱，不使用 Card 组件 */}
      <div className="flex-1 w-full overflow-hidden border rounded-lg">
        <div className="h-full w-full flex flex-col">
          <div className="flex-1 w-full min-h-0">
            <ReactECharts
              ref={chartRef}
              option={option}
              style={{ height: "100%", width: "100%" }}
              opts={{ renderer: "canvas" }}
              onEvents={{
                click: (e: any) => {
                  if (e.data?.type === "industry") {
                    handleIndustryClick(e.data.name);
                  } else if (e.data?.type === "manager") {
                    handleManagerClick(e.data.name);
                  }
                },
              }}
            />
          </div>
          {/* 图例 */}
          <div className="border-t p-2 flex items-center justify-center gap-6 bg-white flex-shrink-0">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-[#0b9444]" />
              <span className="text-xs text-gray-700">行业</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-[#3b82f6]" />
              <span className="text-xs text-gray-700">经理</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-[#f97316]" />
              <span className="text-xs text-gray-700">客户</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-[#ef4444]" />
              <span className="text-xs text-gray-700">钻石级</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
