"use client";

import React, { useState, Suspense } from "react";  // Added Suspense wrapper for Next 14 Query boundaries
import { useRouter, useSearchParams } from "next/navigation";
import { apiRequest } from "@/lib/api";
import Input from "@/components/Input";
import Button from "@/components/Button";

function AcceptInviteForm() {
  const searchParams = useSearchParams();
  const token = searchParams.get("token");
  const router = useRouter();

  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [loading, setLoading] = useState(false);

  const handleAccept = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token) return;
    setError("");
    setSuccess("");
    setLoading(true);

    try {
      // 1. Submit password and token to complete onboarding registration
      await apiRequest(`/invites/${token}/accept`, {
        method: "POST",
        body: JSON.stringify({ password })
      });
      setSuccess("Account successfully registered!");
      
      // 2. Redirect back to unified root login page after 2 seconds
      setTimeout(() => {
        router.push("/");
      }, 2000);
    } catch (err: any) {
      setError(err.message || "Failed to accept invitation.");
    } finally {
      setLoading(false);
    }
  };

  if (!token) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-slate-50 p-6 text-center">
        <div className="max-w-md bg-white p-8 rounded-xl shadow-sm border border-slate-100">
          <h1 className="text-xl font-bold text-red-600 mb-2">Invalid Access Link</h1>
          <p className="text-sm text-slate-500">The onboarding token is missing from the query string parameters.</p>
        </div>
      </div>
    );
  }

  return (
    <main className="flex items-center justify-center min-h-screen p-4 bg-slate-50">
      <div className="w-full max-w-md p-8 bg-white rounded-xl shadow-md border border-slate-100">
        <div className="text-center mb-6">
          <h1 className="text-2xl font-black text-indigo-600">Join Workspace</h1>
          <p className="text-sm text-slate-500 mt-1">Configure your password to complete registration</p>
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

        <form onSubmit={handleAccept} className="space-y-4">
          <Input
            label="Create Workspace Password"
            type="password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Choose a strong password"
          />
          <Button type="submit" loading={loading} className="w-full py-2.5">
            Complete Registration
          </Button>
        </form>
      </div>
    </main>
  );
}

// Wrap in Suspense to prevent build compilation errors in Next.js 14 App Router
export default function AcceptInvitePage() {
  return (
    <Suspense fallback={<div className="text-center py-12 text-sm text-slate-500">Loading form...</div>}>
      <AcceptInviteForm />
    </Suspense>
  );
}