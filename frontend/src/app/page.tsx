import { Footer } from "@/components/landing/footer";
import { Header } from "@/components/landing/header";
import { Hero } from "@/components/landing/hero";

export default function LandingPage() {
  return (
    <div className="min-h-screen w-full overflow-x-clip bg-[#0a0a0a]">
      <Header />
      <main className="flex w-full flex-col">
        <Hero />
        {/* 邮览官专注于邮政经营分析 */}
        <div className="container-md mx-auto px-4 py-16 text-center">
          <h2 className="text-3xl font-bold mb-6">邮览官能帮您做什么？</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 max-w-6xl mx-auto">
            <div className="p-6 bg-white/5 rounded-lg">
              <div className="text-4xl mb-4">📊</div>
              <h3 className="text-xl font-semibold mb-2">智能问数</h3>
              <p className="text-muted-foreground">自然语言查询邮政业务数据</p>
            </div>
            <div className="p-6 bg-white/5 rounded-lg">
              <div className="text-4xl mb-4">🔍</div>
              <h3 className="text-xl font-semibold mb-2">业务诊断</h3>
              <p className="text-muted-foreground">服务质量智能分析与预警</p>
            </div>
            <div className="p-6 bg-white/5 rounded-lg">
              <div className="text-4xl mb-4">📈</div>
              <h3 className="text-xl font-semibold mb-2">趋势预测</h3>
              <p className="text-muted-foreground">业务量与收入智能预测</p>
            </div>
            <div className="p-6 bg-white/5 rounded-lg">
              <div className="text-4xl mb-4">🗺️</div>
              <h3 className="text-xl font-semibold mb-2">网络优化</h3>
              <p className="text-muted-foreground">三级物流体系智能规划</p>
            </div>
          </div>
        </div>
      </main>
      <Footer />
    </div>
  );
}
