# 前端集成文档

本目录包含 Smartrade 前端集成 CopilotKit 的完整文档。

## 📚 文档目录

### 0. [架构说明](./ARCHITECTURE.md) ⭐

**内容**：
- React Server Components (RSC) 架构
- Server/Client Components 分离原则
- 组件层次结构
- 常见错误和解决方案
- 性能优化建议

**适用场景**：
- 理解项目整体架构
- 排查 Server/Client Components 相关错误
- 学习 Next.js App Router 最佳实践

### 1. [CopilotProvider 使用指南](./README_COPILOT.md)

**内容**：
- CopilotProvider 组件使用方法
- 动态用户身份注入
- Supabase Auth 集成
- 后端数据接收方式
- 扩展用法和最佳实践

**适用场景**：
- 需要将用户身份信息传递给后端 Agent
- 监听用户登录/登出状态变化
- 自定义 CopilotKit 配置

### 2. [useRenderToolCall 使用说明](./README_TOOL_RENDERING.md)

**内容**：
- useRenderToolCall Hook 完整 API 参考
- 渲染 ADK 工具调用的方法
- 工作流程和集成示例
- 常见问题和调试技巧
- 最佳实践

**适用场景**：
- 在 CopilotSidebar 中显示工具调用过程
- 自定义工具调用的 UI 渲染
- 实时显示 Agent 执行状态

## 🚀 快速开始

### 基础设置

1. **安装依赖**：
   ```bash
   npm install @copilotkit/react-core @copilotkit/react-ui
   ```

2. **配置 CopilotProvider**（在 `app/layout.tsx`）：
   ```tsx
   import { CopilotProvider } from "@/components/copilot-provider";

   export default function RootLayout({ children }) {
     return (
       <CopilotProvider runtimeUrl="/api/copilotkit" agent="adk_demo">
         {children}
       </CopilotProvider>
     );
   }
   ```

3. **添加 CopilotSidebar**（在页面组件中）：
   ```tsx
   "use client";

   import { CopilotSidebar } from "@copilotkit/react-ui";
   import { useRenderToolCall } from "@copilotkit/react-core";

   export default function Home() {
     // 渲染工具调用
     useRenderToolCall({
       name: "",
       render: ({ args, status, result }) => {
         // 自定义渲染逻辑
       }
     });

     return (
       <CopilotSidebar>
         {/* 你的应用内容 */}
       </CopilotSidebar>
     );
   }
   ```

## 🔧 配置参考

### 环境变量

```bash
# .env.local

# Supabase 配置（用于用户身份）
NEXT_PUBLIC_SUPABASE_URL=your-supabase-url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key

# CopilotKit 运行时 URL（可选）
NEXT_PUBLIC_COPILOT_RUNTIME_URL=/api/copilotkit
```

### BFF 配置

BFF 层配置文件：`app/api/copilotkit/route.ts`

```typescript
import { CopilotRuntime } from "@copilotkit/runtime";
import { HttpAgent } from "@ag-ui/client";

const runtime = new CopilotRuntime({
  agents: {
    "adk_demo": new HttpAgent({
      url: "http://localhost:8000/api/adk/copilotkit/adk_demo"
    }),
    "smart_trader": new HttpAgent({
      url: "http://localhost:8000/api/adk/copilotkit/smart_trader"
    }),
  }
});
```

## 📖 核心概念

### 架构图

```
┌──────────────────────────────────────────────────────────┐
│ 前端 (Next.js)                                            │
│                                                           │
│  ┌─────────────────────────────────────────────────┐    │
│  │ CopilotProvider (layout.tsx)                     │    │
│  │  - 注入用户身份 (Supabase Auth)                  │    │
│  │  - 配置 runtimeUrl 和 agent                      │    │
│  └─────────────────┬───────────────────────────────┘    │
│                    │                                      │
│  ┌─────────────────▼───────────────────────────────┐    │
│  │ CopilotSidebar (page.tsx)                        │    │
│  │  - 聊天界面                                       │    │
│  │  - useRenderToolCall: 渲染工具调用              │    │
│  └─────────────────┬───────────────────────────────┘    │
└────────────────────┼──────────────────────────────────┘
                     │
                     │ POST /api/copilotkit
                     ▼
┌──────────────────────────────────────────────────────────┐
│ BFF 层 (Next.js API Route)                               │
│                                                           │
│  CopilotRuntime                                           │
│   - 接收前端请求                                          │
│   - 转发到后端 Agent                                      │
│                                                           │
└────────────────────┬──────────────────────────────────┘
                     │
                     │ HTTP POST
                     ▼
┌──────────────────────────────────────────────────────────┐
│ 后端 (FastAPI + Google ADK)                               │
│                                                           │
│  /api/adk/copilotkit/{agent_name}                        │
│   - 接收请求和 properties                                 │
│   - 提取 user_id                                         │
│   - 调用 ADK Agent                                        │
│   - 返回工具调用结果                                      │
│                                                           │
└──────────────────────────────────────────────────────────┘
```

### 数据流

1. **用户发送消息** → CopilotSidebar
2. **前端 → BFF** → `/api/copilotkit` (携带 properties: { user_id })
3. **BFF → 后端** → `http://localhost:8000/api/adk/copilotkit/adk_demo`
4. **后端处理**：
   - 提取 `user_id` 从 `forwarded_props`
   - 执行 Agent 逻辑
   - 调用工具（如果需要）
5. **后端 → 前端**：
   - 流式返回 Agent 响应
   - 工具调用事件（args, status, result）
6. **前端渲染**：
   - `useRenderToolCall` 捕获工具调用
   - 在 CopilotSidebar 中显示自定义 UI

## 🎯 常见使用场景

### 场景 1：显示股票查询结果

```tsx
useRenderToolCall({
  name: "searchStock",
  render: ({ args, status, result }) => {
    if (status === "complete" && result) {
      return (
        <div className="p-4 bg-blue-50 rounded">
          <h3>{result.name}</h3>
          <p>价格: ¥{result.price}</p>
          <p>涨跌: {result.change}%</p>
        </div>
      );
    }
    return <div>搜索中...</div>;
  }
});
```

### 场景 2：显示多个工具调用

```tsx
// 捕获所有工具
useRenderToolCall({
  name: "",
  render: ({ name, args, status, result }) => {
    if (name === "searchStock") {
      return <StockCard {...result} />;
    }
    if (name === "getNews") {
      return <NewsCard {...result} />;
    }
    return <GenericCard args={args} result={result} />;
  }
});
```

### 场景 3：添加用户权限验证

```tsx
// components/copilot-provider.tsx
const properties = {
  user_id: userId || 'anonymous',
  user_role: user?.role || 'guest',
  user_permissions: user?.permissions || [],
};
```

## 🐛 调试技巧

### 1. 查看前端发送的数据

```tsx
// 在 CopilotProvider 中添加日志
const properties = {
  user_id: userId || 'anonymous',
};
console.log("📤 Sending properties:", properties);
```

### 2. 查看工具调用事件

```tsx
useRenderToolCall({
  name: "",
  render: ({ name, args, status, result }) => {
    console.log("🔧 Tool Call:", { name, status, args, result });
    return <div>...</div>;
  }
});
```

### 3. 使用 UserDebug 组件

```tsx
import { UserDebug } from "@/components/user-debug";

// 开发环境显示
{process.env.NODE_ENV === 'development' && <UserDebug />}
```

### 4. 查看后端日志

```bash
# 后端日志会显示
INFO - backend.api.endpoint - 🔍 ADK Agent: forwarded_props: {'user_id': '...'}
INFO - backend.api.endpoint - ✅ Successfully extracted user_id: ...
```

## 📦 相关组件

- **CopilotProvider**: `components/copilot-provider.tsx`
- **UserDebug**: `components/user-debug.tsx`
- **BFF 配置**: `app/api/copilotkit/route.ts`

## 🔗 相关链接

- [CopilotKit 官方文档](https://docs.copilotkit.ai)
- [Google ADK 文档](https://github.com/google/genai-agent-builder)
- [Supabase Auth 文档](https://supabase.com/docs/guides/auth)
- [后端集成文档](../../../backend/config/README_LOGGING.md)

## 💡 提示

- 开发时启用 `showDevConsole: true` 查看详细错误
- 使用 Chrome DevTools 的 Network 标签查看请求/响应
- 后端日志级别设置为 `INFO` 以查看详细日志
- 使用 TypeScript 获得完整的类型提示

---

**最后更新**：2025-01-09
**维护者**：Smartrade Team
