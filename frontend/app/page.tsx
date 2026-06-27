"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/store/authStore";
import { apiRequest } from "@/lib/api";
import Input from "@/components/Input";
import Button from "@/components/Button";

export default function Home() {
  const { isAuthenticated, setAuth } = useAuthStore();
  const router = useRouter();
  
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  // Watch session, automatically routing logged-in users straight to workspace
  useEffect(() => {
    if (isAuthenticated) {
      router.push("/dashboard");
    }
  }, [isAuthenticated, router]);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const data = await apiRequest("/auth/login", {
        method: "POST",
        body: JSON.stringify({ email, password }),
      });
      
      setAuth(data.user, data.access_token);
      router.push("/dashboard");
    } catch (err: any) {
      setError(err.message || "Failed to log in.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="flex items-center justify-center min-h-screen p-4 bg-slate-50">
      <div className="w-full max-w-md p-8 bg-white rounded-xl shadow-md border border-slate-100">
        <div className="text-center mb-6">
          <h1 className="text-2xl font-black text-indigo-600">Analytics Platform</h1>
          <p className="text-sm text-slate-500 mt-1">Multi-tenant metric telemetry panel</p>
        </div>
        
        {error && (
          <div className="p-3 mb-4 text-xs text-red-600 bg-red-50 rounded-lg border border-red-100">
            {error}
          </div>
        )}

        <form onSubmit={handleLogin} className="space-y-4">
          <Input
            label="Email Address"
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
          <Input
            label="Password"
            type="password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
          <Button type="submit" loading={loading} className="w-full py-2.5">
            Sign In
          </Button>
        </form>
      </div>
    </main>
  );
}