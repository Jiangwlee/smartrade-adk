"use client";

import { CopilotSidebar } from "@copilotkit/react-ui";
import { useRenderToolCall } from "@copilotkit/react-core";
import { ReactNode } from "react";

/**
 * CopilotSidebarWrapper - Client Component wrapper for CopilotSidebar
 *
 * This component handles:
 * - CopilotSidebar rendering (Client Component)
 * - useRenderToolCall hook registration (Client-side)
 */
export function CopilotSidebarWrapper({ children }: { children: ReactNode }) {
  // 渲染所有后端 ADK 工具调用
  useRenderToolCall({
    name: "*",  // 使用通配符捕获所有工具调用
    description: "Render all ADK tool calls in the chat",
    render: ({ name, args, status, result }) => {
      console.log("[useRenderToolCall] Render called:", { name, status, args, result });

      // 首次调用工具时：显示工具名称和参数
      if (status === "executing") {
        return (
          <div className="p-4 border border-blue-300 rounded-lg bg-blue-50 animate-pulse">
            <div className="flex items-center gap-2 mb-2">
              <div className="w-2 h-2 bg-blue-500 rounded-full animate-ping"></div>
              <h3 className="font-semibold text-blue-800">正在调用工具</h3>
            </div>

            <div className="mb-2">
              <span className="text-sm font-medium text-blue-700">工具名称：</span>
              <code className="text-sm bg-blue-100 px-2 py-0.5 rounded">{name}</code>
            </div>

            <div>
              <span className="text-sm font-medium text-blue-700">参数：</span>
              <pre className="mt-1 p-2 bg-white rounded text-xs overflow-auto border border-blue-200">
                {JSON.stringify(args, null, 2)}
              </pre>
            </div>
          </div>
        );
      }

      // 工具调用完成时：显示结果
      if (status === "complete" && result) {
        return (
          <div className="p-4 border border-green-300 rounded-lg bg-green-50">
            <div className="flex items-center gap-2 mb-2">
              <div className="w-2 h-2 bg-green-500 rounded-full"></div>
              <h3 className="font-semibold text-green-800">工具调用完成</h3>
            </div>

            <div className="mb-2">
              <span className="text-sm font-medium text-green-700">工具名称：</span>
              <code className="text-sm bg-green-100 px-2 py-0.5 rounded">{name}</code>
            </div>

            <div>
              <span className="text-sm font-medium text-green-700">返回结果：</span>
              <pre className="mt-1 p-2 bg-white rounded text-xs overflow-auto border border-green-200">
                {JSON.stringify(result, null, 2)}
              </pre>
            </div>
          </div>
        );
      }

      return null;
    },
  });

  return (
    <CopilotSidebar
      defaultOpen={true}
      clickOutsideToClose={false}
      labels={{
        title: "Smartrade Assistant",
        initial: "👋 你好！我是 Smartrade 智能助手。\n\n我可以帮助你：\n- 了解应用功能\n- 回答使用问题\n- 提供操作指导"
      }}
    >
      {children}
    </CopilotSidebar>
  );
}
