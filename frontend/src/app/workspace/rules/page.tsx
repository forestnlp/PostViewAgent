"use client";

import { BookOpenIcon, ChevronDownIcon, FileTextIcon, LayersIcon } from "lucide-react";
import { useState } from "react";

import {
  WorkspaceBody,
  WorkspaceContainer,
  WorkspaceHeader,
} from "@/components/workspace/workspace-container";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";

// ===================== 业务规则 =====================
const businessRules = [
  { name: "customer_tier", title: "寄递客户分档", category: "客户分层", boards: "寄递", summary: "5档分档体系（特级≥5万元）", details: ["特级（钻石）：上月累计收入 ≥ 50,000 元", "一级（铂金）：上月累计收入 ≥ 10,000 元", "二级（黄金）：上月累计收入 ≥ 3,000 元", "三级（白银）：上月累计收入 ≥ 500 元", "四级（普通）：上月累计收入 < 500 元"] },
  { name: "customer_segment", title: "客户细分", category: "客户分层", boards: "寄递", summary: "6类客户细分（活跃/休眠/高效/低效/有效/无效）", details: ["活跃客户：注册<6个月或180天内有收入", "休眠客户：注册≥6个月且180天内无收入", "高效客户：月均收入≥1000元或年累计≥10000元", "低效客户：月均收入<1000元或年累计<10000元", "有效客户：12个月内有过收入", "无效客户：注册≥2个月且12个月内无收入"] },
  { name: "vip_customer", title: "重点关注客户分级", category: "客户分层", boards: "寄递, 邮务", summary: "5级VIP分级 + 二级分级体系", details: ["1级：年收入 ≥ 100万", "2级：年收入 ≥ 200万", "3级：年收入 ≥ 300万", "4级：年收入 ≥ 500万", "5级：年收入 ≥ 1000万", "二级分级：[6万,12万) / [12万,60万) / [60万,100万)"] },
  { name: "loss_alert", title: "减收与流失判定", category: "风险预警", boards: "寄递", summary: "减收/月流失/年流失/预流失 4维判定", details: ["减收：今年当月收入 < 去年同月", "预流失预警：同比减收 ≥ 25% 且累计收入 > 1000元", "月流失预警：同比减收 ≥ 50%", "年流失：对比期有收入，统计期连续12个月收入为0"] },
  { name: "strategic_customer", title: "战略客户管理", category: "客户管理", boards: "寄递", summary: "集团/省/市三级战略客户 + 补录规则", details: ["三级架构：集团战略客户、省分公司战略客户、市公司战略客户", "补录金额上限：5000万元", "补录时间窗口：每月1日-9日", "审批流：行业主管创建→直接生效；行业经理创建→需主管审批"] },
  { name: "sales_opportunity_status", title: "商机跟进流程", category: "销售管理", boards: "邮务, 寄递", summary: "48h超时 + 30天有效期 + 2km打卡", details: ["48小时无跟进 → 退回线索池", "30天未注册赢单 → 退回线索池", "打卡校验：活动开启时需在客户2公里范围内打卡"] },
  { name: "customer_cancellation", title: "客户注销管理", category: "客户管理", boards: "邮务, 寄递", summary: "注销流程 + 2天外围系统校验 + 状态机", details: ["注销流程：申请→校验→审批→执行", "外围系统校验：2天等待期", "状态机：草稿→待校验→校验中→待审批→已注销/已驳回"] },
  { name: "business_relation_renewal", title: "业务关系续签", category: "客户管理", boards: "邮务, 寄递", summary: "4种续签场景 + 超时自动驳回", details: ["4种续签场景：正常续签、变更续签、合并续签、拆分续签", "超时自动驳回：超过续签期限未处理自动驳回"] },
  { name: "credit_management", title: "客户信用评级与增信管理", category: "风险管理", boards: "邮务, 寄递", summary: "9状态机 + 50万阈值 + 增信审批流", details: ["信用评级：9个状态流转", "50万阈值：超过50万需增信审批", "增信审批流：申请→审核→审批→生效"] },
  { name: "activity_status", title: "营销活动状态管理", category: "营销管理", boards: "邮务, 寄递", summary: "8状态流转 + 下发规则 + 赢单规则", details: ["8个状态：草稿→待审核→已审核→执行中→已暂停→已恢复→已结束→已终止", "下发规则：按组织架构层级下发", "赢单规则：按客户归属判定赢单"] },
  { name: "industry", title: "寄递翼行业分类", category: "基础数据", boards: "寄递", summary: "6大行业 + 11平台 + 10大项目", details: ["6大行业：政务/物流/商企/电商/国际/散户", "11大平台：国内电商/政务/生鲜/银行保险/通讯/快消B2B/汽车/高科技/医药/国际/其他", "10大重点项目：鞋服/互联网/国内电商TOP/车生态/司法/金融/保险/通讯/生鲜"] },
  { name: "kpi_assessment", title: "寄递客户经理KPI考核", category: "绩效考核", boards: "寄递", summary: "时限3必含 + 业务份额100%", details: ["时限要求：3个必含时限指标", "业务份额：目标达成率100%"] },
  { name: "performance_calculation", title: "营销人员业绩计算", category: "绩效考核", boards: "邮务, 寄递", summary: "折算系数公式", details: ["业绩计算：按折算系数公式计算", "适用对象：客户经理/客户主管"] },
  { name: "customer_level_management", title: "法定客户/业务关系等级计算", category: "客户管理", boards: "邮务, 寄递", summary: "4类计算规则", details: ["法定客户等级：按收入规模计算", "业务关系等级：按业务量计算", "4类计算规则覆盖不同客户类型"] },
  { name: "customer_query_rules", title: "客户数据权限与查询范围", category: "基础数据", boards: "邮务, 寄递", summary: "4级权限 + 排序规则", details: ["4级权限：总部/省/市/网点", "排序规则：按收入/业务量/客户名称排序"] },
  { name: "customer_graph", title: "客户图谱与企业规模判定", category: "客户管理", boards: "邮务, 寄递", summary: "4级规模判定 + 画像字段", details: ["4级规模：大型/中型/小型/微型", "画像字段：行业、区域、企业规模、业务特征"] },
  { name: "new_post_subscription", title: "新邮预订网点自提赢单计算", category: "营销管理", boards: "邮务", summary: "赢单逻辑", details: ["网点自提客户的赢单计算规则"] },
  { name: "organization_structure", title: "组织架构", category: "基础数据", boards: "邮务, 寄递", summary: "6级机构 + 5种专业", details: ["6级机构：总部→省→市→区县→网点→揽收段道", "5种专业：寄递、邮务、金融、保险、电商"] },
];

// ===================== 业务术语 =====================
const glossaryTerms: Record<string, { term: string; desc: string }[]> = {
  "客户类": [
    { term: "法定客户", desc: "客户主体（机构或个体）的法定身份，标识：主码（18位统一社会信用代码或身份证号）" },
    { term: "协议客户", desc: "与邮政签订寄递服务协议的客户，标识：子码" },
    { term: "业务关系", desc: "客户与邮政签订的具体业务关系（如寄递、营销），标识：业务关系码" },
    { term: "协议客户分类", desc: "协议/潜客/散客三类" },
    { term: "潜客", desc: "有意向但尚未签订协议的客户" },
    { term: "散客", desc: "个人临时寄递客户" },
  ],
  "客户等级": [
    { term: "钻石/特级大客户", desc: "月收入 >= 50000 元的寄递客户" },
    { term: "一级大客户", desc: "月收入 [10000, 50000) 元的寄递客户" },
    { term: "二级大客户", desc: "月收入 [5000, 10000) 元的寄递客户" },
    { term: "三级大客户", desc: "月收入 [1000, 5000) 元的寄递客户" },
    { term: "小微客户", desc: "月收入 < 1000 元的寄递客户" },
    { term: "重点关注客户", desc: "年收入 100 万及以上的客户，分 1-5 级" },
  ],
  "客户细分": [
    { term: "活跃客户", desc: "注册 < 6 个月 或 180 天内有收入" },
    { term: "休眠客户", desc: "注册 ≥ 6 个月 且 180 天内无收入" },
    { term: "高效客户", desc: "月均收入 >= 1000 元 或 年累计 >= 10000 元" },
    { term: "低效客户", desc: "月均收入 < 1000 元 或 年累计 < 10000 元" },
    { term: "有效客户", desc: "12 个月内有过收入" },
    { term: "无效客户", desc: "注册 ≥ 2 个月 且 12 个月内无收入" },
  ],
  "收入指标": [
    { term: "业务量", desc: "寄递件量" },
    { term: "业务收入", desc: "寄递服务收入" },
    { term: "件均单价", desc: "业务收入 / 业务量" },
    { term: "重量单价", desc: "业务收入 / 总重量" },
    { term: "月均收入", desc: "12 个月平均月收入" },
    { term: "客户单价", desc: "业务收入 / 客户数" },
  ],
  "生命周期": [
    { term: "注销", desc: "客户退出流程（不可逆）" },
    { term: "失效", desc: "业务关系状态不生效" },
    { term: "注销中", desc: "已申请注销，等待外围系统校验和人工审批" },
    { term: "减收", desc: "今年当月收入 < 去年同月" },
    { term: "月流失", desc: "今年当月无收入 + 去年当月有收入" },
    { term: "年流失", desc: "今年累计 1~N 月无收入 + 去年累计 1~N 月有收入" },
    { term: "预流失", desc: "同比下降 >= 25% 且累计收入 > 1000" },
  ],
  "营销类": [
    { term: "营销活动", desc: "针对特定客户群体的营销事件" },
    { term: "商机", desc: "有价值的销售机会（30天有效期）" },
    { term: "线索", desc: "待核实的销售机会" },
    { term: "赢单", desc: "商机转化为实际客户" },
    { term: "丢单", desc: "商机未达成" },
    { term: "营销管理中心", desc: "营销活动的总管理角色" },
    { term: "寄递营销网格", desc: "按客户地址匹配的营销区域" },
    { term: "电子围栏", desc: "营销活动按地理区域下发的范围" },
    { term: "营销网格员", desc: "负责网格内客户营销的一线人员" },
    { term: "网点", desc: "邮政自营或合作的服务网点" },
  ],
  "行业": [
    { term: "寄递翼6大行业", desc: "政务/物流/商企/电商/国际/散户" },
    { term: "11大行业平台", desc: "国内电商/政务/生鲜/银行保险/通讯/快消B2B/汽车/高科技/医药/国际/其他" },
    { term: "10大重点项目", desc: "鞋服/互联网/国内电商TOP/车生态/司法/金融/保险/通讯/生鲜" },
  ],
  "业务类": [
    { term: "寄递业务", desc: "邮政快递业务" },
    { term: "邮务业务", desc: "邮政传统业务（报刊、邮票、函件等）" },
    { term: "金融业务", desc: "代理金融业务" },
    { term: "特快", desc: "特快专递（EMS）" },
    { term: "快包", desc: "快递包裹（经济件）" },
    { term: "国际业务", desc: "国际寄递业务" },
    { term: "物流业务", desc: "合同物流" },
  ],
  "系统/数据类": [
    { term: "新一代寄递平台", desc: "寄递业务数据来源系统" },
    { term: "CRM系统", desc: "中国邮政CRM客户关系管理系统" },
    { term: "邮客行", desc: "邮政一线营销 APP" },
    { term: "邮E联", desc: "邮政企业即时通讯工具" },
    { term: "数据治理", desc: "业务数据的标准化管理" },
    { term: "KPI考核", desc: "关键绩效指标考核" },
    { term: "业务份额", desc: "邮政+竞品 = 100% 的业务分配" },
  ],
};

// ===================== 来源文档 =====================
const sourceDocuments: Record<string, string[]> = {
  "客户管理": ["客户管理分册V1.47", "客户信息采集", "客户洞察分册V1.52", "疑似客户合并", "客户注销子册V1.11"],
  "营销管理": ["营销管理分册V1.41", "活动管理子册V1.32", "三大靶向清单V1.19", "客户图谱V1.15", "新邮预订网点自提营销V1.10", "招标商机管理端V1.11", "招标商机CRM端"],
  "销售管理": ["销售管理分册V1.14", "业绩管理子册V1.10", "业绩管理V1.11", "物流价格库分册"],
  "邮客行": ["经营看板", "一线人员工作台V1.16", "客户运营驾驶舱V1.12"],
  "重点关注客户": ["PC端(1)", "PC端(2)", "邮客行端(1)", "邮客行端(2)"],
  "战略客户": ["战略客户管理(集团)", "战略客户管理(寄递)", "战略客户管理(邮务)"],
  "信用管理": ["信用管理分册(寄递)V1.22", "信用管理分册V1.22"],
  "基础数据": ["基础管理分册V1.25", "产品信息管理", "会员积分管理", "项目制考核", "配置管理中心", "360视图分册V1.15"],
  "知识管理": ["知识库管理分册V1.11", "知识库工单"],
};

// ===================== 样式 =====================
const categoryColors: Record<string, string> = {
  客户分层: "bg-blue-500/10 text-blue-400",
  风险预警: "bg-red-500/10 text-red-400",
  客户管理: "bg-green-500/10 text-green-400",
  销售管理: "bg-purple-500/10 text-purple-400",
  风险管理: "bg-orange-500/10 text-orange-400",
  营销管理: "bg-cyan-500/10 text-cyan-400",
  基础数据: "bg-gray-500/10 text-gray-400",
  绩效考核: "bg-yellow-500/10 text-yellow-400",
};

type TabKey = "rules" | "glossary" | "sources";

const tabs: { key: TabKey; label: string; icon: typeof BookOpenIcon; count: number }[] = [
  { key: "rules", label: "业务规则", icon: BookOpenIcon, count: businessRules.length },
  { key: "glossary", label: "业务术语", icon: LayersIcon, count: Object.values(glossaryTerms).flat().length },
  { key: "sources", label: "来源文档", icon: FileTextIcon, count: Object.values(sourceDocuments).flat().length },
];

// ===================== 页面 =====================
export default function RulesPage() {
  const [activeTab, setActiveTab] = useState<TabKey>("rules");
  const [expandedRule, setExpandedRule] = useState<string | null>(null);

  return (
    <WorkspaceContainer>
      <WorkspaceHeader></WorkspaceHeader>
      <WorkspaceBody>
        <div className="size-full overflow-hidden">
          <ScrollArea className="size-full">
            <div className="mx-auto max-w-(--container-width-md) px-4 py-8">
              {/* 标题区 */}
              <div className="mb-6 flex items-center gap-3">
                <div className="flex size-10 items-center justify-center rounded-lg bg-[#006633]/10">
                  <BookOpenIcon className="size-5 text-[#006633]" />
                </div>
                <div>
                  <h1 className="text-2xl font-bold">业务知识库</h1>
                  <p className="text-muted-foreground text-sm">
                    {businessRules.length} 条业务规则 · {Object.values(glossaryTerms).flat().length} 条业务术语 · {Object.values(sourceDocuments).flat().length} 份来源文档
                  </p>
                </div>
              </div>

              {/* Tab 切换 */}
              <div className="mb-6 flex gap-1 border-b border-border/50">
                {tabs.map((tab) => {
                  const Icon = tab.icon;
                  return (
                    <button
                      key={tab.key}
                      onClick={() => setActiveTab(tab.key)}
                      className={`flex items-center gap-2 px-4 py-2 text-sm font-medium transition-colors ${
                        activeTab === tab.key
                          ? "border-b-2 border-[#006633] text-[#006633]"
                          : "text-muted-foreground hover:text-foreground"
                      }`}
                    >
                      <Icon className="size-4" />
                      {tab.label}
                      <span className="rounded bg-muted px-1.5 py-0.5 text-xs">
                        {tab.count}
                      </span>
                    </button>
                  );
                })}
              </div>

              {/* 业务规则 Tab */}
              {activeTab === "rules" && (
                <div className="space-y-3">
                  {businessRules.map((rule) => (
                    <Collapsible
                      key={rule.name}
                      open={expandedRule === rule.name}
                      onOpenChange={(open) =>
                        setExpandedRule(open ? rule.name : null)
                      }
                    >
                      <CollapsibleTrigger className="w-full">
                        <div className="flex items-center gap-3 rounded-lg border border-border/50 bg-card/50 p-4 transition-colors hover:bg-card">
                          <div className="flex-1 text-left">
                            <div className="mb-1 flex items-center gap-2">
                              <span className="font-medium">{rule.title}</span>
                              <span className={`rounded px-1.5 py-0.5 text-xs ${categoryColors[rule.category] ?? ""}`}>
                                {rule.category}
                              </span>
                            </div>
                            <p className="text-muted-foreground text-sm">{rule.summary}</p>
                            <p className="text-muted-foreground/60 mt-1 text-xs">
                              {rule.boards} · {rule.name}.yaml
                            </p>
                          </div>
                          <ChevronDownIcon
                            className={`text-muted-foreground size-4 shrink-0 transition-transform ${expandedRule === rule.name ? "rotate-180" : ""}`}
                          />
                        </div>
                      </CollapsibleTrigger>
                      <CollapsibleContent>
                        <div className="ml-4 mt-2 space-y-2 border-l-2 border-border/30 pl-4">
                          {rule.details.map((detail, idx) => (
                            <div key={idx} className="text-muted-foreground flex items-start gap-2 text-sm">
                              <span className="mt-1.5 size-1 shrink-0 rounded-full bg-muted-foreground/50" />
                              <span>{detail}</span>
                            </div>
                          ))}
                        </div>
                      </CollapsibleContent>
                    </Collapsible>
                  ))}
                </div>
              )}

              {/* 业务术语 Tab */}
              {activeTab === "glossary" && (
                <div className="space-y-6">
                  {Object.entries(glossaryTerms).map(([category, terms]) => (
                    <div key={category}>
                      <h2 className="mb-3 flex items-center gap-2 text-sm font-semibold">
                        <span className="rounded bg-[#006633]/10 px-2 py-0.5 text-[#006633]">
                          {category}
                        </span>
                        <span className="text-muted-foreground text-xs">
                          {terms.length} 条
                        </span>
                      </h2>
                      <div className="grid grid-cols-1 gap-2 md:grid-cols-2">
                        {terms.map((item) => (
                          <div
                            key={item.term}
                            className="rounded-lg border border-border/50 bg-card/50 p-3"
                          >
                            <div className="font-medium text-sm">{item.term}</div>
                            <div className="text-muted-foreground mt-1 text-xs">
                              {item.desc}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {/* 来源文档 Tab */}
              {activeTab === "sources" && (
                <div className="space-y-6">
                  <div className="rounded-lg border border-[#006633]/20 bg-[#006633]/5 p-4">
                    <p className="text-sm">
                      知识库内容来源于 <span className="font-bold text-[#006633]">53份</span> 寄递CRM系统操作手册，
                      覆盖客户管理、营销管理、销售管理、邮客行、重点关注客户、战略客户、信用管理、基础数据、知识管理等
                      <span className="font-bold text-[#006633]"> 9大业务主题</span>。
                    </p>
                  </div>
                  {Object.entries(sourceDocuments).map(([category, docs]) => (
                    <div key={category}>
                      <h2 className="mb-3 flex items-center gap-2 text-sm font-semibold">
                        <span className="rounded bg-blue-500/10 px-2 py-0.5 text-blue-400">
                          {category}
                        </span>
                        <span className="text-muted-foreground text-xs">
                          {docs.length} 份文档
                        </span>
                      </h2>
                      <div className="flex flex-wrap gap-2">
                        {docs.map((doc) => (
                          <div
                            key={doc}
                            className="flex items-center gap-1.5 rounded-lg border border-border/50 bg-card/50 px-3 py-1.5 text-sm"
                          >
                            <FileTextIcon className="text-muted-foreground size-3.5" />
                            {doc}
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </ScrollArea>
        </div>
      </WorkspaceBody>
    </WorkspaceContainer>
  );
}
