"use client";

import { useEffect, useState, useRef } from "react"; // Added missing useRef import
import { apiRequest } from "@/lib/api";
import Input from "./Input";
import Button from "./Button";

interface ApiKey {
  id: string;
  name: string;
  prefix: string;
  is_active: boolean;
  created_at: string;
}

export default function IntegrationsPanel() {
  const [apiKeys, setApiKeys] = useState<ApiKey[]>([]);
  const [keyName, setKeyName] = useState("");
  const [newPlainKey, setNewPlainKey] = useState("");
  const [loading, setLoading] = useState(false);
  const [fetching, setFetching] = useState(true);

  // Shared Authorization State [2]
  const [authKey, setAuthKey] = useState("");

  // CSV Ingestion States
  const [csvFile, setCsvFile] = useState<File | null>(null);
  const [csvLoading, setCsvLoading] = useState(false);
  const [csvMessage, setCsvMessage] = useState("");
  const [csvError, setCsvError] = useState("");

  // Single Event Simulator States
  const [simEventName, setSimEventName] = useState("");
  const [simProps, setSimProps] = useState('{\n  "plan": "premium",\n  "tier": "enterprise"\n}');
  const [simLoading, setSimLoading] = useState(false);
  const [simMessage, setSimMessage] = useState("");
  const [simError, setSimError] = useState("");

  // Batch Event Simulator States [2]
  const [batchProps, setBatchProps] = useState('[\n  {\n    "event_name": "page_view",\n    "properties": { "url": "/pricing" }\n  },\n  {\n    "event_name": "pricing_completed",\n    "properties": { "plan": "enterprise" }\n  }\n]');
  const [batchLoading, setBatchLoading] = useState(false);
  const [batchMessage, setBatchMessage] = useState("");
  const [batchError, setBatchError] = useState("");

  const fetchApiKeys = async () => {
    try {
      const data = await apiRequest("/api-keys");
      setApiKeys(data);
    } catch (err) {
      console.error("Failed to load API keys", err);
    } finally {
      setFetching(false);
    }
  };

  useEffect(() => {
    fetchApiKeys();
  }, []);

  const handleCreateKey = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setNewPlainKey("");
    try {
      const data = await apiRequest("/api-keys", {
        method: "POST",
        body: JSON.stringify({ name: keyName })
      });
      setNewPlainKey(data.plain_key);
      setAuthKey(data.plain_key); // Auto-fill authorization fields [2]
      setKeyName("");
      fetchApiKeys();
    } catch (err) {
      console.error("Failed to generate API Key", err);
    } finally {
      setLoading(false);
    }
  };

  const handleToggleStatus = async (keyId: string, currentStatus: boolean) => {
    try {
      await apiRequest(`/api-keys/${keyId}/status`, {
        method: "PUT",
        body: JSON.stringify({ is_active: !currentStatus })
      });
      fetchApiKeys();
    } catch (err) {
      console.error("Failed to update status", err);
    }
  };

  const handleRotateKey = async (keyId: string) => {
    try {
      setNewPlainKey("");
      const data = await apiRequest(`/api-keys/${keyId}/rotate`, { method: "PUT" });
      setNewPlainKey(data.plain_key);
      setAuthKey(data.plain_key); // Auto-fill rotated key
      fetchApiKeys();
    } catch (err) {
      console.error("Failed to rotate key", err);
    }
  };

  const handleCsvUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!csvFile || !authKey) return;
    setCsvLoading(true);
    setCsvMessage("");
    setCsvError("");

    try {
      const formData = new FormData();
      formData.append("file", csvFile);

      const BACKEND_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000/api/v1";
      const res = await fetch(`${BACKEND_URL}/ingest/csv`, {
        method: "POST",
        headers: {
          "X-API-Key": authKey
        },
        body: formData
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || "Failed to process CSV file.");
      }

      setCsvMessage(data.message || "CSV upload queued successfully.");
      setCsvFile(null);
    } catch (err: any) {
      setCsvError(err.message || "Failed to upload CSV.");
    } finally {
      setCsvLoading(false);
    }
  };

  const handleSimulateEvent = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!authKey || !simEventName) return;
    setSimLoading(true);
    setSimMessage("");
    setSimError("");

    try {
      let parsedProps = {};
      try {
        parsedProps = JSON.parse(simProps);
      } catch (pErr) {
        throw new Error("Invalid properties JSON syntax formatting.");
      }

      const BACKEND_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000/api/v1";
      const res = await fetch(`${BACKEND_URL}/ingest/single`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-API-Key": authKey
        },
        body: JSON.stringify({
          event_name: simEventName,
          properties: parsedProps
        })
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || "Failed to ingest simulated event.");
      }

      setSimMessage("Event simulated and broadcasted successfully!");
      setSimEventName("");
    } catch (err: any) {
      setSimError(err.message || "Failed to ingest event.");
    } finally {
      setSimLoading(false);
    }
  };

  const handleBatchIngest = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!authKey || !batchProps) return;
    setBatchLoading(true);
    setBatchMessage("");
    setBatchError("");

    try {
      let parsedEvents = [];
      try {
        parsedEvents = JSON.parse(batchProps);
        if (!Array.isArray(parsedEvents)) {
          throw new Error("Input must be a valid JSON array of events.");
        }
      } catch (pErr: any) {
        throw new Error(pErr.message || "Invalid JSON array formatting.");
      }

      const BACKEND_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000/api/v1";
      const res = await fetch(`${BACKEND_URL}/ingest/batch`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-API-Key": authKey
        },
        body: JSON.stringify({
          events: parsedEvents
        })
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || "Failed to ingest batch events.");
      }

      setBatchMessage("Batch events ingested and broadcasted successfully!");
    } catch (err: any) {
      setBatchError(err.message || "Failed to ingest batch.");
    } finally {
      setBatchLoading(false);
    }
  };

  if (fetching) {
    return <div className="text-center text-slate-500 text-sm py-12">Loading Credentials Panel...</div>;
  }

return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 max-w-5xl mx-auto items-stretch">
      
      {/* API Key Manager */}
      <div className="bg-white p-6 rounded-xl border border-slate-100 shadow-sm flex flex-col justify-between h-full space-y-6">
        <div>
          <h2 className="text-lg font-bold text-slate-800">API Key Manager</h2>
          <p className="text-xs text-slate-400 mt-0.5">Generate, rotate, and revoke ingestion authorization keys [2].</p>
        </div>

        {newPlainKey && (
          <div className="p-4 bg-emerald-50 border border-emerald-100 text-emerald-800 rounded-lg text-xs space-y-2">
            <p className="font-semibold">⚠️ Copy your secret key now. It will not be shown again [4]:</p>
            <code className="block bg-white p-2 rounded border border-emerald-200 font-mono select-all overflow-x-auto text-[10px] break-all">
              {newPlainKey}
            </code>
          </div>
        )}

        <form onSubmit={handleCreateKey} className="flex gap-2 items-end">
          <div className="flex-1">
            <Input
              label="Friendly Key Name"
              type="text"
              required
              value={keyName}
              onChange={(e) => setKeyName(e.target.value)}
              placeholder="e.g., Server Node Ingest"
            />
          </div>
          <Button type="submit" loading={loading} className="py-2.5 text-xs">Generate</Button>
        </form>

        <div className="space-y-3">
          <h3 className="text-xs font-black text-slate-400 uppercase tracking-wider">Registered Keys</h3>
          {apiKeys.length === 0 ? (
            <p className="text-xs text-slate-500 italic">No credentials active. Create your first key above.</p>
          ) : (
            <div className="divide-y divide-slate-100 border border-slate-100 rounded-lg overflow-hidden max-h-40 overflow-y-auto">
              {apiKeys.map((key) => (
                <div key={key.id} className="p-3 bg-slate-50/50 flex items-center justify-between text-xs">
                  <div>
                    <p className="font-semibold text-slate-800">{key.name}</p>
                    <p className="font-mono text-[9px] text-slate-400 mt-0.5">Prefix: {key.prefix} — Status: {key.is_active ? "Active" : "Revoked"}</p>
                  </div>
                  <div className="flex gap-2">
                    <Button
                      variant="secondary"
                      onClick={() => handleToggleStatus(key.id, key.is_active)}
                      className="px-2 py-1 text-[9px]"
                    >
                      {key.is_active ? "Revoke" : "Activate"}
                    </Button>
                    <Button
                      variant="secondary"
                      onClick={() => handleRotateKey(key.id)}
                      className="px-2 py-1 text-[9px] text-indigo-600 border-indigo-100 hover:bg-indigo-50"
                    >
                      Rotate
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Batch Event Simulator */}
      <div className="bg-white p-6 rounded-xl border border-slate-100 shadow-sm flex flex-col justify-between h-full space-y-6">
        <div>
          <h2 className="text-lg font-bold text-slate-800">Batch Event Simulator</h2>
          <p className="text-xs text-slate-400 mt-0.5">Mock and broadcast arrays of telemetry tracking events [2].</p>
        </div>

        {batchMessage && (
          <div className="p-3 text-xs text-emerald-600 bg-emerald-50 rounded-lg border border-emerald-100">
            {batchMessage}
          </div>
        )}

        {batchError && (
          <div className="p-3 text-xs text-red-600 bg-red-50 rounded-lg border border-red-100">
            {batchError}
          </div>
        )}

        <form onSubmit={handleBatchIngest} className="space-y-4">
          <Input
            label="X-API-Key Secret"
            type="text"
            required
            value={authKey}
            onChange={(e) => setAuthKey(e.target.value)}
            placeholder="X-API-Key"
          />

          <div>
            <label className="block text-sm font-semibold text-slate-700 mb-1">
              Custom Events Payload Array (JSON)
            </label>
            <textarea
              required
              rows={4}
              value={batchProps}
              onChange={(e) => setBatchProps(e.target.value)}
              className="w-full px-3 py-2 text-xs border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 transition font-mono text-slate-800"
            />
          </div>

          <Button type="submit" loading={batchLoading} disabled={!batchProps || !authKey} className="w-full py-2.5 text-xs">
            Simulate & Ingest Event Batch
          </Button>
        </form>
      </div>

      {/* Single Event Simulator */}
      <div className="bg-white p-6 rounded-xl border border-slate-100 shadow-sm flex flex-col justify-between h-full space-y-6">
        <div>
          <h2 className="text-lg font-bold text-slate-800">Single Event Simulator</h2>
          <p className="text-xs text-slate-400 mt-0.5">Mock and broadcast custom telemetry tracking events instantly [2].</p>
        </div>

        {simMessage && (
          <div className="p-3 text-xs text-emerald-600 bg-emerald-50 rounded-lg border border-emerald-100">
            {simMessage}
          </div>
        )}

        {simError && (
          <div className="p-3 text-xs text-red-600 bg-red-50 rounded-lg border border-red-100">
            {simError}
          </div>
        )}

        <form onSubmit={handleSimulateEvent} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <Input
              label="X-API-Key Secret"
              type="text"
              required
              value={authKey}
              onChange={(e) => setAuthKey(e.target.value)}
              placeholder="X-API-Key"
            />
            <Input
              label="Simulated Event Name"
              type="text"
              required
              value={simEventName}
              onChange={(e) => setSimEventName(e.target.value)}
              placeholder="e.g., pricing_completed"
            />
          </div>

          <div>
            <label className="block text-sm font-semibold text-slate-700 mb-1">
              Custom Properties payload (JSON)
            </label>
            <textarea
              required
              rows={4}
              value={simProps}
              onChange={(e) => setSimProps(e.target.value)}
              className="w-full px-3 py-2 text-xs border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 transition font-mono text-slate-800"
            />
          </div>

          <Button type="submit" loading={simLoading} disabled={!simEventName || !authKey} className="w-full py-2.5 text-xs">
            Simulate & Ingest Event
          </Button>
        </form>
      </div>

      {/* CSV Bulk Ingestor */}
      <div className="bg-white p-6 rounded-xl border border-slate-100 shadow-sm flex flex-col justify-between h-full space-y-6">
        <div>
          <h2 className="text-lg font-bold text-slate-800">CSV Bulk Ingestor</h2>
          <p className="text-xs text-slate-400 mt-0.5">Stream event files asynchronously using your secure API key [2].</p>
        </div>

        {csvMessage && (
          <div className="p-3 text-xs text-emerald-600 bg-emerald-50 rounded-lg border border-emerald-100">
            {csvMessage}
          </div>
        )}

        {csvError && (
          <div className="p-3 text-xs text-red-600 bg-red-50 rounded-lg border border-red-100">
            {csvError}
          </div>
        )}

        <form onSubmit={handleCsvUpload} className="space-y-4 flex-1 flex flex-col justify-between h-full">
          <Input
            label="X-API-Key Authorization Secret (CSV)"
            type="text"
            required
            value={authKey}
            onChange={(e) => setAuthKey(e.target.value)}
            placeholder="Paste your pk_live_... key here"
          />

          <div className="border-2 border-dashed border-slate-200 rounded-lg p-6 text-center hover:border-indigo-400 transition cursor-pointer relative bg-slate-50/50 flex-1 flex flex-col justify-center min-h-[110px]">
            <input
              type="file"
              accept=".csv"
              required
              onChange={(e) => setCsvFile(e.target.files?.[0] || null)}
              className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
            />
            <span className="text-xs text-slate-500 font-semibold block">
              {csvFile ? `Selected: ${csvFile.name}` : "Click or Drag & Drop .csv file here"}
            </span>
            <span className="text-[10px] text-slate-400 mt-1 block">Compatible with standard comma-separated text files.</span>
          </div>

          <Button type="submit" loading={csvLoading} disabled={!csvFile || !authKey} className="w-full py-2.5 text-xs">
            Upload & Ingest Bulk Data
          </Button>
        </form>
      </div>
    </div>
  );
}