"use client";

import ReactECharts, { type EChartsOption, type EChartsReactProps } from "echarts-for-react";
import { SearchIcon } from "lucide-react";
import { useEffect, useRef, useState } from "react";

interface GraphNode {
  id: string;
  name: string;
  category: number;  // 0=行业，1=经理，2=客户
  value: number;
  customerCount?: number;
  revenue?: number;
  level?: string;
  industry?: string;
  team?: string;
  managers?: string[];
}

interface GraphLink {
  source: string;
  target: string;
}

function fmtRevenue(v: number | undefined | null): string {
  if (v == null || Number.isNaN(v)) return "未知";
  if (v >= 10000) return `${(v / 10000).toFixed(2)}亿`;
  return `${v.toLocaleString("zh-CN", { maximumFractionDigits: 1 })}万`;
}

export function KnowledgeGraphSimple() {
  const [nodes, setNodes] = useState<GraphNode[]>([]);
  const [links, setLinks] = useState<GraphLink[]>([]);
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(true);
  const [expandedIndustries, setExpandedIndustries] = useState<Set<string>>(new Set());
  const chartRef = useRef<ReactECharts | null>(null);

  // 只加载行业
  useEffect(() => {
    async function loadIndustries() {
      setLoading(true);
      try {
        console.log("【开始加载】行业列表");
        
        const industriesRes = await fetch("/api/knowledge-graph/industries");
        const industries = await industriesRes.json();
        console.log(`【行业】${industries.length} 个`);
        
        const industryNodes: GraphNode[] = industries.map((ind: any) => ({
          id: `industry:${ind.name}`,
          name: ind.name,
          category: 0,
          value: ind.revenue,
          customerCount: ind.customer_count,
        }));
        
        setNodes(industryNodes);
        setLinks([]);
        setLoading(false);
        
        console.log("【加载完成】", industryNodes.length, "个行业");
        
      } catch (e) {
        console.error("加载失败:", e);
        setLoading(false);
      }
    }
    
    loadIndustries();
  }, []);

  // 点击行业展开
  const handleIndustryClick = async (industryName: string) => {
    if (expandedIndustries.has(industryName)) {
      // 收起
      const newExpanded = new Set(expandedIndustries);
      newExpanded.delete(industryName);
      setExpandedIndustries(newExpanded);
      
      // 移除该行业的经理和客户节点
      setNodes(prev => prev.filter(n => {
        return n.category === 0 || n.industry !== industryName;
      }));
      setLinks(prev => prev.filter(l => {
        return !l.source.startsWith('manager:') && !l.target.startsWith('customer:');
      }));
      
      console.log(`【收起】${industryName}`);
      return;
    }
    
    // 展开
    setExpandedIndustries(new Set([...expandedIndustries, industryName]));
    setLoading(true);
    
    try {
      console.log(`【展开】加载${industryName}的经理和客户`);
      
      // 并行加载经理和客户
      const [managersRes, customersRes] = await Promise.all([
        fetch(`/api/knowledge-graph/industries/${encodeURIComponent(industryName)}/managers`),
        fetch(`/api/knowledge-graph/industries/${encodeURIComponent(industryName)}/customers`)
      ]);
      
      const managers = await managersRes.json();
      const customers = await customersRes.json();
      
      console.log(`【数据】经理：${managers.length}, 客户：${customers.length}`);
      
      // 创建经理节点
      const managerNodes: GraphNode[] = managers.map((m: any) => ({
        id: `manager:${m.name}`,
        name: m.name,
        category: 1,
        value: m.revenue,
        customerCount: m.customer_count,
        industry: industryName,
        team: m.teams?.[0],
      }));
      
      // 创建客户节点
      const customerNodes: GraphNode[] = customers.map((c: any) => ({
        id: `customer:${c.name}`,
        name: c.name,
        category: 2,
        value: c.revenue,
        level: c.level,
        industry: c.industry2 || industryName,
        managers: c.managers || [],
      }));
      
      // 构建边
      const industryLinks: GraphLink[] = managerNodes.map((m) => ({
        source: `industry:${industryName}`,
        target: m.id,
      }));
      
      const managerCustomerLinks: GraphLink[] = customerNodes.flatMap((c) => {
        const mgrs = c.managers || [];
        return mgrs.map((mgr: string) => ({
          source: `manager:${mgr}`,
          target: c.id,
        }));
      });
      
      // 添加节点和边
      setNodes(prev => [...prev, ...managerNodes, ...customerNodes]);
      setLinks(prev => [...prev, ...industryLinks, ...managerCustomerLinks]);
      
      console.log(`【完成】新增节点：${managerNodes.length + customerNodes.length}, 新增边：${industryLinks.length + managerCustomerLinks.length}`);
      
    } catch (e) {
      console.error("加载失败:", e);
    } finally {
      setLoading(false);
    }
  };

  // 过滤节点
  const filteredNodes = nodes.filter((n) => {
    if (!query.trim()) return true;
    const q = query.toLowerCase();
    return n.name.toLowerCase().includes(q);
  });

  // ECharts 配置
  const option: EChartsOption = {
    tooltip: {
      show: true,
      trigger: "item",
      formatter: (params: any) => {
        if (!params.data) return "";
        const node = params.data as GraphNode;
        let content = `<b>${node.name}</b><br/>`;
        content += `类型：${node.category === 0 ? "行业" : node.category === 1 ? "经理" : "客户"}<br/>`;
        content += `收入：${fmtRevenue(node.value)}<br/>`;
        if (node.category === 0 && node.customerCount) {
          content += `客户数：${node.customerCount}<br/>`;
          content += `<span style="color:blue;cursor:pointer;">👆 点击展开/收起</span>`;
        }
        if (node.category === 1 && node.customerCount) {
          content += `客户数：${node.customerCount}<br/>`;
          content += `行业：${node.industry}`;
        }
        if (node.category === 2 && node.level) {
          content += `等级：${node.level}<br/>`;
          content += `行业：${node.industry}`;
        }
        return content;
      },
    },
    series: [
      {
        type: "graph",
        layout: "force",
        data: filteredNodes,
        links: links,
        categories: [
          { name: "行业", itemStyle: { color: "#0b9444" } },
          { name: "经理", itemStyle: { color: "#3b82f6" } },
          { name: "客户", itemStyle: { color: "#f97316" } },
        ],
        roam: true,
        zoom: 1.2,
        label: {
          show: true,
          position: "right",
          formatter: (params: any) => {
            const node = params.data as GraphNode;
            // 只显示行业和客户名称，经理用点表示避免太拥挤
            if (node.category === 0 || node.category === 2) {
              return node.name;
            }
            return "";
          },
          fontSize: node => node.category === 0 ? 14 : node.category === 2 ? 10 : 8,
        },
        labelLayout: {
          hideOverlap: true,
        },
        lineStyle: {
          color: "source",
          curveness: 0.3,
          width: 1,
        },
        emphasis: {
          focus: "adjacency",
          lineStyle: {
            width: 4,
          },
        },
        force: {
          repulsion: 300,
          edgeLength: [50, 150],
          gravity: 0.1,
        },
        initialRadius: node => node.category === 0 ? 30 : node.category === 1 ? 15 : 8,
      },
    ],
  };

  // 处理图表初始化后的点击事件
  const onChartReady = (chartInstance: any) => {
    chartInstance.on("click", (params: any) => {
      if (params.dataType === "node" && params.data.category === 0) {
        // 点击行业节点
        handleIndustryClick(params.data.name);
      }
    });
  };

  return (
    <div className="w-full h-[calc(100vh-140px)] flex flex-col gap-2 p-2">
      {/* 顶部工具栏 */}
      <div className="flex items-center justify-between px-4 py-2 bg-white border border-gray-200 rounded-lg shadow-sm flex-shrink-0">
        <div className="flex items-center gap-4">
          <h2 className="text-lg font-bold text-gray-900">客户关系图谱</h2>
          <span className="text-sm text-gray-500">
            行业 · 客户经理 · 客户
          </span>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 text-sm">
            <span className="flex items-center gap-1">
              <span className="w-3 h-3 rounded-full bg-green-600"></span>
              行业
            </span>
            <span className="flex items-center gap-1">
              <span className="w-3 h-3 rounded-full bg-blue-500"></span>
              经理
            </span>
            <span className="flex items-center gap-1">
              <span className="w-3 h-3 rounded-full bg-orange-500"></span>
              客户
            </span>
          </div>
          <div className="relative">
            <input
              type="text"
              placeholder="搜索..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              className="pl-8 pr-3 py-1.5 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <SearchIcon className="w-4 h-4 text-gray-400 absolute left-2.5 top-1/2 -translate-y-1/2" />
          </div>
        </div>
      </div>

      {/* 图谱区域 */}
      <div className="flex-1 bg-white border border-gray-200 rounded-lg shadow-sm overflow-hidden">
        {loading ? (
          <div className="w-full h-full flex items-center justify-center">
            <div className="text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
              <p className="text-gray-600">加载中...</p>
              <p className="text-sm text-gray-500 mt-2">正在加载 {nodes.length} 个节点</p>
            </div>
          </div>
        ) : (
          <ReactECharts
            option={option}
            style={{ height: "100%", width: "100%" }}
            opts={{ renderer: "canvas" }}
            onChartReady={onChartReady}
          />
        )}
      </div>
    </div>
  );
}
