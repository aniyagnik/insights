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
  
  const [isSignUp, setIsSignUp] = useState(false); 
  const [orgName, setOrgName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (isAuthenticated) {
      router.push("/dashboard");
    }
  }, [isAuthenticated, router]);

  const handleAuth = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setSuccess("");
    setLoading(true);

    try {
      if (isSignUp) {
        await apiRequest("/auth/signup", {
          method: "POST",
          body: JSON.stringify({ org_name: orgName, email, password }),
        });
        setSuccess("Organization registered successfully!");
      }
      
      const loginData = await apiRequest("/auth/login", {
        method: "POST",
        body: JSON.stringify({ email, password }),
      });
      
      setAuth(loginData.user, loginData.access_token);
      router.push("/dashboard");
    } catch (err: any) {
      setError(err.message || "An authentication error occurred.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="flex items-center justify-center min-h-screen p-4 bg-slate-50">
      <div className="w-full max-w-md p-8 bg-white rounded-xl shadow-md border border-slate-100">
        <div className="text-center mb-6">
          <h1 className="text-2xl font-black text-indigo-600">Analytics Platform</h1>
          <p className="text-sm text-slate-500 mt-1">
            {isSignUp ? "Register your organization & owner account" : "Multi-tenant metric telemetry panel"}
          </p>
        </div>
        
        {error && (
          <div className="p-3 mb-4 text-xs text-red-600 bg-red-50 rounded-lg border border-red-100">
            {error}
          </div>
        )}

        {success && (
          <div className="p-3 mb-4 text-xs text-emerald-600 bg-emerald-50 rounded-lg border border-emerald-100">
            {success}
          </div>
        )}

        <form onSubmit={handleAuth} className="space-y-4">
          {isSignUp && (
            <Input
              label="Organization Name"
              type="text"
              required
              value={orgName}
              onChange={(e) => setOrgName(e.target.value)}
            />
          )}
          
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
            {isSignUp ? "Register & Sign In" : "Sign In"}
          </Button>
        </form>

        <div className="text-center mt-6 pt-4 border-t border-slate-100">
          <button
            onClick={() => {
              setIsSignUp(!isSignUp);
              setError("");
              setSuccess("");
            }}
            className="text-xs text-indigo-600 hover:text-indigo-700 font-bold transition"
          >
            {isSignUp ? "Already have an organization? Sign In" : "New organization? Create Account"}
          </button>
        </div>
      </div>
    </main>
  );
}