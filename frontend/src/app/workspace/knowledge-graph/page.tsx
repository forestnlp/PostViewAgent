"use client";

import { Network } from "lucide-react";

import {
  WorkspaceBody,
  WorkspaceContainer,
  WorkspaceHeader,
} from "@/components/workspace/workspace-container";
import { KnowledgeGraphSimple } from "@/components/workspace/knowledge-graph-simple";

export default function KnowledgeGraphPage() {
  return (
    <WorkspaceContainer>
      <WorkspaceHeader></WorkspaceHeader>
      <WorkspaceBody>
        <div className="flex size-full flex-col">
          {/* 标题区 */}
          <div className="flex shrink-0 items-center gap-3 px-4 pt-4">
            <div className="flex size-10 items-center justify-center rounded-lg bg-[#0b9444]/10">
              <Network className="size-5 text-[#0b9444]" />
            </div>
            <div>
              <h1 className="text-xl font-bold">客户关系图谱</h1>
              <p className="text-muted-foreground text-xs">
                行业 · 客户经理 · 客户 · 团队
              </p>
            </div>
          </div>

          {/* 图谱画布 */}
          <div className="min-h-0 flex-1 pt-2">
            <KnowledgeGraphSimple />
          </div>
        </div>
      </WorkspaceBody>
    </WorkspaceContainer>
  );
}
