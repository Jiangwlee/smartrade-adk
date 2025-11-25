"use client";

import { CopilotChat } from "@copilotkit/react-ui";

import { smartradeAssistantLabels } from "@/lib/copilotkit/copilot-labels";
import { useCopilotToolCallRenderer } from "@/lib/copilotkit/use-copilot-tool-call-renderer";

export function CopilotChatWrapper() {
  useCopilotToolCallRenderer();

  return (
    <div className="chat-wrapper flex flex-col flex-1 min-h-0 h-full w-full max-w-3xl mx-auto self-stretch">
      <CopilotChat
        className="chat-fill flex flex-1 min-h-0 h-full w-full flex-col overflow-hidden"
        labels={smartradeAssistantLabels}
      />
    </div>
  );
}
