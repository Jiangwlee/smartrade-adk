"use client";

import { CopilotKit } from "@copilotkit/react-core";
import { createClient } from "@/lib/supabase/client";
import { useEffect, useState } from "react";

interface CopilotProviderProps {
  children: React.ReactNode;
  runtimeUrl: string;
  agent: string;
}

/**
 * CopilotKit Provider with dynamic user injection
 *
 * This component wraps CopilotKit and automatically injects the current user's ID
 * from Supabase auth into the properties sent to the backend.
 *
 * @example
 * ```tsx
 * <CopilotProvider runtimeUrl="/api/copilotkit" agent="adk_demo">
 *   <YourApp />
 * </CopilotProvider>
 * ```
 */
export function CopilotProvider({
  children,
  runtimeUrl,
  agent,
}: CopilotProviderProps) {
  const [userId, setUserId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const supabase = createClient();

    // 获取当前用户
    const fetchUser = async () => {
      try {
        const { data: { user } } = await supabase.auth.getUser();
        setUserId(user?.id || null);
      } catch (error) {
        console.error("Failed to fetch user:", error);
        setUserId(null);
      } finally {
        setIsLoading(false);
      }
    };

    fetchUser();

    // 监听认证状态变化
    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      (_event, session) => {
        setUserId(session?.user?.id || null);
      }
    );

    return () => {
      subscription.unsubscribe();
    };
  }, []);

  // 构建动态 properties
  const properties = {
    user_id: userId || 'anonymous',
    // 可以添加更多属性
    // user_email: user?.email,
    // user_role: user?.role,
  };

  // 如果需要，可以在加载时显示 loading 状态
  // if (isLoading) {
  //   return <div>Loading...</div>;
  // }

  return (
    <CopilotKit
      runtimeUrl={runtimeUrl}
      agent={agent}
      properties={properties}
      showDevConsole={true}
    >
      {children}
    </CopilotKit>
  );
}
