"use client";

import { useEffect, useState, useRef } from "react";
import { useAuthStore } from "@/store/authStore";

interface LiveEvent {
  event_name: string;
  properties: Record<string, any>;
  timestamp: string;
}

export default function LiveStreamViewer() {
  const accessToken = useAuthStore((state) => state.accessToken);
  const [events, setEvents] = useState<LiveEvent[]>([]);
  const [connected, setConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    if (!accessToken) return;

    // Establish persistent secure connection to backend WebSocket
    const wsUrl = `ws://127.0.0.1:8000/api/v1/ws/events?token=${accessToken}`;
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      setConnected(true);
    };

    ws.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data);
        
        // Handle single and batch event stream notifications
        if (payload.type === "live_event") {
          const newEvent: LiveEvent = payload.data;
          setEvents((prev) => [newEvent, ...prev].slice(0, 50));
        } else if (payload.type === "batch") {
          const newEvents: LiveEvent[] = payload.events;
          setEvents((prev) => [...newEvents, ...prev].slice(0, 50));
        }
      } catch (err) {
        console.error("Failed to parse websocket message", err);
      }
    };

    ws.onclose = () => {
      setConnected(false);
    };

    // Clean up connection channel on unmount
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [accessToken]);

  return (
    <div className="bg-slate-900 text-slate-100 p-6 rounded-xl shadow-md border border-slate-800 flex flex-col h-[500px]">
      {/* Sockets Status Header */}
      <div className="flex items-center justify-between pb-4 border-b border-slate-800 mb-4">
        <div className="flex items-center gap-3">
          <span className={`w-2.5 h-3 rounded-full ${connected ? "bg-emerald-500 animate-pulse" : "bg-rose-500"}`}></span>
          <h3 className="font-semibold text-sm">Real-Time Ingestion Event Log</h3>
        </div>
        <span className="text-[10px] font-mono bg-slate-800 text-slate-400 px-2 py-0.5 rounded uppercase">
          {connected ? "Active" : "Offline"}
        </span>
      </div>

      {/* Terminal Display */}
      <div className="flex-1 overflow-y-auto space-y-3 font-mono text-xs">
        {events.length === 0 ? (
          <div className="h-full flex items-center justify-center text-slate-500 italic">
            Awaiting incoming telemetry streams... Ingest events via API or CSV to tail logs in real-time.
          </div>
        ) : (
          events.map((evt, idx) => (
            <div key={idx} className="p-3 bg-slate-950/60 rounded-lg border border-slate-800/80 hover:border-slate-700/60 transition">
              <div className="flex items-center justify-between mb-1.5 text-slate-400">
                <span className="font-bold text-indigo-400">{evt.event_name}</span>
                <span>{new Date(evt.timestamp).toLocaleTimeString()}</span>
              </div>
              <pre className="text-slate-300 overflow-x-auto whitespace-pre-wrap leading-relaxed text-[11px]">
                {JSON.stringify(evt.properties, null, 2)}
              </pre>
            </div>
          ))
        )}
      </div>
    </div>
  );
}