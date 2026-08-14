"use client";

import ReactECharts, { type EChartsOption } from "echarts-for-react";
import { ArrowLeftIcon, SearchIcon } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import { cn } from "@/lib/utils";

interface GraphNode {
  id: string;
  name: string;
  category: number;  // 0=行业，1=经理，2=客户
  value: number;
  customerCount?: number;
  industry?: string;
  team?: string;
  manager?: string;
  managers?: string[];  // 客户关联的所有经理
  org?: string;  // 所属机构
}

interface DrillState {
  type: "industry";
  name: string;
}

const INDUSTRY_COLORS: Record<string, string> = {
  "商企类": "#0b9444",
  "政务类": "#2563eb",
  "电商类": "#f97316",
  "国际类": "#7c3aed",
  "散户类": "#0891b2",
  "物流类": "#ca8a04",
};

function fmtRevenue(v: number | undefined | null): string {
  if (v == null || Number.isNaN(v)) return "未知";
  if (v >= 10000) return `${(v / 10000).toFixed(2)}亿`;
  return `${v.toLocaleString("zh-CN", { maximumFractionDigits: 1 })}万`;
}

export function KnowledgeGraphSimple() {
  const [nodes, setNodes] = useState<GraphNode[]>([]);
  const [links, setLinks] = useState<any[]>([]);
  const [activeIndustry, setActiveIndustry] = useState<string | null>(null);
  const [query, setQuery] = useState("");
  const [hideEmptyManagers, setHideEmptyManagers] = useState(false);  // 隐藏无客户的经理

  // 加载行业
  useEffect(() => {
    fetch("/api/knowledge-graph/industries")
      .then((r) => r.json())
      .then((data: any[]) => {
        console.log("【加载行业】", data);
        const graphNodes: GraphNode[] = data.map((ind) => ({
          id: `industry:${ind.name}`,
          name: ind.name,
          category: 0,
          value: ind.revenue,
          customerCount: ind.customer_count,
        }));
        console.log("【加载行业】", graphNodes.length, "个节点");
        setNodes(graphNodes);
        setLinks([]);  // 确保 links 初始化为空数组
      })
      .catch((e) => console.error("加载失败:", e));
  }, []);

  const industries = useMemo(() => {
    return nodes.filter((n) => n.category === 0).map((n) => n.name);
  }, [nodes]);

  // 过滤节点
  const filteredNodes = useMemo(() => {
    let result = [...nodes];
    
    // 行业筛选
    if (activeIndustry) {
      result = result.filter((n) => {
        if (n.category === 0) return n.name === activeIndustry;
        if (n.category === 1) return n.industry === activeIndustry;
        if (n.category === 2) return n.industry === activeIndustry;
        return true;
      });
    }
    
    // 搜索过滤
    if (query.trim()) {
      const q = query.toLowerCase();
      result = result.filter((n) => n.name.toLowerCase().includes(q));
    }
    
    // 隐藏无客户的经理
    if (hideEmptyManagers) {
      const managersWithCustomers = new Set(links
        .filter((l) => l.source.startsWith('manager:'))
        .map((l) => l.source)
      );
      result = result.filter((n) => {
        if (n.category !== 1) return true;  // 非经理节点保留
        return managersWithCustomers.has(n.id);
      });
    }
    
    return result;
  }, [nodes, activeIndustry, query, hideEmptyManagers, links]);

  // 下钻到行业
  const handleIndustryClick = async (industryName: string) => {
    setActiveIndustry(industryName);
    try {
      console.log("【下钻】加载", industryName, "的经理和客户");
      
      // 加载经理
      const managersRes = await fetch(`/api/knowledge-graph/industries/${encodeURIComponent(industryName)}/managers`);
      const managers = await managersRes.json();
      console.log("【经理数据】", managers.length, "个");
      
      // 加载客户
      const customersRes = await fetch(`/api/knowledge-graph/industries/${encodeURIComponent(industryName)}/customers`);
      const customers = await customersRes.json();
      console.log("【客户数据】", customers.length, "个");
      
      // 添加经理节点
      const managerNodes: GraphNode[] = managers.map((m: any) => ({
        id: `manager:${m.name}`,
        name: m.name,
        category: 1,
        value: m.revenue,
        customerCount: m.customer_count,
        industry: m.industry_name,
        team: m.teams?.[0],
      }));
      
      // 添加客户节点
      const customerNodes: GraphNode[] = customers.map((c: any) => ({
        id: `customer:${c.name}`,
        name: c.name,
        category: 2,
        value: c.revenue,
        industry: c.industry_name,
        manager: c.managers?.[0],  // 只记录第一个经理用于显示
        managers: c.managers || [],  // 保存所有经理
      }));
      
      // 合并节点（避免重复）
      const existingIds = new Set(nodes.map((n) => n.id));
      const newNodes = [
        ...managerNodes.filter((n) => !existingIds.has(n.id)),
        ...customerNodes.filter((n) => !existingIds.has(n.id)),
      ];
      
      // 构建边 - 支持多经理关联
      const newLinks = [
        // 行业->经理
        ...managerNodes.map((m) => ({
          source: `industry:${industryName}`,
          target: m.id,
        })),
        // 经理->客户（支持多对多）
        ...customerNodes.flatMap((c) => {
          const managers = c.managers || [];
          return managers.map((mgr: string) => ({
            source: `manager:${mgr}`,
            target: c.id,
          }));
        }),
      ];
      
      setNodes([...nodes, ...newNodes]);
      setLinks([...links, ...newLinks]);
      
      console.log("【下钻完成】新增节点:", newNodes.length, "新增边:", newLinks.length);
      console.log("【当前状态】总节点:", nodes.length + newNodes.length, "总边:", links.length + newLinks.length);
      
    } catch (e) {
      console.error("下钻失败:", e);
    }
  };

  const handleBack = () => {
    setActiveIndustry(null);
  };

  // ECharts 配置
  const option: EChartsOption = {
    title: {
      text: activeIndustry ? '' : '行业总览',
      left: 'center',
      top: 10,
      textStyle: {
        fontSize: 16,
        fontWeight: 'bold',
      },
    },
    subtitle: {
      text: activeIndustry ? '' : '点击行业下钻查看经理和客户',
      left: 'center',
      top: 35,
      textStyle: {
        fontSize: 12,
        color: '#666',
      },
    },
    tooltip: {
      show: true,
      trigger: 'item',  // 默认显示节点 tooltip
      formatter: (params: any) => {
        if (!params.data) return "";
        const node = params.data as GraphNode;
        let content = `<b>${node.name}</b><br/>`;
        content += `类型：${node.category === 0 ? "行业" : node.category === 1 ? "经理" : "客户"}<br/>`;
        content += `收入：${fmtRevenue(node.value)}<br/>`;
        if (node.customerCount) {
          content += `客户数：${node.customerCount}<br/>`;
        }
        if (node.industry) {
          content += `行业：${node.industry}<br/>`;
        }
        // 经理显示团队信息
        if (node.category === 1 && node.team) {
          content += `团队：${node.team}<br/>`;
        }
        if (node.category === 1 && node.org) {
          content += `机构：${node.org}<br/>`;
        }
        // 客户显示多经理关联
        if (node.category === 2 && node.managers && node.managers.length > 0) {
          content += `关联经理：${node.managers.length} 个<br/>`;
          if (node.managers.length <= 5) {
            content += node.managers.join(", ");
          } else {
            content += node.managers.slice(0, 3).join(", ") + `...等${node.managers.length}人`;
          }
        }
        return content;
      },
    },
    // 添加 link tooltip
    axisPointer: {
      type: 'shadow',
    },
    series: [
        {
          type: "graph",
          layout: "force",
          data: filteredNodes,
          links: links,
          categories: [
            { name: "行业", itemStyle: { color: "#0b9444" } },
            { name: "客户经理", itemStyle: { color: "#2563eb" } },
            { name: "客户", itemStyle: { color: "#f97316" } },
          ],
          roam: true,
          label: {
            show: true,
            position: "right",
            formatter: (params: any) => params?.data?.name || "",
          },
          lineStyle: {
            color: "source",
            curveness: 0.1,
          },
          // Link tooltip
          tooltip: {
            show: true,
            formatter: (params: any) => {
              if (params.dataType !== 'edge') return '';
              const link = params.data;
              const source = link.source;
              const target = link.target;
              return `<b>${source} → ${target}</b>`;
            },
          },
          emphasis: {
            focus: "adjacency",
            lineStyle: {
              width: 4,
            },
          },
        force: {
          repulsion: activeIndustry ? 800 : 1500,
          edgeLength: activeIndustry ? 150 : 250,
        },
        symbolSize: (value: any) => {
          // value 可能是数字或对象，直接返回固定值
          return 50;
        },
        itemStyle: {
          color: (params: any) => {
            // params.data 才是节点数据
            const node = params?.data;
            if (!node) return "#999";
            const category = node.category;
            if (category === 0) return "#0b9444";  // 行业 - 绿
            if (category === 1) return "#2563eb";  // 经理 - 蓝
            if (category === 2) return "#f97316";  // 客户 - 橙
            return "#999";
          },
        },
        draggable: true,
        click: (params: any) => {
          if (!params?.data) return;
          const node = params.data as GraphNode;
          if (node.category === 0) {
            handleIndustryClick(node.name);
          }
        },
      },
    ],
  };

  return (
    <div className="flex size-full flex-col p-4 gap-4">
      {/* 顶部控制栏 */}
      <div className="flex items-center gap-4">
        {activeIndustry && (
          <button
            onClick={handleBack}
            className="flex items-center gap-1 rounded-md border px-3 py-1.5 text-sm hover:bg-accent"
          >
            <ArrowLeftIcon className="size-4" />
            返回总览
          </button>
        )}

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
                activeIndustry === ind ? "text-white" : "bg-muted hover:bg-accent"
              )}
              style={{
                backgroundColor: activeIndustry === ind ? INDUSTRY_COLORS[ind] : undefined,
              }}
            >
              {ind}
            </button>
          ))}
        </div>

        <div className="ml-auto flex items-center gap-2">
          {/* 隐藏空经理开关 */}
          <label className="flex items-center gap-2 text-sm cursor-pointer">
            <input
              type="checkbox"
              checked={hideEmptyManagers}
              onChange={(e) => setHideEmptyManagers(e.target.checked)}
              className="rounded border-gray-300"
            />
            <span>隐藏无客户经理</span>
          </label>
          
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
        <ReactECharts option={option} style={{ height: "100%", width: "100%" }} />
      </div>

      {/* 统计信息 */}
      <div className="shrink-0 text-sm text-muted-foreground">
        节点：{filteredNodes.length} 个 | 关系：{links.length} 条
        {activeIndustry && ` | 当前：${activeIndustry}`}
      </div>
    </div>
  );
}
