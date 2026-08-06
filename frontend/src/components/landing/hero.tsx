"use client";

import { ChevronRightIcon } from "lucide-react";
import { AnimatePresence, motion } from "motion/react";
import Link from "next/link";
import { useEffect, useState } from "react";

import { AuroraText } from "@/components/ui/aurora-text";
import { Button } from "@/components/ui/button";
import { FlickeringGrid } from "@/components/ui/flickering-grid";
import { cn } from "@/lib/utils";

const HERO_WORDS = [
  "智能问数",
  "业务诊断",
  "趋势预测",
  "网络优化",
  "寄递分析",
  "服务质量",
  "业务量预测",
  "物流规划",
  "数据可视化",
  "智能决策",
  "邮政分析",
  "智能体协作",
];

export function Hero({ className }: { className?: string }) {
  return (
    <div
      className={cn(
        "relative flex size-full flex-col items-center justify-center overflow-hidden",
        className,
      )}
    >
      {/* 渐变背景层 */}
      <div className="absolute inset-0 z-0">
        {/* 深绿到黑的渐变 */}
        <div className="absolute inset-0 bg-gradient-to-br from-[#0a1f0d] via-[#051406] to-black" />

        {/* 邮政绿色光晕 - 更柔和 */}
        <div className="absolute inset-0">
          <div className="absolute top-1/4 left-1/4 h-[800px] w-[800px] rounded-full bg-[#0B9444] opacity-20 blur-[200px]" />
          <div className="absolute right-1/4 bottom-1/4 h-[600px] w-[600px] rounded-full bg-[#00d166] opacity-15 blur-[180px]" />
          <div className="absolute top-1/2 left-1/2 h-[1000px] w-[1000px] -translate-x-1/2 -translate-y-1/2 transform rounded-full bg-[#008C45] opacity-10 blur-[250px]" />
        </div>

        {/* 细网格线 - 更精致 */}
        <div className="absolute inset-0 opacity-[0.03]">
          <div
            className="h-full w-full"
            style={{
              backgroundImage: `
                linear-gradient(rgba(11, 148, 68, 0.5) 1px, transparent 1px),
                linear-gradient(90deg, rgba(11, 148, 68, 0.5) 1px, transparent 1px)
              `,
              backgroundSize: "60px 60px",
            }}
          />
        </div>
      </div>

      {/* 邮政绿色粒子效果 */}
      <FlickeringGrid
        className="absolute inset-0 z-10"
        squareSize={3}
        gridGap={6}
        color="#0B9444"
        maxOpacity={0.35}
        flickerChance={0.3}
      />

      {/* 内容层 */}
      <div className="container-md relative z-10 mx-auto flex min-h-[92svh] flex-col items-center justify-center px-4 pt-20 pb-14">
        {/* Logo 和标题 */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="text-center"
        >
          <h1 className="text-center text-6xl leading-tight font-bold break-words md:text-7xl lg:text-8xl">
            <span className="bg-gradient-to-r from-[#0B9444] via-[#00d166] to-[#0B9444] bg-clip-text text-transparent">
              邮览官
            </span>
          </h1>
        </motion.div>

        {/* 动态关键词 */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.2 }}
          className="mt-6 flex w-full max-w-4xl items-center justify-center gap-3 text-center"
        >
          <div className="text-2xl font-semibold text-white md:text-3xl lg:text-4xl">
            <HeroWordRotate words={HERO_WORDS} />
          </div>
          <span className="hidden text-lg font-medium text-[#0B9444] sm:inline-block">
            |
          </span>
          <span className="text-lg font-medium text-[#0B9444]">
            邮政经营分析智能体
          </span>
        </motion.div>

        {/* 描述文字 */}
        <motion.p
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.4 }}
          className="mt-8 max-w-3xl text-center text-lg leading-8 text-[#a0d4b8] md:text-xl"
        >
          基于先进的 AI 智能体架构，采用内网垂直模型，确保数据安全。
          邮览官能够智能分析邮政业务数据、诊断服务质量、预测业务趋势，
          为邮政经营决策提供全方位智能支持。
        </motion.p>

        {/* 按钮组 */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.6 }}
          className="mt-10"
        >
          <Link href="/workspace">
            <Button
              className="h-12 border-0 bg-[#0B9444] px-8 text-base text-white shadow-lg shadow-[#0B9444]/30 transition-all duration-300 hover:bg-[#00d166]"
              size="lg"
            >
              <span>开始使用</span>
              <ChevronRightIcon className="ml-2 size-5" />
            </Button>
          </Link>
        </motion.div>
      </div>

      {/* 底部装饰线 */}
      <div className="absolute right-0 bottom-0 left-0 h-px bg-gradient-to-r from-transparent via-[#0B9444]/30 to-transparent" />
    </div>
  );
}

function HeroWordRotate({
  words,
  duration = 2200,
}: {
  words: string[];
  duration?: number;
}) {
  const [index, setIndex] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setIndex((prevIndex) => (prevIndex + 1) % words.length);
    }, duration);

    return () => clearInterval(interval);
  }, [words, duration]);

  return (
    <div className="relative max-w-full min-w-0 overflow-hidden py-2">
      <AnimatePresence mode="popLayout">
        <motion.div
          key={index}
          className="max-w-full"
          initial={{ opacity: 0, y: -50, filter: "blur(16px)" }}
          animate={{ opacity: 1, y: 0, filter: "blur(0px)" }}
          exit={{ opacity: 0, y: 50, filter: "blur(16px)" }}
          transition={{ duration: 0.3, ease: "easeOut" }}
        >
          <AuroraText
            className="max-w-full [overflow-wrap:anywhere] whitespace-normal"
            speed={3}
            colors={["#efefbb", "#e9c665", "#e3a812"]}
          >
            {words[index]}
          </AuroraText>
        </motion.div>
      </AnimatePresence>
    </div>
  );
}
