"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import React, { useState, useEffect } from "react";
import { useAuthStore } from "@/store/authStore";
import { apiRequest } from "@/lib/api";

export default function Providers({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(() => new QueryClient());
  const setAuth = useAuthStore((state) => state.setAuth);
  const clearAuth = useAuthStore((state) => state.clearAuth);
  
  // Render loading state while validating potential active session cookies
  const [checkingSession, setCheckingSession] = useState(true);

  useEffect(() => {
    const recoverSession = async () => {
      try {
        // 1. Check for a valid HttpOnly refresh cookie on the backend
        const tokenData = await apiRequest("/auth/refresh", { method: "POST" });
        
        // 2. Fetch the user profile using the newly issued access token
        const meData = await apiRequest("/users/me", {
          headers: { Authorization: `Bearer ${tokenData.access_token}` }
        });
        
        // 3. Restore the Zustand auth state
        setAuth(meData, tokenData.access_token);
      } catch (err) {
        // If cookie is missing or expired, cleanly wipe out state
        clearAuth();
      } finally {
        setCheckingSession(false);
      }
    };

    recoverSession();
  }, [setAuth, clearAuth]);

  if (checkingSession) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-slate-50">
        <span className="text-sm font-semibold text-slate-500 animate-pulse">
          Restoring Secure Session...
        </span>
      </div>
    );
  }

  return (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );
}