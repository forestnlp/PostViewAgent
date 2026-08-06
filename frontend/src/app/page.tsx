import { Footer } from "@/components/landing/footer";
import { Header } from "@/components/landing/header";
import { Hero } from "@/components/landing/hero";

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
            <div className="rounded-lg bg-white/5 p-6">
              <div className="mb-4 text-4xl">📊</div>
              <h3 className="mb-2 text-xl font-semibold">智能问数</h3>
              <p className="text-muted-foreground">自然语言查询邮政业务数据</p>
            </div>
            <div className="rounded-lg bg-white/5 p-6">
              <div className="mb-4 text-4xl">🔍</div>
              <h3 className="mb-2 text-xl font-semibold">业务诊断</h3>
              <p className="text-muted-foreground">服务质量智能分析与预警</p>
            </div>
            <div className="rounded-lg bg-white/5 p-6">
              <div className="mb-4 text-4xl">📈</div>
              <h3 className="mb-2 text-xl font-semibold">趋势预测</h3>
              <p className="text-muted-foreground">业务量与收入智能预测</p>
            </div>
            <div className="rounded-lg bg-white/5 p-6">
              <div className="mb-4 text-4xl">🗺️</div>
              <h3 className="mb-2 text-xl font-semibold">网络优化</h3>
              <p className="text-muted-foreground">三级物流体系智能规划</p>
            </div>
          </div>
        </div>
      </main>
      <Footer />
    </div>
  );
}
