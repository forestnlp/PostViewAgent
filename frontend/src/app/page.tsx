import Link from "next/link";

import { Footer } from "@/components/landing/footer";
import { Header } from "@/components/landing/header";
import { Hero } from "@/components/landing/hero";

const featureCards = [
  {
    icon: "📊",
    title: "智能问数",
    description: "自然语言查询邮政业务数据",
    prompt: "查询武汉市前10名商企客户的业务量排名",
  },
  {
    icon: "🔍",
    title: "业务诊断",
    description: "服务质量智能分析与预警",
    prompt: "分析武汉市减收最严重的区县是什么？主要原因是什么？",
  },
  {
    icon: "📈",
    title: "趋势预测",
    description: "业务量与收入智能预测",
    prompt: "查询所有特级大客户的名单，并说明特级大客户的判定标准是什么？",
  },
  {
    icon: "🗺️",
    title: "客户分析",
    description: "客户分级与流失预警分析",
    prompt: "找出武汉市收入超过100万的重点客户，并说明VIP客户的分级标准",
  },
];

export default function LandingPage() {
  return (
    <div className="min-h-screen w-full overflow-x-clip bg-[#0a0a0a]">
      <Header hideOnHome={true} /> {/* 首页隐藏 Header */}
      <main className="flex w-full flex-col">
        <Hero />
        {/* 邮览官专注于邮政经营分析 */}
        <div className="container-md mx-auto px-4 py-16 text-center">
          <h2 className="mb-6 text-3xl font-bold">邮览官能帮您做什么？</h2>
          <div className="mx-auto grid max-w-6xl grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-4">
            {featureCards.map((card) => (
              <Link
                key={card.title}
                href={`/workspace/chats/new?q=${encodeURIComponent(card.prompt)}`}
                className="rounded-lg bg-white/5 p-6 transition-colors hover:bg-white/10"
              >
                <div className="mb-4 text-4xl">{card.icon}</div>
                <h3 className="mb-2 text-xl font-semibold">{card.title}</h3>
                <p className="text-muted-foreground">{card.description}</p>
              </Link>
            ))}
          </div>
        </div>
      </main>
      <Footer />
    </div>
  );
}
