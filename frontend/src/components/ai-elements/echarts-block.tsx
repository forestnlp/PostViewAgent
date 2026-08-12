"use client";

import { parse as lenientParse } from "best-effort-json-parser";
import ReactECharts, { type EChartsOption } from "echarts-for-react";
import { useMemo, useState } from "react";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

/**
 * Tolerate LLM-produced JSON quirks: unescaped literal newlines inside string
 * values (e.g. a `\n` that the model wrote as a real line break), trailing
 * commas, etc. First try strict parsing; fall back to a lenient parser that
 * fixes the most common issues.
 */
function parseEChartsOption(raw: string): unknown {
  try {
    return JSON.parse(raw);
  } catch {
    // best-effort-json-parser fixes unescaped newlines, trailing commas and
    // other common LLM JSON mistakes.
    return lenientParse(raw);
  }
}

/**
 * Renders a fenced code block with the `echarts` language as an interactive
 * ECharts chart. The code block content must be a valid ECharts option JSON.
 *
 * Example:
 *
 * ```echarts
 * {
 *   "tooltip": {},
 *   "series": [{ "type": "pie", "data": [{ "name": "电商类", "value": 2974 }] }]
 * }
 * ```
 */
export function EChartsBlock({
  code,
  className,
}: {
  code: string;
  className?: string;
}) {
  const [error, setError] = useState<string | null>(null);

  const option = useMemo<EChartsOption | null>(() => {
    try {
      const parsed = parseEChartsOption(code);
      if (parsed && typeof parsed === "object") {
        return parsed as EChartsOption;
      }
      setError("图表配置必须是 JSON 对象");
      return null;
    } catch (e) {
      setError(e instanceof Error ? e.message : "图表配置解析失败");
      return null;
    }
  }, [code]);

  if (error) {
    return (
      <div
        className={cn(
          "my-4 w-full overflow-hidden rounded-xl border border-dashed border-destructive",
          className,
        )}
      >
        <div className="bg-destructive/10 text-destructive p-3 text-xs">
          ECharts 渲染失败：{error}
        </div>
        <pre className="bg-muted/40 overflow-x-auto p-4 font-mono text-xs">
          {code}
        </pre>
        <div className="p-3">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setError(null)}
            className="text-xs"
          >
            重试
          </Button>
        </div>
      </div>
    );
  }

  if (!option) {
    return null;
  }

  return (
    <div
      className={cn(
        "my-4 w-full overflow-hidden rounded-xl border bg-background",
        className,
      )}
    >
      <ReactECharts
        option={option}
        notMerge
        lazyUpdate
        style={{ height: 360, width: "100%" }}
        opts={{ renderer: "canvas" }}
      />
    </div>
  );
}
