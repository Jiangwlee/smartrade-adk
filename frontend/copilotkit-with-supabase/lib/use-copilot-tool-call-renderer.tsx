"use client";

import { ReactNode } from "react";
import { useRenderToolCall } from "@copilotkit/react-core";
import { Wrench } from "lucide-react";
import { CopilotToolCallCard } from "@/components/copilot-tool-call-card";

type Options = {
  description?: string;
  namePattern?: string;
  renderPendingBubble?: (name: string) => ReactNode;
};

const defaultDescription = "Render all ADK tool calls in the chat";

export function useCopilotToolCallRenderer(options?: Options) {
  const assistantMessageClass =
    "copilotKitMessage copilotKitAssistantMessage tool-call-message";

  useRenderToolCall({
    name: options?.namePattern ?? "*",
    description: options?.description ?? defaultDescription,
    render: ({ name, args, status, result }) => {
      console.log("[useRenderToolCall] Render called:", { name, status, args, result });

      if (status === "executing") {
        if (options?.renderPendingBubble) {
          return (
            <div className={`${assistantMessageClass} tool-bubble-pending`}>
              {options.renderPendingBubble(name)}
            </div>
          );
        }

        return (
          <div className={`${assistantMessageClass} tool-bubble-pending`}>
            <div className="flex items-center gap-2">
              <Wrench className="h-4 w-4 text-white shrink-0" />
              <span className="text-sm font-medium text-white truncate">{name}</span>
            </div>
          </div>
        );
      }

      if (status === "complete") {
        return (
          <div className={assistantMessageClass}>
            <CopilotToolCallCard name={name} args={args} result={result} />
          </div>
        );
      }

      return null;
    },
  });
}
