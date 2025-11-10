"use client";

import { CopilotChat } from "@copilotkit/react-ui";

import { smartradeAssistantLabels } from "@/lib/copilot-labels";
import { useCopilotToolCallRenderer } from "@/lib/use-copilot-tool-call-renderer";

export function CopilotChatWrapper() {
  useCopilotToolCallRenderer();

  return (
    <div className="w-full max-w-3xl mx-auto">
      <CopilotChat className="w-full" labels={smartradeAssistantLabels} />
    </div>
  );
}
