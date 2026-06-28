"use client";

import { useEffect, useState } from "react";
import { apiRequest } from "@/lib/api";
import Input from "./Input";
import Button from "./Button";

interface Invitation {
  id: string;
  email: string;
  role: string;
  token: string;
  is_accepted: boolean;
  expires_at: string;
}

// Added: Strictly typed Alert History mapping [2]
interface AlertHistory {
  id: string;
  triggered_value: number;
  status_at_trigger: string;
  created_at: string;
  ruleName?: string;
  eventName?: string;
}

interface AlertRule {
  id: string;
  name: string;
  event_name: string;
  threshold: number;
  time_window_minutes: number;
  status: string;
  history: AlertHistory[];  // Map history array
}

export default function AlertsAndTeamPanel() {
  // Invite States
  const [invites, setInvites] = useState<Invitation[]>([]);
  const [inviteEmail, setInviteEmail] = useState("");
  const [inviteRole, setInviteRole] = useState("viewer");
  const [inviteLoading, setInviteLoading] = useState(false);

  // Alert States
  const [alerts, setAlerts] = useState<AlertRule[]>([]);
  const [alertName, setAlertName] = useState("");
  const [eventName, setEventName] = useState("");
  const [threshold, setThreshold] = useState("");
  const [windowMinutes, setWindowMinutes] = useState("10");
  const [alertLoading, setAlertLoading] = useState(false);

  const [fetching, setFetching] = useState(true);

  const [origin, setOrigin] = useState("");
  useEffect(() => {
    setOrigin(window.location.origin);
  }, []);

  const fetchData = async () => {
    try {
      const [invitesData, alertsData] = await Promise.all([
        apiRequest("/invites"),
        apiRequest("/alerts")
      ]);
      setInvites(invitesData);
      setAlerts(alertsData);
    } catch (err) {
      console.error("Failed to load panel data", err);
    } finally {
      setFetching(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleCreateInvite = async (e: React.FormEvent) => {
    e.preventDefault();
    setInviteLoading(true);
    try {
      await apiRequest("/invites", {
        method: "POST",
        body: JSON.stringify({ email: inviteEmail, role: inviteRole })
      });
      setInviteEmail("");
      setInviteRole("viewer");
      fetchData();
    } catch (err) {
      console.error("Failed to create invite", err);
    } finally {
      setInviteLoading(false);
    }
  };

  const handleCreateAlert = async (e: React.FormEvent) => {
    e.preventDefault();
    setAlertLoading(true);
    try {
      await apiRequest("/alerts", {
        method: "POST",
        body: JSON.stringify({
          name: alertName,
          event_name: eventName,
          threshold: parseFloat(threshold),
          time_window_minutes: parseInt(windowMinutes)
        })
      });
      setAlertName("");
      setEventName("");
      setThreshold("");
      setWindowMinutes("10");
      fetchData();
    } catch (err) {
      console.error("Failed to configure alert rule", err);
    } finally {
      setAlertLoading(false);
    }
  };

  // Added: Toggles alert statuses between active and muted [2]
  const handleToggleMute = async (alertId: string, currentStatus: string) => {
    try {
      const nextStatus = currentStatus === "muted" ? "active" : "muted";
      await apiRequest(`/alerts/${alertId}`, {
        method: "PUT",
        body: JSON.stringify({ status: nextStatus })
      });
      fetchData();
    } catch (err) {
      console.error("Failed to toggle alert status", err);
    }
  };

  const handleDeleteAlert = async (alertId: string) => {
    try {
      await apiRequest(`/alerts/${alertId}`, { method: "DELETE" });
      fetchData();
    } catch (err) {
      console.error("Failed to delete alert rule", err);
    }
  };

  // Flatten, sort, and slice history logs chronologically [2]
  const alertHistoryList: AlertHistory[] = alerts
    .flatMap((al) =>
      al.history.map((hist) => ({
        ...hist,
        ruleName: al.name,
        eventName: al.event_name
      }))
    )
    .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
    .slice(0, 15); // Show latest 15 logs

  if (fetching) {
    return <div className="text-center text-slate-500 text-sm py-12">Loading Workspace Administration...</div>;
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 max-w-5xl mx-auto items-stretch">
      {/* Left Column: Team Onboarding */}
      <div className="bg-white p-6 rounded-xl border border-slate-100 shadow-sm space-y-6 flex flex-col justify-between h-full">
        <div>
          <h2 className="text-lg font-bold text-slate-800">Team Onboarding</h2>
          <p className="text-xs text-slate-400 mt-0.5">Invite new colleagues and assign workspace roles [2].</p>
        </div>

        <form onSubmit={handleCreateInvite} className="space-y-4">
          <Input
            label="Invitee Email Address"
            type="email"
            required
            value={inviteEmail}
            onChange={(e) => setInviteEmail(e.target.value)}
            placeholder="colleague@company.com"
          />
          
          <div>
            <label className="block text-sm font-semibold text-slate-700 mb-1">
              Assign Workspace Role
            </label>
            <select
              value={inviteRole}
              onChange={(e) => setInviteRole(e.target.value)}
              className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 transition text-slate-800"
            >
              <option value="viewer">Viewer (Read-Only)</option>
              <option value="analyst">Analyst (Query Metrics)</option>
              <option value="admin">Admin (Manage Keys/Dashboards)</option>
            </select>
          </div>

          <Button type="submit" loading={inviteLoading} className="w-full py-2.5 text-xs mt-2">
            Send Invitation Link
          </Button>
        </form>

        <div className="space-y-3">
          <h3 className="text-xs font-black text-slate-400 uppercase tracking-wider">Pending Invites</h3>
          {invites.length === 0 ? (
            <p className="text-xs text-slate-500 italic">No pending team invitations found.</p>
          ) : (
            <div className="divide-y divide-slate-100 border border-slate-100 rounded-lg overflow-hidden max-h-48 overflow-y-auto">
              {invites.map((inv) => (
                <div key={inv.id} className="p-3 bg-slate-50/50 flex items-center justify-between text-xs gap-4">
                  <div className="shrink-0">
                    <p className="font-semibold text-slate-800 truncate max-w-[100px]">{inv.email}</p>
                    <p className="font-mono text-[9px] text-slate-400 mt-0.5">Role: {inv.role}</p>
                  </div>
                  <span className="font-mono text-[9px] bg-white border border-slate-200 text-indigo-600 px-2 py-1 rounded truncate select-all">
                    {origin}/invite/accept?token={inv.token}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Right Column: Alert Rules */}
      <div className="bg-white p-6 rounded-xl border border-slate-100 shadow-sm space-y-6 flex flex-col justify-between h-full">
        <div>
          <h2 className="text-lg font-bold text-slate-800">Metrics Alert Rules</h2>
          <p className="text-xs text-slate-400 mt-0.5">Define sliding-window metric thresholds monitored by Celery Beat [2].</p>
        </div>

        <form onSubmit={handleCreateAlert} className="space-y-4">
          <Input
            label="Alert Rule Name"
            type="text"
            required
            value={alertName}
            onChange={(e) => setAlertName(e.target.value)}
            placeholder="e.g., High Error Frequency Warning"
          />
          <div className="grid grid-cols-2 gap-4">
            <Input
              label="Target Event Name"
              type="text"
              required
              value={eventName}
              onChange={(e) => setEventName(e.target.value)}
              placeholder="e.g., error_occurred"
            />
            <Input
              label="Trigger Threshold"
              type="number"
              required
              value={threshold}
              onChange={(e) => setThreshold(e.target.value)}
              placeholder="e.g., 5"
            />
          </div>
          <Input
            label="Sliding Window (Minutes)"
            type="number"
            required
            value={windowMinutes}
            onChange={(e) => setWindowMinutes(e.target.value)}
          />
          <Button type="submit" loading={alertLoading} className="w-full py-2.5 text-xs mt-2">
            Create Alert Rule
          </Button>
        </form>

        <div className="space-y-3">
          <h3 className="text-xs font-black text-slate-400 uppercase tracking-wider">Configured Rules</h3>
          {alerts.length === 0 ? (
            <p className="text-xs text-slate-500 italic">No alert rules configured. Create one above.</p>
          ) : (
            <div className="divide-y divide-slate-100 border border-slate-100 rounded-lg overflow-hidden max-h-40 overflow-y-auto">
              {alerts.map((al) => (
                <div key={al.id} className="p-3 bg-slate-50/50 flex items-center justify-between text-xs">
                  <div>
                    <div className="flex items-center gap-2">
                      <p className="font-semibold text-slate-800">{al.name}</p>
                      {/* Color status indicators: Pulse red if triggered, gray if muted, green if active normal [2] */}
                      <span className={`w-1.5 h-1.5 rounded-full ${al.status === "triggered" ? "bg-rose-500 animate-pulse" : al.status === "muted" ? "bg-slate-400" : "bg-emerald-500"}`}></span>
                    </div>
                    <p className="text-[10px] text-slate-400 mt-0.5">Threshold: {al.threshold} hits / {al.time_window_minutes}min ({al.event_name})</p>
                  </div>
                  <div className="flex gap-2">
                    {/* Added: Mute/Unmute Action Toggle */}
                    <Button
                      variant="secondary"
                      onClick={() => handleToggleMute(al.id, al.status)}
                      className="px-2 py-1 text-[9px]"
                    >
                      {al.status === "muted" ? "Unmute" : "Mute"}
                    </Button>
                    <Button
                      variant="danger"
                      onClick={() => handleDeleteAlert(al.id)}
                      className="px-2 py-1 text-[9px]"
                    >
                      Delete
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Added: Symmetrical Alert Resolution & Trigger History Feed [2] */}
      <div className="col-span-1 lg:col-span-2 bg-white p-6 rounded-xl border border-slate-100 shadow-sm space-y-4">
        <div>
          <h2 className="text-lg font-bold text-slate-800">Alert Trigger History Feed</h2>
          <p className="text-xs text-slate-400 mt-0.5">Chronological resolution and threshold breach event logs [2].</p>
        </div>
        
        <div className="border border-slate-100 rounded-xl overflow-hidden text-xs">
          <table className="w-full text-left">
            <thead className="bg-slate-50 text-slate-500 font-bold border-b border-slate-100">
              <tr>
                <th className="p-3">Logged Date</th>
                <th className="p-3">Alert Rule Name</th>
                <th className="p-3">Target Event Name</th>
                <th className="p-3">Observed Value</th>
                <th className="p-3 text-right">Logged Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-slate-700">
              {alertHistoryList.length === 0 ? (
                <tr>
                  <td colSpan={5} className="p-8 text-center text-slate-400 italic">No alert history logs found in the database. Ensure Celery Beat is active.</td>
                </tr>
              ) : (
                alertHistoryList.map((hist) => (
                  <tr key={hist.id} className="hover:bg-slate-50/50 transition">
                    <td className="p-3 font-mono text-[10px]">{new Date(hist.created_at).toLocaleString()}</td>
                    <td className="p-3 font-semibold text-slate-800">{hist.ruleName}</td>
                    <td className="p-3 font-mono text-[10px] text-slate-500">{hist.eventName}</td>
                    <td className="p-3 font-bold text-slate-700">{hist.triggered_value}</td>
                    <td className="p-3 text-right font-black">
                      <span className={`px-2 py-0.5 rounded text-[10px] uppercase border ${hist.status_at_trigger === "triggered" ? "bg-red-50 text-red-700 border-red-100" : "bg-emerald-50 text-emerald-700 border-emerald-100"}`}>
                        {hist.status_at_trigger}
                      </span>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}