"use client";

import { CopilotSidebar } from "@copilotkit/react-ui";
import { ReactNode } from "react";

import { smartradeAssistantLabels } from "@/lib/copilotkit/copilot-labels";
import { useCopilotToolCallRenderer } from "@/lib/copilotkit/use-copilot-tool-call-renderer";

export function CopilotSidebarWrapper({ children }: { children: ReactNode }) {
  useCopilotToolCallRenderer();

  return (
    <CopilotSidebar
      defaultOpen
      clickOutsideToClose={false}
      labels={smartradeAssistantLabels}
    >
      {children}
    </CopilotSidebar>
  );
}
