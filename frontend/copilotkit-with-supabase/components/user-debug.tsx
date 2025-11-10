"use client";

import { createClient } from "@/lib/supabase/client";
import { useEffect, useState } from "react";

/**
 * Debug component to display current user information
 * Useful for verifying that user ID is correctly injected into CopilotKit
 *
 * Usage:
 * ```tsx
 * import { UserDebug } from "@/components/user-debug";
 *
 * <UserDebug />
 * ```
 */
export function UserDebug() {
  const [userId, setUserId] = useState<string | null>(null);
  const [userEmail, setUserEmail] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const supabase = createClient();

    const fetchUser = async () => {
      try {
        const { data: { user } } = await supabase.auth.getUser();
        setUserId(user?.id || null);
        setUserEmail(user?.email || null);
      } catch (error) {
        console.error("Failed to fetch user:", error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchUser();

    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      (_event, session) => {
        setUserId(session?.user?.id || null);
        setUserEmail(session?.user?.email || null);
      }
    );

    return () => {
      subscription.unsubscribe();
    };
  }, []);

  if (isLoading) {
    return (
      <div className="fixed bottom-4 right-4 bg-gray-800 text-white p-4 rounded-lg shadow-lg text-xs">
        <p>Loading user...</p>
      </div>
    );
  }

  return (
    <div className="fixed bottom-4 right-4 bg-gray-800 text-white p-4 rounded-lg shadow-lg text-xs max-w-sm">
      <h3 className="font-bold mb-2">🔍 User Debug Info</h3>
      <div className="space-y-1">
        <p>
          <span className="text-gray-400">User ID:</span>{" "}
          <span className="font-mono text-green-400">
            {userId || "anonymous"}
          </span>
        </p>
        {userEmail && (
          <p>
            <span className="text-gray-400">Email:</span>{" "}
            <span className="font-mono text-blue-400">{userEmail}</span>
          </p>
        )}
        <p>
          <span className="text-gray-400">Status:</span>{" "}
          <span className={userId ? "text-green-400" : "text-yellow-400"}>
            {userId ? "Authenticated" : "Not logged in"}
          </span>
        </p>
      </div>
      <p className="mt-2 text-gray-500 text-[10px]">
        This user ID is automatically injected into CopilotKit properties
      </p>
    </div>
  );
}
