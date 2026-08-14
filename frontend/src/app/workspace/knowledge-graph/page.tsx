"use client";

import { Network } from "lucide-react";

import {
  WorkspaceBody,
  WorkspaceContainer,
  WorkspaceHeader,
} from "@/components/workspace/workspace-container";
import KnowledgeGraphVisual from "@/components/workspace/knowledge-graph-visual";

export default function KnowledgeGraphPage() {
  return (
    <WorkspaceContainer>
      <WorkspaceHeader></WorkspaceHeader>
      <WorkspaceBody>
        <KnowledgeGraphVisual />
      </WorkspaceBody>
    </WorkspaceContainer>
  );
}
