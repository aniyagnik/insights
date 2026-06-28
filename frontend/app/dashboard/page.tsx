"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/store/authStore";
import { apiRequest } from "@/lib/api";
import Button from "@/components/Button";
import Input from "@/components/Input";
import Modal from "@/components/Modal";
import WidgetCard from "@/components/WidgetCard";
import LiveStreamViewer from "@/components/LiveStreamViewer";
import IntegrationsPanel from "@/components/IntegrationsPanel";
import AlertsAndTeamPanel from "@/components/AlertsAndTeamPanel"; 
interface Dashboard {
  id: string;
  name: string;
  description: string;
  widgets: any[];
  is_public: boolean;
}

export default function DashboardPage() {
  const { user, isAuthenticated, clearAuth } = useAuthStore();
  const router = useRouter();
  
  const [dashboards, setDashboards] = useState<Dashboard[]>([]);
  const [activeDashboard, setActiveDashboard] = useState<Dashboard | null>(null);
  const [showLiveStream, setShowLiveStream] = useState(false);
  const [showIntegrations, setShowIntegrations] = useState(false);  // Added state [2]
  const [showTeamAlerts, setShowTeamAlerts] = useState(false); 
  const [loading, setLoading] = useState(true);

  // Dashboard creation states
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [dashName, setDashName] = useState("");
  const [dashDesc, setDashDesc] = useState("");
  const [isPublic, setIsPublic] = useState(false);
  const [createLoading, setCreateLoading] = useState(false);

  // Widget creation states
  const [isWidgetOpen, setIsWidgetOpen] = useState(false);
  const [widgetName, setWidgetName] = useState("");
  const [widgetType, setWidgetType] = useState("line");
  const [eventName, setEventName] = useState("");
  const [timeRangeHours, setTimeRangeHours] = useState("24");
  const [interval, setInterval] = useState("hour");
  const [widgetLoading, setWidgetLoading] = useState(false);

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

  const handleCreateDashboard = async (e: React.FormEvent) => {
    e.preventDefault();
    setCreateLoading(true);

    try {
      const newDash = await apiRequest("/dashboards", {
        method: "POST",
        body: JSON.stringify({
          name: dashName,
          description: dashDesc,
          is_public: isPublic
        })
      });

      setDashboards((prev) => [...prev, newDash]);
      setActiveDashboard(newDash);
      setShowLiveStream(false);
      setShowIntegrations(false);  // Ensure closed on select

      setDashName("");
      setDashDesc("");
      setIsPublic(false);
      setIsCreateOpen(false);
    } catch (err) {
      console.error("Failed to create dashboard", err);
    } finally {
      setCreateLoading(false);
    }
  };

  const handleCreateWidget = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeDashboard) return;
    setWidgetLoading(true);

    try {
      const newWidget = await apiRequest(`/dashboards/${activeDashboard.id}/widgets`, {
        method: "POST",
        body: JSON.stringify({
          name: widgetName,
          type: widgetType,
          query_config: {
            event_name: eventName,
            time_range_hours: parseInt(timeRangeHours),
            interval: interval
          }
        })
      });

      setDashboards((prev) =>
        prev.map((dash) => {
          if (dash.id === activeDashboard.id) {
            return {
              ...dash,
              widgets: [...dash.widgets, newWidget]
            };
          }
          return dash;
        })
      );

      setActiveDashboard((prev) => {
        if (!prev) return null;
        return {
          ...prev,
          widgets: [...prev.widgets, newWidget]
        };
      });

      setWidgetName("");
      setWidgetType("line");
      setEventName("");
      setTimeRangeHours("24");
      setInterval("hour");
      setIsWidgetOpen(false);
    } catch (err) {
      console.error("Failed to create widget", err);
    } finally {
      setWidgetLoading(false);
    }
  };

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
        <span className="text-sm font-semibold text-slate-500 animate-pulse">Loading Workspace...</span>
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
        {dashboards.length === 0 && !showLiveStream && !showIntegrations && !showTeamAlerts ? (
          <div className="max-w-md mx-auto mt-20 text-center bg-white p-8 rounded-xl border border-slate-100 shadow-sm">
            <h2 className="text-lg font-bold text-slate-800 mb-2">No Dashboards Created</h2>
            <p className="text-sm text-slate-500 mb-6">
              Establish your first visual telemetry board to begin tracking live analytics metrics [2].
            </p>
            <Button onClick={() => setIsCreateOpen(true)} className="mx-auto text-xs">
              Create First Dashboard
            </Button>
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
                    setShowLiveStream(false);
                    setShowIntegrations(false);
                    setShowTeamAlerts(false);  // Toggle off team alerts
                  }}
                  className={`px-4 py-1.5 text-sm font-bold rounded-lg transition ${
                    !showLiveStream && !showIntegrations && !showTeamAlerts && activeDashboard?.id === dash.id
                      ? "bg-indigo-600 text-white"
                      : "text-slate-600 hover:bg-slate-100"
                  }`}
                >
                  {dash.name}
                </button>
              ))}
              
              {/* Create Dashboard inline button */}
              <button
                onClick={() => setIsCreateOpen(true)}
                className="px-3 py-1 text-xs font-extrabold text-slate-500 hover:text-indigo-600 bg-slate-100 hover:bg-indigo-50 border border-slate-200 hover:border-indigo-100 rounded-lg transition ml-1"
              >
                + Add Board
              </button>

              {/* Persistent Live Stream Tab */}
              <button
                onClick={() => {
                  setShowLiveStream(true);
                  setActiveDashboard(null);
                  setShowIntegrations(false);
                  setShowTeamAlerts(false);
                }}
                className={`px-4 py-1.5 text-sm font-bold rounded-lg transition ml-auto flex items-center gap-2 ${
                  showLiveStream
                    ? "bg-indigo-600 text-white"
                    : "text-slate-600 hover:bg-slate-100"
                }`}
              >
                <span className={`w-2 h-2 rounded-full bg-emerald-500 ${showLiveStream ? "animate-ping" : ""}`}></span>
                Live Stream
              </button>

              {/* Developer Settings Tab */}
              <button
                onClick={() => {
                  setShowIntegrations(true);
                  setShowLiveStream(false);
                  setActiveDashboard(null);
                  setShowTeamAlerts(false);
                }}
                className={`px-4 py-1.5 text-sm font-bold rounded-lg transition flex items-center gap-2 ${
                  showIntegrations
                    ? "bg-indigo-600 text-white"
                    : "text-slate-600 hover:bg-slate-100"
                }`}
              >
                Developer Settings
              </button>

              <button
                onClick={() => {
                  setShowTeamAlerts(true);
                  setShowIntegrations(false);
                  setShowLiveStream(false);
                  setActiveDashboard(null);
                }}
                className={`px-4 py-1.5 text-sm font-bold rounded-lg transition flex items-center gap-2 ${
                  showTeamAlerts
                    ? "bg-indigo-600 text-white"
                    : "text-slate-600 hover:bg-slate-100"
                }`}
              >
                Team & Alerts
              </button>
            </div>

            {showTeamAlerts ? (
              <div className="max-w-5xl mx-auto space-y-4">
                <div>
                  <h2 className="text-2xl font-black text-slate-800">Workspace Management</h2>
                  <p className="text-slate-500 text-sm">Onboard colleagues and configure system metric alerts [2].</p>
                </div>
                <AlertsAndTeamPanel />
              </div>
            ) : showIntegrations ? (
              <div className="max-w-5xl mx-auto space-y-4">
                <div>
                  <h2 className="text-2xl font-black text-slate-800">Developer Integrations</h2>
                  <p className="text-slate-500 text-sm">Provision access credentials and upload bulk telemetry records [2].</p>
                </div>
                <IntegrationsPanel />
              </div>
            ) : showLiveStream ? (
              <div className="max-w-4xl mx-auto space-y-4">
                <div>
                  <h2 className="text-2xl font-black text-slate-800">Live Telemetry Feed</h2>
                  <p className="text-slate-500 text-sm">Tail incoming multi-tenant ingestion events in real-time over secure WebSockets.</p>
                </div>
                <LiveStreamViewer />
              </div>
            ) : activeDashboard && (
              <div className="space-y-6">
                <div className="flex items-center justify-between">
                  <div>
                    <h2 className="text-2xl font-black text-slate-800">{activeDashboard.name}</h2>
                    <p className="text-slate-500 text-sm">{activeDashboard.description}</p>
                  </div>
                  
                  {/* Dashboard Action Header Panel */}
                  <div className="flex items-center gap-3">
                    {activeDashboard.is_public && (
                      <span className="text-[10px] bg-emerald-50 text-emerald-700 px-2.5 py-1 rounded-full font-bold uppercase tracking-wider border border-emerald-100 select-none">
                        Public Share Link Active
                      </span>
                    )}
                    <Button
                      onClick={() => setIsWidgetOpen(true)}
                      className="px-3 py-1.5 text-xs font-extrabold"
                    >
                      + Add Chart Widget
                    </Button>
                  </div>
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

      {/* Reusable Dashboard Creation Modal Form */}
      <Modal
        isOpen={isCreateOpen}
        onClose={() => setIsCreateOpen(false)}
        title="Create Custom Dashboard"
      >
        <form onSubmit={handleCreateDashboard} className="space-y-4">
          <Input
            label="Dashboard Name"
            type="text"
            required
            value={dashName}
            onChange={(e) => setDashName(e.target.value)}
            placeholder="e.g., Marketing Analytics"
          />
          <Input
            label="Description (Optional)"
            type="text"
            value={dashDesc}
            onChange={(e) => setDashDesc(e.target.value)}
            placeholder="Brief summary of visual metrics"
          />
          
          <div className="flex items-center gap-2 pt-2 pb-2">
            <input
              type="checkbox"
              id="isPublic"
              checked={isPublic}
              onChange={(e) => setIsPublic(e.target.checked)}
              className="w-4 h-4 text-indigo-600 focus:ring-indigo-500 border-slate-300 rounded"
            />
            <label htmlFor="isPublic" className="text-xs font-bold text-slate-700 select-none cursor-pointer">
              Make Dashboard Public (Read-Only Share Link)
            </label>
          </div>

          <div className="flex items-center justify-end gap-2 pt-4 border-t border-slate-100">
            <Button
              type="button"
              variant="secondary"
              onClick={() => setIsCreateOpen(false)}
            >
              Cancel
            </Button>
            <Button type="submit" loading={createLoading}>
              Create Dashboard
            </Button>
          </div>
        </form>
      </Modal>

      {/* Reusable Widget Creation Modal Form */}
      <Modal
        isOpen={isWidgetOpen}
        onClose={() => setIsWidgetOpen(false)}
        title={`Add Widget to ${activeDashboard?.name}`}
      >
        <form onSubmit={handleCreateWidget} className="space-y-4">
          <Input
            label="Widget Name"
            type="text"
            required
            value={widgetName}
            onChange={(e) => setWidgetName(e.target.value)}
            placeholder="e.g., Active Checkout Count"
          />
          
          <div>
            <label className="block text-sm font-semibold text-slate-700 mb-1">
              Chart Visualization Type
            </label>
            <select
              value={widgetType}
              onChange={(e) => setWidgetType(e.target.value)}
              className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 transition text-slate-800"
            >
              <option value="line">Line Chart</option>
              <option value="bar">Bar Chart</option>
              <option value="pie">Pie Chart</option>
              <option value="kpi">KPI Card</option>
              <option value="table">Data Table</option>
            </select>
          </div>

          <Input
            label="Target Tracking Event Name"
            type="text"
            required
            value={eventName}
            onChange={(e) => setEventName(e.target.value)}
            placeholder="e.g., checkout_completed"
          />

          <div className="grid grid-cols-2 gap-4">
            <Input
              label="Lookback Range (Hours)"
              type="number"
              required
              value={timeRangeHours}
              onChange={(e) => setTimeRangeHours(e.target.value)}
            />
            <div>
              <label className="block text-sm font-semibold text-slate-700 mb-1">
                Time Interval Step
              </label>
              <select
                value={interval}
                onChange={(e) => setInterval(e.target.value)}
                className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 transition text-slate-800"
              >
                <option value="hour">Hourly Buckets</option>
                <option value="day">Daily Buckets</option>
              </select>
            </div>
          </div>

          <div className="flex items-center justify-end gap-2 pt-4 border-t border-slate-100">
            <Button
              type="button"
              variant="secondary"
              onClick={() => setIsWidgetOpen(false)}
            >
              Cancel
            </Button>
            <Button type="submit" loading={widgetLoading}>
              Add Widget
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}