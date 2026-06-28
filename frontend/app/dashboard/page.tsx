"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/store/authStore";
import { apiRequest } from "@/lib/api";
import Button from "@/components/Button";
import WidgetCard from "@/components/WidgetCard";
import LiveStreamViewer from "@/components/LiveStreamViewer";  // Imported

interface Dashboard {
  id: string;
  name: string;
  description: string;
  widgets: any[];
}

export default function DashboardPage() {
  const { user, isAuthenticated, clearAuth } = useAuthStore();
  const router = useRouter();
  
  const [dashboards, setDashboards] = useState<Dashboard[]>([]);
  const [activeDashboard, setActiveDashboard] = useState<Dashboard | null>(null);
  const [showLiveStream, setShowLiveStream] = useState(false);  // Added state
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!isAuthenticated) {
      router.push("/");
      return;
    }

    const fetchDashboards = async () => {
      try {
        const data = await apiRequest("/dashboards");
        setDashboards(data);
        if (data.length > 0) {
          setActiveDashboard(data[0]);
        }
      } catch (err) {
        console.error("Failed to load dashboards", err);
      } finally {
        setLoading(false);
      }
    };

    fetchDashboards();
  }, [isAuthenticated, router]);

  const handleLogout = async () => {
    try {
      await apiRequest("/auth/logout", { method: "POST" });
    } catch (err) {
      console.error("Logout request failed", err);
    } finally {
      clearAuth();
      router.push("/");
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-slate-50">
        <span className="text-sm font-semibold text-slate-500">Loading Workspace...</span>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col">
      {/* Header Panel */}
      <header className="bg-white border-b border-slate-200 px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <h1 className="text-lg font-extrabold text-indigo-600">Analytics Workspace</h1>
          <span className="text-xs bg-indigo-50 text-indigo-700 px-2 py-0.5 rounded font-mono">
            Org ID: {user?.organization_id.slice(0, 8)}...
          </span>
        </div>
        <div className="flex items-center gap-4">
          <span className="text-sm text-slate-600 font-semibold">{user?.email}</span>
          <Button
            onClick={handleLogout}
            variant="danger"
            className="px-3 py-1.5 text-xs"
          >
            Sign Out
          </Button>
        </div>
      </header>

      {/* Workspace Area */}
      <main className="flex-1 p-6">
        {dashboards.length === 0 && !showLiveStream ? (
          <div className="max-w-md mx-auto mt-20 text-center bg-white p-8 rounded-xl border border-slate-100 shadow-sm">
            <h2 className="text-lg font-bold text-slate-800 mb-2">No Dashboards Created</h2>
            <p className="text-sm text-slate-500 mb-6">
              Establish your first visual telemetry board inside Swagger UI to begin tracking live analytics metrics.
            </p>
          </div>
        ) : (
          <div className="space-y-6">
            {/* Horizontal Selector Panel */}
            <div className="flex items-center gap-2 border-b border-slate-200 pb-2">
              {dashboards.map((dash) => (
                <button
                  key={dash.id}
                  onClick={() => {
                    setActiveDashboard(dash);
                    setShowLiveStream(false);  // Toggle off stream
                  }}
                  className={`px-4 py-1.5 text-sm font-bold rounded-lg transition ${
                    !showLiveStream && activeDashboard?.id === dash.id
                      ? "bg-indigo-600 text-white"
                      : "text-slate-600 hover:bg-slate-100"
                  }`}
                >
                  {dash.name}
                </button>
              ))}
              
              {/* Added: Persistent Live Stream Tab */}
              <button
                onClick={() => {
                  setShowLiveStream(true);
                  setActiveDashboard(null);  // Toggle off dashboards
                }}
                className={`px-4 py-1.5 text-sm font-bold rounded-lg transition ml-auto flex items-center gap-2 ${
                  showLiveStream
                    ? "bg-indigo-600 text-white"
                    : "text-slate-600 hover:bg-slate-100"
                }`}
              >
                <span className={`w-2 h-2 rounded-full bg-emerald-500 ${showLiveStream ? "animate-ping" : ""}`}></span>
                Live Stream Viewer
              </button>
            </div>

            {/* Display either Live Stream Logger or Active Dashboard Widgets Grid */}
            {showLiveStream ? (
              <div className="max-w-4xl mx-auto space-y-4">
                <div>
                  <h2 className="text-2xl font-black text-slate-800">Live Telemetry Feed</h2>
                  <p className="text-slate-500 text-sm">Tail incoming multi-tenant ingestion events in real-time over secure WebSockets.</p>
                </div>
                <LiveStreamViewer />
              </div>
            ) : activeDashboard && (
              <div className="space-y-6">
                <div>
                  <h2 className="text-2xl font-black text-slate-800">{activeDashboard.name}</h2>
                  <p className="text-slate-500 text-sm">{activeDashboard.description}</p>
                </div>

                {/* Dashboard Widgets Layout Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {activeDashboard.widgets.length === 0 ? (
                    <div className="col-span-full py-12 text-center bg-white rounded-xl border border-dashed border-slate-200">
                      <p className="text-sm text-slate-500">This dashboard has no widgets configured yet.</p>
                    </div>
                  ) : (
                    activeDashboard.widgets.map((widget) => (
                      <WidgetCard 
                        key={widget.id} 
                        dashboardId={activeDashboard.id} 
                        widgetId={widget.id} 
                      />
                    ))
                  )}
                </div>
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  );
}