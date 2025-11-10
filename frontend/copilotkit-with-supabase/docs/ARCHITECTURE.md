# 前端架构说明

## React Server Components (RSC) 架构

本项目使用 Next.js App Router 的 React Server Components 架构，正确分离了 Server Components 和 Client Components。

## 组件层次结构

```
app/layout.tsx (Server Component)
  └─ CopilotProvider (Client Component)
      └─ app/page.tsx (Server Component)
          ├─ AuthButton (Server Component) ✅
          ├─ Hero (Server Component)
          └─ CopilotSidebarWrapper (Client Component)
              ├─ CopilotSidebar (Client Component)
              │   └─ useRenderToolCall (Hook)
              └─ children (Server Components passed as props) ✅
```

## 核心原则

### ✅ 允许的操作

1. **Server Component 渲染 Client Component**
   ```tsx
   // page.tsx (Server Component)
   export default function Page() {
     return <CopilotSidebarWrapper>...</CopilotSidebarWrapper>;
   }
   ```

2. **Server Component 作为 Children 传递给 Client Component**
   ```tsx
   // page.tsx (Server Component)
   export default function Page() {
     return (
       <CopilotSidebarWrapper>
         <AuthButton /> {/* Server Component 作为 children */}
       </CopilotSidebarWrapper>
     );
   }
   ```

### ❌ 禁止的操作

1. **Client Component 直接导入 Server Component**
   ```tsx
   // ❌ 错误
   "use client";
   import { AuthButton } from "./auth-button"; // Server Component

   export function ClientComp() {
     return <AuthButton />; // 会报错！
   }
   ```

2. **Client Component 内使用 Server-only API**
   ```tsx
   // ❌ 错误
   "use client";
   import { cookies } from "next/headers"; // Server-only

   export function ClientComp() {
     const c = cookies(); // 会报错！
   }
   ```

## 文件说明

### 1. `app/layout.tsx` (Server Component)

**职责**：
- 应用根布局
- 配置 metadata
- 集成全局 Provider

**关键代码**：
```tsx
export default function RootLayout({ children }) {
  return (
    <html>
      <body>
        <ThemeProvider>
          <CopilotProvider runtimeUrl="/api/copilotkit" agent="adk_demo">
            {children}
          </CopilotProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
```

### 2. `app/page.tsx` (Server Component)

**职责**：
- 主页内容渲染
- 使用 Server Components（AuthButton, Hero 等）
- 包裹 CopilotSidebarWrapper

**关键代码**：
```tsx
export default function Home() {
  return (
    <CopilotSidebarWrapper>
      <main>
        <AuthButton /> {/* Server Component - 可以访问 cookies */}
        <Hero />
      </main>
    </CopilotSidebarWrapper>
  );
}
```

**为什么保持为 Server Component？**
- 可以使用 `AuthButton`（需要 `cookies()` API）
- 可以进行服务器端数据获取
- 更好的性能（减少客户端 JavaScript）

### 3. `components/copilot-sidebar-wrapper.tsx` (Client Component)

**职责**：
- 包裹 CopilotSidebar（Client Component）
- 注册 useRenderToolCall hook
- 接收 Server Components 作为 children

**关键代码**：
```tsx
"use client";

import { CopilotSidebar } from "@copilotkit/react-ui";
import { useRenderToolCall } from "@copilotkit/react-core";

export function CopilotSidebarWrapper({ children }) {
  useRenderToolCall({
    name: "",
    render: ({ args, status, result }) => {
      // 渲染逻辑
    }
  });

  return (
    <CopilotSidebar>
      {children} {/* Server Components 可以作为 children 传入 */}
    </CopilotSidebar>
  );
}
```

**为什么必须是 Client Component？**
- 使用 React hooks（useRenderToolCall）
- CopilotSidebar 本身是 Client Component
- 需要客户端交互逻辑

### 4. `components/copilot-provider.tsx` (Client Component)

**职责**：
- 包裹 CopilotKit Provider
- 动态注入用户身份（从 Supabase Auth）
- 配置 CopilotKit

**关键代码**：
```tsx
"use client";

export function CopilotProvider({ children, runtimeUrl, agent }) {
  const [userId, setUserId] = useState(null);

  useEffect(() => {
    const supabase = createClient(); // Client-side Supabase
    // 获取用户信息
  }, []);

  return (
    <CopilotKit
      runtimeUrl={runtimeUrl}
      agent={agent}
      properties={{ user_id: userId }}
    >
      {children}
    </CopilotKit>
  );
}
```

**为什么必须是 Client Component？**
- 使用 React hooks（useState, useEffect）
- 需要监听 Supabase auth 状态变化
- 动态更新 properties

### 5. `components/auth-button.tsx` (Server Component)

**职责**：
- 显示用户登录状态
- 服务器端验证用户身份

**关键代码**：
```tsx
export async function AuthButton() {
  const supabase = await createClient(); // Server-side Supabase
  const { data } = await supabase.auth.getClaims();

  return user ? (
    <div>Hey, {user.email}!</div>
  ) : (
    <Link href="/auth/login">Sign in</Link>
  );
}
```

**为什么必须是 Server Component？**
- 使用 `cookies()` from `next/headers`
- 服务器端数据获取
- 更安全的认证检查

## 数据流

### 1. 用户身份注入流程

```
layout.tsx (Server)
  └─ CopilotProvider (Client)
      ├─ useEffect: 获取 Supabase user
      ├─ properties: { user_id }
      └─ 发送到 /api/copilotkit
```

### 2. 工具调用渲染流程

```
page.tsx (Server)
  └─ CopilotSidebarWrapper (Client)
      ├─ useRenderToolCall: 注册渲染器
      └─ CopilotSidebar
          └─ 接收后端工具调用 → 触发渲染
```

### 3. 认证状态显示流程

```
page.tsx (Server)
  └─ AuthButton (Server)
      ├─ cookies(): 读取 session
      └─ 渲染登录状态
```

## 常见错误和解决方案

### 错误 1: "You're importing a component that needs next/headers"

**原因**：Client Component 导入了使用 Server-only API 的组件

**解决方案**：
```tsx
// ❌ 错误
"use client";
import { AuthButton } from "./auth-button";

// ✅ 正确：将 Server Component 作为 children 传入
"use client";
export function Wrapper({ children }) {
  return <div>{children}</div>;
}

// 在 Server Component 中
<Wrapper>
  <AuthButton />
</Wrapper>
```

### 错误 2: "Cannot use hooks in Server Component"

**原因**：在 Server Component 中使用了 React hooks

**解决方案**：
```tsx
// ❌ 错误
export default function Page() {
  const [state, setState] = useState(); // Server Component 不能用 hooks
}

// ✅ 正确：创建独立的 Client Component
"use client";
export function ClientPart() {
  const [state, setState] = useState();
  return <div>...</div>;
}

// 在 Server Component 中使用
export default function Page() {
  return <ClientPart />;
}
```

### 错误 3: "Cannot pass function props to Client Component"

**原因**：Server Component 向 Client Component 传递了函数

**解决方案**：
```tsx
// ❌ 错误
<ClientComp onAction={async () => { ... }} />

// ✅ 正确：使用 Server Actions
"use server";
export async function handleAction() {
  // Server-side logic
}

// 在 Client Component 中
"use client";
import { handleAction } from "./actions";

<button onClick={() => handleAction()}>Click</button>
```

## 性能优化

### 1. Server Components 优先

- 默认使用 Server Components
- 只在必要时标记 `"use client"`
- Server Components 不会增加客户端 JavaScript bundle 大小

### 2. Client Components 边界

- 尽可能将 `"use client"` 推到组件树的叶子节点
- 减少 Client Components 的数量和大小

### 3. 数据获取

- Server Components 中进行数据获取
- 避免客户端瀑布请求（waterfall requests）

## 调试技巧

### 1. 检查组件类型

```bash
# 查找所有 Client Components
grep -r "\"use client\"" app/ components/

# 查找所有 async Server Components
grep -r "export async function" app/ components/
```

### 2. 验证导入链

```bash
# 检查是否有 Client Component 导入 Server Component
# （应该通过 children/props 传递）
```

### 3. 使用 React DevTools

- 查看组件树
- 确认 Client/Server 边界
- 检查 props 传递

## 参考资料

- [Next.js App Router](https://nextjs.org/docs/app)
- [React Server Components](https://react.dev/blog/2023/03/22/react-labs-what-we-have-been-working-on-march-2023#react-server-components)
- [Server and Client Composition](https://nextjs.org/docs/app/building-your-application/rendering/composition-patterns)
- [CopilotKit 文档](https://docs.copilotkit.ai)

---

**最后更新**：2025-01-09
**维护者**：Smartrade Team
