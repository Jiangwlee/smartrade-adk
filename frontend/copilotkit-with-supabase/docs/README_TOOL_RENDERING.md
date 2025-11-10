# useRenderToolCall 使用说明

## 概述

`useRenderToolCall` 是 CopilotKit 提供的纯渲染 hook，用于在前端可视化后端工具调用的执行过程和结果。

## 核心特性

- ✅ **纯渲染**：只负责显示，不执行任何逻辑
- ✅ **实时状态**：显示工具调用的 `inProgress` 和 `complete` 状态
- ✅ **通配符支持**：使用 `name: ""` 捕获所有工具调用
- ✅ **自定义 UI**：完全控制渲染样式

## API 参考

### 参数

```typescript
useRenderToolCall({
  name: string;           // 工具名称，"" 表示所有工具
  description?: string;   // 描述（可选）
  parameters?: Parameter[]; // 参数定义（可选，用于类型提示）
  render: (props) => ReactElement | null;  // 渲染函数
  available?: "enabled" | "disabled";  // 是否启用（可选）
});
```

### Render 函数参数

```typescript
render: ({ args, status, result, name, description }) => {
  // args: 工具调用的参数（实时更新）
  // status: "inProgress" | "executing" | "complete"
  // result: 工具返回的结果（status 为 "complete" 时可用）
  // name: 工具名称
  // description: 工具描述
}
```

## 使用示例

### 1. 渲染所有工具调用（当前实现）

```tsx
useRenderToolCall({
  name: "",  // 空字符串 = 捕获所有工具
  description: "Render all ADK tool calls",
  render: ({ args, status, result }) => {
    if (status === "inProgress") {
      return (
        <div className="p-4 border rounded animate-pulse">
          <h3>调用工具中...</h3>
          <p>{JSON.stringify(args, null, 2)}</p>
        </div>
      );
    }

    if (status === "complete" && result) {
      return (
        <div className="p-4 border rounded bg-green-50">
          <h3>工具调用完成</h3>
          <pre>{JSON.stringify(result, null, 2)}</pre>
        </div>
      );
    }

    return null;
  },
});
```

### 2. 渲染特定工具

```tsx
// 只渲染名为 "searchStock" 的工具
useRenderToolCall({
  name: "searchStock",
  description: "Display stock search results",
  render: ({ args, status, result }) => {
    if (status === "inProgress") {
      return <div>搜索股票: {args.symbol}...</div>;
    }

    if (status === "complete" && result) {
      return (
        <div>
          <h3>{result.name}</h3>
          <p>价格: ¥{result.price}</p>
        </div>
      );
    }

    return null;
  },
});
```

### 3. 多个渲染器

```tsx
// 可以为不同的工具定义不同的渲染器
useRenderToolCall({
  name: "getWeather",
  render: ({ result }) => <WeatherCard data={result} />
});

useRenderToolCall({
  name: "getStock",
  render: ({ result }) => <StockCard data={result} />
});

// 捕获其他所有工具
useRenderToolCall({
  name: "",
  render: ({ args, result }) => <GenericToolCard args={args} result={result} />
});
```

## 工作流程

```
┌─────────────────────────────────────────────────────────────┐
│ 1. 用户在 CopilotSidebar 中发送消息                         │
│    "帮我查一下比亚迪的股票信息"                              │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. 前端 BFF (/api/copilotkit) 转发到后端                    │
│    → http://localhost:8000/api/adk/copilotkit/adk_demo      │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. ADK Agent 决定调用工具                                    │
│    tool: "searchStock"                                       │
│    args: { symbol: "002594" }                                │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. 前端接收到工具调用事件                                    │
│    status: "inProgress"                                      │
│    ↓                                                         │
│    useRenderToolCall 渲染 inProgress 状态                    │
│    显示: "调用工具中..."                                      │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│ 5. 后端执行完成，返回结果                                    │
│    status: "complete"                                        │
│    result: { name: "比亚迪", price: 256.8, ... }             │
│    ↓                                                         │
│    useRenderToolCall 渲染 complete 状态                      │
│    显示: 股票卡片                                            │
└─────────────────────────────────────────────────────────────┘
```

## 与 ADK 集成

### ADK Agent 端（Python）

```python
# backend/agents/adk_demo/agent.py

from google.genai.types import Tool, FunctionDeclaration

# 定义工具
search_stock_tool = Tool(
    function_declarations=[
        FunctionDeclaration(
            name="searchStock",
            description="搜索股票信息",
            parameters={
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "股票代码"
                    }
                },
                "required": ["symbol"]
            }
        )
    ]
)

# Agent 使用工具
agent = Agent(
    model="gemini-2.0-flash-exp",
    tools=[search_stock_tool],
    # ...
)
```

### 前端渲染（TypeScript）

```tsx
// frontend/app/page.tsx

useRenderToolCall({
  name: "searchStock",  // 与 ADK 工具名称匹配
  render: ({ args, status, result }) => {
    // 自定义渲染逻辑
  }
});
```

## 常见问题

### Q1: 为什么我的工具调用没有被渲染？

**可能原因**：
1. `name` 参数不匹配
   ```tsx
   // ❌ 错误：使用 "*"
   name: "*"

   // ✅ 正确：使用空字符串
   name: ""
   ```

2. Hook 注册太晚（在工具调用之后）
   ```tsx
   // ✅ 确保在组件顶层调用
   export default function Home() {
     useRenderToolCall({ ... });  // 在这里

     return <CopilotSidebar>...</CopilotSidebar>;
   }
   ```

### Q2: 如何同时渲染多个工具？

可以多次调用 `useRenderToolCall`：

```tsx
export default function Home() {
  useRenderToolCall({ name: "searchStock", ... });
  useRenderToolCall({ name: "getNews", ... });
  useRenderToolCall({ name: "", ... });  // 捕获其他所有工具

  return <CopilotSidebar>...</CopilotSidebar>;
}
```

### Q3: `parameters` 参数是必需的吗？

**不是必需的**。`parameters` 主要用于：
- 提供类型提示（TypeScript）
- 文档目的

对于纯渲染，后端 ADK 工具已经定义了参数，前端参数定义是冗余的。

```tsx
// ✅ 简化版（推荐）
useRenderToolCall({
  name: "",
  render: ({ args, status, result }) => { ... }
});

// ✅ 完整版（带类型提示）
useRenderToolCall({
  name: "searchStock",
  parameters: [
    { name: "symbol", type: "string", required: true }
  ],
  render: ({ args, status, result }) => { ... }
});
```

### Q4: Status 有哪些可能的值？

根据文档和源码：
- `"inProgress"` - 参数正在流式传输
- `"executing"` - 正在执行（可能不会触发渲染）
- `"complete"` - 执行完成

实际使用中，主要关注：
- `"inProgress"` - 显示加载状态
- `"complete"` - 显示结果

### Q5: 如何调试工具调用？

```tsx
useRenderToolCall({
  name: "",
  render: ({ args, status, result, name }) => {
    // 在控制台打印调试信息
    console.log("Tool Call:", { name, status, args, result });

    return (
      <div className="p-4 border">
        <pre>{JSON.stringify({ name, status, args, result }, null, 2)}</pre>
      </div>
    );
  }
});
```

## 最佳实践

### ✅ 推荐

```tsx
// 1. 使用 "" 捕获所有工具
useRenderToolCall({ name: "", ... });

// 2. 提供友好的加载状态
if (status === "inProgress") {
  return <LoadingSpinner />;
}

// 3. 验证结果存在后再渲染
if (status === "complete" && result) {
  return <ResultCard data={result} />;
}

// 4. 返回 null 表示不渲染
return null;
```

### ❌ 避免

```tsx
// 1. 不要使用 "*"
name: "*"  // ❌

// 2. 不要忘记检查 result
if (status === "complete") {
  return <div>{result.data}</div>;  // ❌ result 可能是 undefined
}

// 3. 不要在渲染函数中执行副作用
render: ({ args }) => {
  makeAPICall(args);  // ❌ 这是渲染 hook，不应执行逻辑
  return <div>...</div>;
}
```

## 进阶用法

### 根据工具名称定制渲染

```tsx
useRenderToolCall({
  name: "",
  render: ({ name, args, status, result }) => {
    // 根据不同的工具名称返回不同的 UI
    if (name === "searchStock") {
      return <StockCard {...result} />;
    }

    if (name === "getNews") {
      return <NewsCard {...result} />;
    }

    // 默认渲染
    return <GenericCard args={args} result={result} />;
  }
});
```

### 添加错误处理

```tsx
useRenderToolCall({
  name: "",
  render: ({ status, result }) => {
    if (status === "complete") {
      if (result?.error) {
        return (
          <div className="p-4 bg-red-50 text-red-800">
            <h3>执行失败</h3>
            <p>{result.error}</p>
          </div>
        );
      }

      return <SuccessCard data={result} />;
    }

    return null;
  }
});
```

## 参考资料

- [CopilotKit 官方文档](https://docs.copilotkit.ai/reference/hooks/useRenderToolCall)
- [ADK Agent 文档](../../../backend/agents/README.md)
- [前端集成指南](../components/README_COPILOT.md)
