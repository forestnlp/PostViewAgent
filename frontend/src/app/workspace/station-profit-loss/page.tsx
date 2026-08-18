"use client";

import ReactECharts, { type EChartsOption } from "echarts-for-react";
import { useEffect, useState } from "react";
import { BarChart3, TrendingUp, AlertTriangle, RefreshCw } from "lucide-react";

import {
  WorkspaceBody,
  WorkspaceContainer,
  WorkspaceHeader,
} from "@/components/workspace/workspace-container";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

// ===================== 类型 =====================
interface Region {
  company: string;
  region: string;
}

interface RankingItem {
  period: string;
  company: string;
  region: string;
  网点名称: string;
  营业利润_单月: number;
}

interface AlertItem {
  网点名称: string;
  region: string;
  连续亏损月数: number;
  累计亏损: number;
  预警等级: string;
}

interface TrendItem {
  period: string;
  营业利润_单月: number;
  环比变化: number;
  环比变化率: number;
}

// ===================== 工具函数 =====================
function fmtMoney(v: number | null | undefined): string {
  if (v == null || Number.isNaN(v)) return "-";
  const abs = Math.abs(v);
  if (abs >= 100000000) return `${(v / 100000000).toFixed(2)}亿`;
  if (abs >= 10000) return `${(v / 10000).toFixed(1)}万`;
  return v.toFixed(0);
}

const levelColor: Record<string, string> = {
  高危: "bg-red-500/10 text-red-400",
  中危: "bg-orange-500/10 text-orange-400",
  低危: "bg-yellow-500/10 text-yellow-400",
};

// ===================== 页面 =====================
export default function StationProfitLossPage() {
  const [regions, setRegions] = useState<Region[]>([]);
  const [selectedCompany, setSelectedCompany] = useState<string>("");
  const [selectedPeriod, setSelectedPeriod] = useState<string>("2026-06");
  const [ranking, setRanking] = useState<{ red: RankingItem[]; black: RankingItem[] }>({ red: [], black: [] });
  const [alerts, setAlerts] = useState<AlertItem[]>([]);
  const [trend, setTrend] = useState<TrendItem[]>([]);
  const [loading, setLoading] = useState(false);

  // 加载区公司列表
  useEffect(() => {
    fetch("/api/station-profit-loss/regions")
      .then((r) => r.json())
      .then((data: Region[]) => {
        setRegions(data);
        if (data.length > 0 && data[0]) setSelectedCompany(data[0].company);
      })
      .catch((e) => console.error("加载区公司失败:", e));
  }, []);

  // 加载数据
  useEffect(() => {
    if (!selectedCompany) return;
    setLoading(true);
    const company = encodeURIComponent(selectedCompany);
    const period = encodeURIComponent(selectedPeriod);
    Promise.all([
      fetch(`/api/station-profit-loss/ranking?company=${company}&period=${period}&type=both&top_n=5`).then((r) => r.json()),
      fetch(`/api/station-profit-loss/alert?company=${company}&months=3`).then((r) => r.json()),
      fetch(`/api/station-profit-loss/trend?company=${company}&metric=营业利润`).then((r) => r.json()),
    ])
      .then(([rankingData, alertData, trendData]) => {
        setRanking({
          red: rankingData?.red ?? [],
          black: rankingData?.black ?? [],
        });
        setAlerts(alertData ?? []);
        setTrend(trendData ?? []);
        setLoading(false);
      })
      .catch((e) => {
        console.error("加载数据失败:", e);
        setLoading(false);
      });
  }, [selectedCompany, selectedPeriod]);

  // 红黑榜柱状图
  const rankingOption: EChartsOption = {
    tooltip: { trigger: "axis" },
    legend: { data: ["红榜", "黑榜"] },
    grid: { left: 60, right: 20, top: 40, bottom: 40 },
    xAxis: { type: "category", data: ranking.red.map((r) => r.网点名称) },
    yAxis: { type: "value", name: "单月营业利润(元)" },
    series: [
      {
        name: "红榜",
        type: "bar",
        data: ranking.red.map((r) => r.营业利润_单月),
        itemStyle: { color: "#e74c3c" },
      },
    ],
  };

  // 趋势折线图
  const trendOption: EChartsOption = {
    tooltip: { trigger: "axis" },
    grid: { left: 60, right: 20, top: 40, bottom: 40 },
    xAxis: { type: "category", data: trend.map((t) => t.period) },
    yAxis: { type: "value", name: "单月营业利润(元)" },
    series: [
      {
        name: "营业利润",
        type: "line",
        data: trend.map((t) => t.营业利润_单月),
        smooth: true,
        areaStyle: { opacity: 0.2 },
      },
    ],
  };

  return (
    <WorkspaceContainer>
      <WorkspaceHeader></WorkspaceHeader>
      <WorkspaceBody>
        <div className="size-full overflow-auto">
          <div className="mx-auto max-w-(--container-width-md) px-4 py-8">
            {/* 标题区 */}
            <div className="mb-6 flex items-center gap-3">
              <div className="flex size-10 items-center justify-center rounded-lg bg-[#006633]/10">
                <BarChart3 className="size-5 text-[#006633]" />
              </div>
              <div>
                <h1 className="text-2xl font-bold">网点损益分析</h1>
                <p className="text-muted-foreground text-sm">
                  18个月 × 13区 × 263网点 · 查询/红黑榜/预警/趋势/仿真
                </p>
              </div>
            </div>

            {/* 筛选区 */}
            <div className="mb-6 flex flex-wrap items-center gap-3">
              <select
                value={selectedCompany}
                onChange={(e) => setSelectedCompany(e.target.value)}
                className="rounded-lg border border-border/50 bg-card/50 px-3 py-2 text-sm"
              >
                {regions.map((r) => (
                  <option key={r.company} value={r.company}>
                    {r.region}
                  </option>
                ))}
              </select>
              <select
                value={selectedPeriod}
                onChange={(e) => setSelectedPeriod(e.target.value)}
                className="rounded-lg border border-border/50 bg-card/50 px-3 py-2 text-sm"
              >
                {["2026-06", "2026-05", "2026-04", "2026-03", "2026-02", "2026-01",
                  "2025-12", "2025-11", "2025-10", "2025-09", "2025-08", "2025-07"].map((p) => (
                  <option key={p} value={p}>
                    {p}
                  </option>
                ))}
              </select>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setSelectedCompany(selectedCompany)}
                disabled={loading}
              >
                <RefreshCw className={`size-4 ${loading ? "animate-spin" : ""}`} />
                刷新
              </Button>
            </div>

            {/* 红黑榜 */}
            <div className="mb-6 grid grid-cols-1 gap-4 lg:grid-cols-2">
              <Card className="p-4">
                <h2 className="mb-3 flex items-center gap-2 text-sm font-semibold">
                  <span className="size-2 rounded-full bg-red-500" />
                  红榜（盈利 TOP5）
                </h2>
                <div className="space-y-2">
                  {ranking.red.map((r, i) => (
                    <div key={i} className="flex items-center justify-between rounded-lg bg-card/50 px-3 py-2 text-sm">
                      <span className="font-medium">{i + 1}. {r.网点名称}</span>
                      <span className="text-red-400">+{fmtMoney(r.营业利润_单月)}</span>
                    </div>
                  ))}
                </div>
              </Card>
              <Card className="p-4">
                <h2 className="mb-3 flex items-center gap-2 text-sm font-semibold">
                  <span className="size-2 rounded-full bg-green-500" />
                  黑榜（亏损 TOP5）
                </h2>
                <div className="space-y-2">
                  {ranking.black.map((r, i) => (
                    <div key={i} className="flex items-center justify-between rounded-lg bg-card/50 px-3 py-2 text-sm">
                      <span className="font-medium">{i + 1}. {r.网点名称}</span>
                      <span className="text-green-400">{fmtMoney(r.营业利润_单月)}</span>
                    </div>
                  ))}
                </div>
              </Card>
            </div>

            {/* 趋势图 */}
            <Card className="mb-6 p-4">
              <h2 className="mb-3 flex items-center gap-2 text-sm font-semibold">
                <TrendingUp className="size-4 text-[#006633]" />
                营业利润月度趋势
              </h2>
              <ReactECharts option={trendOption} style={{ height: 300 }} />
            </Card>

            {/* 亏损预警 */}
            <Card className="p-4">
              <h2 className="mb-3 flex items-center gap-2 text-sm font-semibold">
                <AlertTriangle className="size-4 text-orange-400" />
                亏损预警（连续3个月）
              </h2>
              {alerts.length === 0 ? (
                <p className="text-muted-foreground text-sm">该区无连续3个月亏损网点</p>
              ) : (
                <div className="space-y-2">
                  {alerts.map((a, i) => (
                    <div key={i} className="flex items-center justify-between rounded-lg bg-card/50 px-3 py-2 text-sm">
                      <div className="flex items-center gap-2">
                        <Badge className={levelColor[a.预警等级]}>{a.预警等级}</Badge>
                        <span className="font-medium">{a.网点名称}</span>
                      </div>
                      <span className="text-muted-foreground">
                        连续{a.连续亏损月数}月 · 累计{fmtMoney(a.累计亏损)}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </Card>
          </div>
        </div>
      </WorkspaceBody>
    </WorkspaceContainer>
  );
}
