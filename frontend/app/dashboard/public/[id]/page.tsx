"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { apiRequest } from "@/lib/api";
import WidgetCard from "@/components/WidgetCard";

interface Dashboard {
  id: string;
  name: string;
  description: string;
  widgets: any[];
}

export default function PublicDashboardPage() {
  const params = useParams();
  const dashboardId = params.id as string;
  
  const [dashboard, setDashboard] = useState<Dashboard | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const fetchPublicDashboard = async () => {
      try {
        const data = await apiRequest(`/dashboards/public/${dashboardId}`);
        setDashboard(data);
      } catch (err: any) {
        setError(err.message || "Failed to load public dashboard.");
      } finally {
        setLoading(false);
      }
    };

    if (dashboardId) {
      fetchPublicDashboard();
    }
  }, [dashboardId]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-slate-50">
        <span className="text-sm font-semibold text-slate-500 animate-pulse">
          Loading Public Workspace...
        </span>
      </div>
    );
  }

  if (error || !dashboard) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen bg-slate-50 p-6 text-center">
        <div className="max-w-md bg-white p-8 rounded-xl shadow-md border border-slate-100">
          <h1 className="text-xl font-bold text-red-600 mb-2">Access Denied</h1>
          <p className="text-sm text-slate-500">{error || "This dashboard is private or does not exist."}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col">
      {/* Read-Only Header */}
      <header className="bg-white border-b border-slate-200 px-6 py-4 flex items-center justify-between">
        <div>
          <h1 className="text-lg font-black text-indigo-600">{dashboard.name}</h1>
          <p className="text-xs text-slate-500 mt-0.5">{dashboard.description}</p>
        </div>
        <span className="text-[10px] font-bold bg-indigo-50 text-indigo-700 px-2.5 py-1 rounded-full uppercase">
          Public Share Link
        </span>
      </header>

      {/* Widgets Area */}
      <main className="flex-1 p-6">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {dashboard.widgets.length === 0 ? (
            <div className="col-span-full py-12 text-center bg-white rounded-xl border border-dashed border-slate-200">
              <p className="text-sm text-slate-500">This dashboard has no widgets configured.</p>
            </div>
          ) : (
            dashboard.widgets.map((widget) => (
              <WidgetCard 
                key={widget.id} 
                dashboardId={dashboard.id} 
                widgetId={widget.id} 
                isPublic={true}  // Explicitly set public flag to bypass private auth hooks
              />
            ))
          )}
        </div>
      </main>
    </div>
  );
}