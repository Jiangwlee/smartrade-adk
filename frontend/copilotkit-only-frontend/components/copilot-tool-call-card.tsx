"use client";

import { Copy, Check, ChevronDown, ChevronUp, Wrench, X } from "lucide-react";
import { useState } from "react";

type ToolCallCardProps = {
  name: string;
  args: any;
  result: any;
};

export function CopilotToolCallCard({ name, args, result }: ToolCallCardProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [activeTab, setActiveTab] = useState<"params" | "result">("params");

  const isSuccess = result && !result.error;

  const copyToClipboard = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text);
    } catch (err) {
      console.error("复制失败:", err);
    }
  };

  const handleCopy = (data: any) => {
    const text = typeof data === "string" ? data : JSON.stringify(data, null, 2);
    copyToClipboard(text);
  };

  return (
    <div
      className={`tool-call-card rounded-lg border bg-white shadow-sm transition-all duration-300 ${
        isSuccess ? "border-[#2AAA8A]/30" : "border-gray-300"
      }`}
    >
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full p-3 flex items-center justify-between gap-3 hover:bg-gray-50 transition-colors rounded-lg"
      >
        <div className="flex items-center gap-2 flex-1 min-w-0">
          <Wrench className="h-5 w-5 text-gray-600 shrink-0" />
          <span className="font-medium text-gray-900 truncate">{name}</span>
        </div>

        <div className="flex items-center gap-2 shrink-0">
          {isSuccess ? (
            <Check className="h-4 w-4" style={{ color: "#2AAA8A" }} />
          ) : (
            <X className="h-4 w-4 text-gray-500" />
          )}
          {isExpanded ? (
            <ChevronUp className="h-4 w-4 text-gray-500" />
          ) : (
            <ChevronDown className="h-4 w-4 text-gray-500" />
          )}
        </div>
      </button>

      {isExpanded && (
        <div className="border-t border-gray-200">
          <div className="flex items-center justify-between px-3 pt-3">
            <div className="flex gap-2">
              <button
                onClick={() => setActiveTab("params")}
                className={`px-3 py-1.5 text-sm font-medium rounded-md transition-colors ${
                  activeTab === "params"
                    ? "bg-gray-100 text-gray-900"
                    : "text-gray-600 hover:text-gray-900"
                }`}
              >
                参数
              </button>
              <button
                onClick={() => setActiveTab("result")}
                className={`px-3 py-1.5 text-sm font-medium rounded-md transition-colors ${
                  activeTab === "result"
                    ? "bg-gray-100 text-gray-900"
                    : "text-gray-600 hover:text-gray-900"
                }`}
              >
                结果
              </button>
            </div>
          </div>

          <div className="px-3 pb-3 mt-3">
            {activeTab === "params" ? (
              <div className="relative">
                <button
                  onClick={() => handleCopy(args)}
                  className="absolute top-2 right-2 p-1.5 rounded hover:bg-gray-200 transition-colors"
                  aria-label="复制参数"
                >
                  <Copy className="h-3.5 w-3.5 text-gray-500" />
                </button>
                <pre className="text-xs bg-gray-50 rounded p-3 pr-10 overflow-auto max-h-80 text-gray-900">
                  {typeof args === "string" ? args : JSON.stringify(args, null, 2)}
                </pre>
              </div>
            ) : (
              <div className="relative">
                {result ? (
                  <>
                    <button
                      onClick={() => handleCopy(result)}
                      className="absolute top-2 right-2 p-1.5 rounded hover:bg-gray-200 transition-colors"
                      aria-label="复制结果"
                    >
                      <Copy className="h-3.5 w-3.5 text-gray-500" />
                    </button>
                    <pre className="text-xs bg-gray-50 rounded p-3 pr-10 overflow-auto max-h-80 text-gray-900">
                      {typeof result === "string" ? result : JSON.stringify(result, null, 2)}
                    </pre>
                  </>
                ) : (
                  <div className="text-sm text-gray-500 text-center py-4">暂无结果</div>
                )}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
