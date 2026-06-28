"use client";

import { useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { apiRequest } from "@/lib/api";
import {
  LineChart, Line, BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, Tooltip, ResponsiveContainer
} from "recharts";

interface WidgetProps {
  dashboardId: string;
  widgetId: string;
  isPublic?: boolean;
}

const COLORS = ["#4f46e5", "#06b6d4", "#10b981", "#f59e0b", "#ef4444"];

export default function WidgetCard({ dashboardId, widgetId, isPublic = false }: WidgetProps) {  // Modified props
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  const { data, isLoading, error } = useQuery({
    queryKey: ["widgetData", dashboardId, widgetId, isPublic],
    queryFn: () => {
      const endpoint = isPublic
        ? `/dashboards/public/${dashboardId}/widgets/${widgetId}/data`
        : `/dashboards/${dashboardId}/widgets/${widgetId}/data`;
      return apiRequest(endpoint);
    },
    refetchInterval: 30000,
  });

  if (!mounted) {
    return (
      <div className="bg-white p-6 rounded-xl border border-slate-100 shadow-sm h-72 flex items-center justify-center">
        <span className="text-xs text-slate-400">Loading charts...</span>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="bg-white p-6 rounded-xl border border-slate-100 h-72 flex flex-col justify-between animate-pulse">
        <div className="h-4 bg-slate-200 rounded w-1/3"></div>
        <div className="h-40 bg-slate-100 rounded"></div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="bg-white p-6 rounded-xl border border-slate-100 h-72 flex flex-col justify-between">
        <h3 className="font-bold text-slate-800 text-sm">{data?.widget_name || "Error Loading Widget"}</h3>
        <div className="h-40 flex items-center justify-center bg-red-50 text-red-600 rounded-lg text-xs font-semibold p-4 text-center">
          Failed to fetch widget telemetry data.
        </div>
      </div>
    );
  }

  const chartData = data.data || [];
  const totalValue = chartData.reduce((sum: number, item: any) => sum + item.value, 0);

  return (
    <div className="bg-white p-6 rounded-xl border border-slate-100 shadow-sm h-72 flex flex-col justify-between">
      <div>
        <div className="flex items-center justify-between">
          <h3 className="font-bold text-slate-800 text-sm truncate max-w-[150px]">{data.widget_name}</h3>
          <span className="text-[9px] bg-slate-100 text-slate-500 px-2 py-0.5 rounded font-mono uppercase">
            {data.interval}ly buckets
          </span>
        </div>
        <p className="text-[10px] text-slate-400 uppercase font-black tracking-wider mt-0.5">
          {data.type} — {data.event_name}
        </p>
      </div>

      <div className="h-44 mt-4">
        {chartData.length === 0 ? (
          <div className="h-full flex items-center justify-center bg-slate-50 rounded-lg border border-dashed border-slate-200 text-xs text-slate-400">
            No telemetry recorded in past {data.time_range_hours}h
          </div>
        ) : data.type === "kpi" ? (
          <div className="h-full flex flex-col items-center justify-center bg-indigo-50/50 rounded-lg border border-indigo-100">
            <span className="text-4xl font-black text-indigo-600">{totalValue}</span>
            <span className="text-[9px] font-bold text-indigo-500 uppercase tracking-wider mt-1">
              Accumulated Count
            </span>
          </div>
        ) : data.type === "table" ? (
          <div className="h-full overflow-y-auto text-xs border border-slate-100 rounded-lg">
            <table className="w-full text-left">
              <thead className="bg-slate-50 text-slate-500 sticky top-0">
                <tr>
                  <th className="p-2 font-bold">Bucket Interval</th>
                  <th className="p-2 font-bold text-right">Count</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-slate-700">
                {chartData.slice(-5).reverse().map((item: any, idx: number) => (
                  <tr key={idx}>
                    <td className="p-2 font-mono">
                      {new Date(item.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                    </td>
                    <td className="p-2 text-right font-semibold">{item.value}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : data.type === "line" ? (
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData}>
              <XAxis dataKey="timestamp" tickFormatter={(t) => new Date(t).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })} tick={{ fontSize: 9 }} stroke="#cbd5e1" />
              <YAxis tick={{ fontSize: 9 }} stroke="#cbd5e1" />
              <Tooltip labelFormatter={(t) => new Date(t).toLocaleString()} contentStyle={{ fontSize: 11, borderRadius: 8, borderColor: "#f1f5f9" }} />
              <Line type="monotone" dataKey="value" stroke="#4f46e5" strokeWidth={2.5} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        ) : data.type === "bar" ? (
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData}>
              <XAxis dataKey="timestamp" tickFormatter={(t) => new Date(t).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })} tick={{ fontSize: 9 }} stroke="#cbd5e1" />
              <YAxis tick={{ fontSize: 9 }} stroke="#cbd5e1" />
              <Tooltip labelFormatter={(t) => new Date(t).toLocaleString()} contentStyle={{ fontSize: 11, borderRadius: 8, borderColor: "#f1f5f9" }} />
              <Bar dataKey="value" fill="#4f46e5" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        ) : data.type === "pie" ? (
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie data={chartData} dataKey="value" nameKey="timestamp" cx="50%" cy="50%" outerRadius={50} labelLine={false}>
                {chartData.map((_: any, index: number) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip labelFormatter={(t) => new Date(t).toLocaleTimeString()} contentStyle={{ fontSize: 10, borderRadius: 8 }} />
            </PieChart>
          </ResponsiveContainer>
        ) : null}
      </div>
    </div>
  );
}