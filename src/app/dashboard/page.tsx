"use client";

import React, { useState } from "react";
import {
  Zap, Activity, Server, GitBranch,
  ArrowUpRight, ArrowDownRight, Clock, CreditCard,
  Key, Settings, LogOut, ChevronRight, ChevronDown, ChevronUp,
  Play, Square, Terminal, Layers,
  Crown
} from "lucide-react";

// ─── Types ───────────────────────────────────────────────────────
type LogEntry = { time: string; level: "info" | "success" | "error" | "warn"; message: string };
type Tool = { name: string; description: string; params: any[] };
type ServerConfig = { command: string; args: string; status: "idle" | "connecting" | "connected" | "error"; message: string; tools: Tool[] };
type UsageStat = { label: string; value: string | number; limit: string | number; unit: string; percentage: number; trend?: "up" | "down" };
type RecentActivity = { id: string; action: string; server: string; time: string; status: "success" | "error" | "warning" };

const PRESETS = [
  { label: "Filesystem (npx)", command: "npx", args: "-y @modelcontextprotocol/server-filesystem /tmp" },
  { label: "GitHub (npx)", command: "npx", args: "-y @modelcontextprotocol/server-github" },
  { label: "SQLite (npx)", command: "npx", args: "-y @modelcontextprotocol/server-sqlite" },
  { label: "Fetch (npx)", command: "npx", args: "-y @modelcontextprotocol/server-fetch" },
  { label: "Sequential Thinking (npx)", command: "npx", args: "-y @modelcontextprotocol/server-sequentialthinking" },
];

function timeAgo(iso: string): string {
  const then = new Date(iso).getTime();
  if (isNaN(then)) return "";
  const diff = Math.max(0, Date.now() - then);
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins} minute${mins === 1 ? "" : "s"} ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours} hour${hours === 1 ? "" : "s"} ago`;
  const days = Math.floor(hours / 24);
  return `${days} day${days === 1 ? "" : "s"} ago`;
}

// ─── Components ──────────────────────────────────────────────────
export default function DashboardPage() {
  const [activeTab, setActiveTab] = useState(0);
  const [expandedTool, setExpandedTool] = useState<string | null>(null);
  const [toolResults, setToolResults] = useState<Record<string, { status: "idle" | "loading" | "success" | "error"; output: string }>>({});
  const [paramValues, setParamValues] = useState<Record<string, Record<string, string>>>({});
  const [logs, setLogs] = useState<LogEntry[]>([
    { time: new Date().toLocaleTimeString(), level: "info", message: "MCP Workbench initialized. Ready to connect." },
  ]);
  const [config, setConfig] = useState<ServerConfig>({ command: "npx", args: "-y @modelcontextprotocol/server-filesystem /tmp", status: "idle", message: "", tools: [] });
  const [commandInput, setCommandInput] = useState("npx");
  const [argsInput, setArgsInput] = useState("-y @modelcontextprotocol/server-filesystem /tmp");
  const [selectedPreset, setSelectedPreset] = useState(0);
  const [showPresets, setShowPresets] = useState(false);
  const [showMobileMenu, setShowMobileMenu] = useState(false);
  const [userEmail, setUserEmail] = useState("");
  const [userTier, setUserTier] = useState("Free");
  const [usageStats, setUsageStats] = useState<UsageStat[]>([]);
  const [recentActivity, setRecentActivity] = useState<RecentActivity[]>([]);
  const wsRef = React.useRef<WebSocket | null>(null);

  React.useEffect(() => {
    const token = localStorage.getItem("mcpwb_token");
    if (!token) {
      window.location.href = "/login";
      return;
    }
    const userRaw = localStorage.getItem("mcpwb_user");
    if (userRaw) {
      try {
        const u = JSON.parse(userRaw);
        setUserEmail(u.email || "");
      } catch {}
    }
    const authHeaders = { Authorization: `Bearer ${token}` };

    fetch("/api/subscriptions", { headers: authHeaders })
      .then((r) => (r.ok ? r.json() : null))
      .then((data) => {
        if (data && data.subscription) {
          const t = data.subscription.tier;
          setUserTier(t.charAt(0).toUpperCase() + t.slice(1));
        }
      })
      .catch(() => {});

    fetch("/api/usage", { headers: authHeaders })
      .then((r) => (r.ok ? r.json() : null))
      .then((data) => {
        if (!data) return;
        const limit = data.session_limit;
        const used = data.session_count;
        const pct = limit > 0 ? Math.min(100, Math.round((used / limit) * 100)) : 0;
        setUsageStats([
          {
            label: "MCP Sessions",
            value: used,
            limit: limit === -1 ? "∞" : limit,
            unit: "this month",
            percentage: pct,
            trend: "up",
          },
          {
            label: "Remaining",
            value: data.remaining === "unlimited" ? "∞" : data.remaining,
            limit: limit === -1 ? "∞" : limit,
            unit: "sessions",
            percentage: 100 - pct,
          },
          {
            label: "Plan",
            value: data.tier.charAt(0).toUpperCase() + data.tier.slice(1),
            limit: "tier",
            unit: "",
            percentage: data.tier === "free" ? 20 : 100,
          },
        ]);
      })
      .catch(() => {});

    fetch("/api/activity", { headers: authHeaders })
      .then((r) => (r.ok ? r.json() : null))
      .then((data) => {
        if (!data || !Array.isArray(data.activity)) return;
        const items: RecentActivity[] = data.activity.map((a: any) => ({
          id: a.session_id,
          action: a.tool_calls > 0 ? `Server Test (${a.tool_calls} tool calls)` : "Server Test",
          server: a.command || "MCP server",
          time: timeAgo(a.started_at),
          status: a.status === "success" ? "success" : "error",
        }));
        setRecentActivity(items);
      })
      .catch(() => {});
  }, []);

  const addLog = (level: LogEntry["level"], message: string) => {
    setLogs((prev) => [...prev.slice(-99), { time: new Date().toLocaleTimeString(), level, message }]);
  };

  const handleConnect = () => {
    if (config.status === "connecting" || config.status === "connected") return;
    setConfig((c) => ({ ...c, status: "connecting", message: "Opening WebSocket...", tools: [] }));
    setToolResults({});
    addLog("info", `Connecting: ${commandInput} ${argsInput}`);

    const token = localStorage.getItem("mcpwb_token") || "";
    const proto = window.location.protocol === "https:" ? "wss:" : "ws:";
    const ws = new WebSocket(`${proto}//${window.location.host}/ws?token=${encodeURIComponent(token)}`);
    wsRef.current = ws;
    let initReceived = false;
    let toolsReceived = false;

    ws.onopen = () => {
      addLog("success", "WebSocket connected");
      const args = argsInput.trim().split(/\s+/);
      ws.send(JSON.stringify({ command: commandInput, args }));
      addLog("info", `Spawning: ${commandInput} ${argsInput}`);
    };

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        if (msg.type === "error") {
          addLog("error", msg.message);
          setConfig((c) => ({ ...c, status: "error", message: msg.message }));
          ws.close();
          return;
        }
        if (msg.type === "message" && msg.payload) {
          const payload = msg.payload;
          addLog("info", JSON.stringify(payload).slice(0, 200));
          if (payload.id === 0 && payload.result && !initReceived) {
            initReceived = true;
            addLog("success", `Initialize response received. Protocol version: ${payload.result.protocolVersion || "unknown"}`);
            ws.send(JSON.stringify({ jsonrpc: "2.0", method: "notifications/initialized" }));
            ws.send(JSON.stringify({ jsonrpc: "2.0", id: 1, method: "tools/list" }));
            addLog("info", "Listing available tools...");
          }
          if (payload.id === 1 && payload.result && !toolsReceived) {
            toolsReceived = true;
            const rawTools = payload.result.tools || [];
            const mappedTools: Tool[] = rawTools.map((t: any) => ({
              name: t.name,
              description: t.description || "",
              params: t.inputSchema && t.inputSchema.properties
                ? Object.entries(t.inputSchema.properties).map(([name, prop]: [string, any]) => ({
                    name,
                    type: prop.type || "string",
                    required: (t.inputSchema.required || []).includes(name),
                    description: prop.description || "",
                  }))
                : [],
            }));
            setConfig((c) => ({
              ...c,
              status: "connected",
              message: `Connected. ${mappedTools.length} tools discovered.`,
              tools: mappedTools,
            }));
            addLog("success", `Server ready. ${mappedTools.length} tools available.`);
          }
          if (payload.id && payload.id >= 2 && payload.result) {
            const toolName = (ws as any).__pendingToolCall || Object.keys(toolResults).find((k) => toolResults[k]?.status === "loading") || "tool";
            (ws as any).__pendingToolCall = null;
            setToolResults((prev) => ({
              ...prev,
              [toolName]: { status: "success", output: JSON.stringify(payload.result, null, 2) },
            }));
            addLog("success", `Tool ${toolName} responded`);
          }
        }
      } catch (e) {
        addLog("error", `Failed to parse message: ${String(e)}`);
      }
    };

    ws.onerror = () => {
      addLog("error", "WebSocket error. Is the proxy running?");
      setConfig((c) => ({ ...c, status: "error", message: "Connection failed. Ensure the MCP Workbench server is running." }));
    };

    ws.onclose = () => {
      if (!initReceived) {
        addLog("warn", "Connection closed before initialization completed.");
      } else {
        addLog("info", "Connection closed.");
      }
      setConfig((c) => (c.status === "connected" ? { ...c, status: "idle", message: "", tools: [] } : c));
      wsRef.current = null;
    };
  };

  const handleDisconnect = () => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    setConfig((c) => ({ ...c, status: "idle", message: "", tools: [] }));
    setToolResults({});
    addLog("info", "Connection closed.");
  };

  const handlePreset = (idx: number) => {
    setSelectedPreset(idx);
    setCommandInput(PRESETS[idx].command);
    setArgsInput(PRESETS[idx].args);
    setShowPresets(false);
  };

  const tabs = [
    { icon: <Terminal size={16} />, label: "Console" },
    { icon: <Server size={16} />, label: "Tools" },
    { icon: <Activity size={16} />, label: "Raw" },
  ];

  const navItems = [
    { href: "/dashboard", label: "Overview", icon: <Activity size={18} /> },
    { href: "/dashboard/subscription", label: "Subscription", icon: <CreditCard size={18} /> },
    { href: "/dashboard/api-keys", label: "API Keys", icon: <Key size={18} /> },
    { href: "/dashboard/settings", label: "Settings", icon: <Settings size={18} /> },
  ];

  return (
    <div className="min-h-screen bg-background text-foreground">
      {/* ─── Navbar ─────────────────────────────────────── */}
      <nav className="border-b border-border">
        <div className="max-w-7xl mx-auto px-4 h-14 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Zap className="text-primary" size={22} />
            <span className="font-bold text-lg tracking-tight">MCP Workbench</span>
          </div>
          <div className="hidden md:flex items-center gap-6 text-sm text-muted">
            <a href="/dashboard" className="text-foreground hover:text-foreground transition-colors">Dashboard</a>
            <a href="/" className="hover:text-foreground transition-colors">Home</a>
            <a href="https://github.com/s63jp/mcp-workbench" className="hover:text-foreground transition-colors">GitHub</a>
          </div>
          <div className="flex items-center gap-3">
            <button className="md:hidden text-muted" onClick={() => setShowMobileMenu(!showMobileMenu)}>
              <Layers size={20} />
            </button>
            <div className="hidden md:flex items-center gap-3">
              <span className="text-sm text-muted">{userTier} Plan</span>
              <div className="w-8 h-8 rounded-full bg-primary/20 flex items-center justify-center text-primary font-semibold text-sm">
                {userEmail ? userEmail.charAt(0).toUpperCase() : "U"}
              </div>
            </div>
          </div>
        </div>
      </nav>

      {/* ─── Mobile Menu ────────────────────────────────── */}
      {showMobileMenu && (
        <div className="md:hidden border-b border-border bg-surface">
          <div className="px-4 py-3 space-y-2">
            {navItems.map((item) => (
              <a
                key={item.href}
                href={item.href}
                className="flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-surface-hover transition-colors text-sm"
                onClick={() => setShowMobileMenu(false)}
              >
                {item.icon}
                {item.label}
              </a>
            ))}
          </div>
        </div>
      )}

      {/* ─── Dashboard Layout ───────────────────────────── */}
      <div className="max-w-7xl mx-auto px-4 py-6">
        <div className="flex flex-col md:flex-row gap-6">
          {/* Sidebar Navigation */}
          <aside className="hidden md:block w-56 shrink-0">
            <nav className="sticky top-6 space-y-1">
              {navItems.map((item) => (
                <a
                  key={item.href}
                  href={item.href}
                  className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors ${
                    item.href === "/dashboard"
                      ? "bg-primary/10 text-primary border border-primary/20"
                      : "text-muted hover:text-foreground hover:bg-surface-hover"
                  }`}
                >
                  {item.icon}
                  {item.label}
                </a>
              ))}
              <div className="pt-4 mt-4 border-t border-border">
                <a href="/" className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-muted hover:text-danger transition-colors">
                  <LogOut size={18} />
                  Sign Out
                </a>
              </div>
            </nav>
          </aside>

          {/* Main Content */}
          <main className="flex-1 min-w-0">
            {/* Header */}
            <div className="mb-6">
              <h1 className="text-2xl font-bold mb-1">Dashboard</h1>
              <p className="text-sm text-muted">Welcome back! Here&apos;s your MCP Workbench overview.</p>
            </div>

            {/* Usage Stats Grid */}
            <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
              {usageStats.map((stat) => (
                <div key={stat.label} className="p-4 rounded-xl border border-border bg-surface">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs text-muted">{stat.label}</span>
                    {stat.trend && (
                      <span className={stat.trend === "up" ? "text-success" : "text-danger"}>
                        {stat.trend === "up" ? <ArrowUpRight size={14} /> : <ArrowDownRight size={14} />}
                      </span>
                    )}
                  </div>
                  <div className="flex items-baseline gap-1 mb-2">
                    <span className="text-2xl font-bold">{stat.value}</span>
                    <span className="text-xs text-muted">/ {stat.limit} {stat.unit}</span>
                  </div>
                  <div className="w-full bg-border rounded-full h-1.5 overflow-hidden">
                    <div
                      className={`h-full rounded-full transition-all ${stat.percentage > 80 ? "bg-warning" : stat.percentage > 50 ? "bg-primary" : "bg-success"}`}
                      style={{ width: `${Math.min(stat.percentage, 100)}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>

            {/* Current Plan Banner */}
            <div className="p-4 rounded-xl border border-primary/30 bg-gradient-to-r from-primary/10 to-transparent mb-6">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-lg bg-primary/20">
                    <Crown size={20} className="text-primary" />
                  </div>
                  <div>
                    <h3 className="font-semibold">{userTier} Plan</h3>
                    <p className="text-xs text-muted">{userTier === "Free" ? "Free forever. Upgrade when you need more." : "Active subscription"}</p>
                  </div>
                </div>
                <a href="/dashboard/subscription" className="text-sm text-primary hover:underline flex items-center gap-1">
                  Manage Plan <ChevronRight size={14} />
                </a>
              </div>
            </div>

            {/* Quick Connect Section */}
            <div className="rounded-2xl border border-border bg-surface overflow-hidden shadow-lg mb-6">
              {/* Header */}
              <div className="flex items-center justify-between px-5 py-3 border-b border-border bg-surface-hover">
                <div className="flex items-center gap-3">
                  <div className="w-3 h-3 rounded-full bg-danger" />
                  <div className="w-3 h-3 rounded-full bg-warning" />
                  <div className="w-3 h-3 rounded-full bg-success" />
                  <span className="ml-2 text-sm font-mono text-muted">Quick Connect</span>
                </div>
                <div className="flex items-center gap-2">
                  {config.status === "connected" ? (
                    <>
                      <span className="flex items-center gap-1.5 text-xs text-success">
                        <span className="w-1.5 h-1.5 rounded-full bg-success animate-pulse" /> Connected
                      </span>
                      <button onClick={handleDisconnect} className="text-xs px-3 py-1 rounded-md bg-danger/10 text-danger hover:bg-danger/20 transition-colors flex items-center gap-1">
                        <Square size={12} /> Disconnect
                      </button>
                    </>
                  ) : config.status === "connecting" ? (
                    <span className="flex items-center gap-1.5 text-xs text-warning">
                      <span className="w-3 h-3 border-2 border-warning border-t-transparent rounded-full animate-spin" /> Connecting...
                    </span>
                  ) : (
                    <button onClick={handleConnect} className="text-xs px-3 py-1.5 rounded-md bg-primary text-white hover:bg-primary-hover transition-colors flex items-center gap-1.5">
                      <Play size={12} fill="currentColor" /> Connect
                    </button>
                  )}
                </div>
              </div>

              {/* Connection Form */}
              <div className="p-5 border-b border-border">
                <div className="flex items-end gap-3 mb-3">
                  <div className="relative">
                    <button onClick={() => setShowPresets(!showPresets)} className="flex items-center gap-2 text-sm px-3 py-2 rounded-lg border border-border hover:bg-surface-hover transition-colors bg-background">
                      {PRESETS[selectedPreset].label}
                      <ChevronDown size={14} className={`transition-transform ${showPresets ? "rotate-180" : ""}`} />
                    </button>
                    {showPresets && (
                      <div className="absolute top-full left-0 mt-1 w-56 rounded-lg border border-border bg-surface shadow-xl z-10">
                        {PRESETS.map((p, i) => (
                          <button key={i} onClick={() => handlePreset(i)} className={`w-full text-left text-sm px-3 py-2 hover:bg-surface-hover first:rounded-t-lg last:rounded-b-lg ${i === selectedPreset ? "text-primary" : ""}`}>
                            {p.label}
                          </button>
                        ))}
                      </div>
                    )}
                  </div>
                  <div className="flex-1">
                    <label className="block text-xs text-muted mb-1 font-mono">Command</label>
                    <input value={commandInput} onChange={(e) => setCommandInput(e.target.value)} className="w-full bg-background border border-border rounded-lg px-3 py-2 text-sm font-mono focus:outline-none focus:border-primary transition-colors" placeholder="npx" />
                  </div>
                  <div className="flex-[2]">
                    <label className="block text-xs text-muted mb-1 font-mono">Arguments</label>
                    <input value={argsInput} onChange={(e) => setArgsInput(e.target.value)} className="w-full bg-background border border-border rounded-lg px-3 py-2 text-sm font-mono focus:outline-none focus:border-primary transition-colors" placeholder="-y @modelcontextprotocol/server-filesystem /tmp" />
                  </div>
                </div>
                {config.message && (
                  <div className={`text-xs px-3 py-2 rounded-lg font-mono ${config.status === "error" ? "bg-danger/10 text-danger border border-danger/20" : config.status === "connected" ? "bg-success/10 text-success border border-success/20" : "bg-warning/10 text-warning border border-warning/20"}`}>
                    &gt; {config.message}
                  </div>
                )}
              </div>

              {/* Tabs + Content */}
              <div className="flex flex-col sm:flex-row">
                <div className="w-full sm:w-44 border-r border-border flex flex-row sm:flex-col overflow-x-auto">
                  {tabs.map((t, i) => (
                    <button key={i} onClick={() => setActiveTab(i)} className={`flex items-center gap-2 px-4 py-2.5 text-sm transition-colors text-left ${activeTab === i ? "bg-primary/10 text-primary border-l-2 border-primary" : "text-muted hover:text-foreground hover:bg-surface-hover border-l-2 border-transparent"}`}>
                      {t.icon} {t.label}
                    </button>
                  ))}
                </div>

                <div className="flex-1 min-h-[300px] max-h-[400px] overflow-y-auto">
                  {activeTab === 0 && (
                    <div className="p-4 font-mono text-xs space-y-1">
                      {logs.map((l, i) => (
                        <div key={i} className="flex gap-3">
                          <span className="text-muted shrink-0 w-[52px]">{l.time.split(" ")[0]}</span>
                          <span className={`shrink-0 w-16 font-bold ${l.level === "success" ? "text-success" : l.level === "error" ? "text-danger" : l.level === "warn" ? "text-warning" : "text-accent"}`}>{l.level.toUpperCase()}</span>
                          <span className="text-foreground/80">{l.message}</span>
                        </div>
                      ))}
                      <div className="animate-pulse text-muted">▌</div>
                    </div>
                  )}

                  {activeTab === 1 && (
                    <div className="p-4 space-y-2">
                      {config.tools.length === 0 ? (
                        <p className="text-sm text-muted text-center py-10">No tools discovered. Connect to a server first.</p>
                      ) : (
                        config.tools.map((tool) => (
                          <div key={tool.name} className="border border-border rounded-lg overflow-hidden">
                            <button onClick={() => setExpandedTool(expandedTool === tool.name ? null : tool.name)} className="w-full flex items-center justify-between px-4 py-3 hover:bg-surface-hover transition-colors">
                              <div className="flex items-center gap-3">
                                <GitBranch size={16} className="text-primary" />
                                <span className="font-mono text-sm font-semibold">{tool.name}</span>
                                <span className="text-xs text-muted">{tool.params.length} param{tool.params.length !== 1 ? "s" : ""}</span>
                              </div>
                              {expandedTool === tool.name ? <ChevronUp size={16} className="text-muted" /> : <ChevronDown size={16} className="text-muted" />}
                            </button>
                            {expandedTool === tool.name && (
                              <div className="px-4 py-3 border-t border-border bg-background/50">
                                <p className="text-sm text-muted mb-3">{tool.description}</p>
                                <div className="space-y-3 mb-3">
                                  {tool.params.map((p) => (
                                    <div key={p.name}>
                                      <div className="flex items-center gap-2 mb-1">
                                        <span className="font-mono text-xs text-primary">{p.name}</span>
                                        <span className="text-[10px] px-1.5 py-0.5 rounded bg-border text-muted">{p.type}</span>
                                        {p.required && <span className="text-[10px] px-1.5 py-0.5 rounded bg-danger/10 text-danger">required</span>}
                                      </div>
                                      <p className="text-xs text-muted mb-1">{p.description}</p>
                                      <input
                                        type="text"
                                        placeholder={p.type === "string" ? `"value"` : p.type === "number" ? "0" : "{}"}
                                        value={paramValues[tool.name]?.[p.name] || ""}
                                        onChange={(e) => setParamValues((prev) => ({ ...prev, [tool.name]: { ...(prev[tool.name] || {}), [p.name]: e.target.value } }))}
                                        className="w-full bg-background border border-border rounded-md px-2 py-1 text-xs font-mono focus:outline-none focus:border-primary transition-colors"
                                      />
                                    </div>
                                  ))}
                                </div>
                                <button
                                  onClick={() => {
                                    setToolResults((prev) => ({ ...prev, [tool.name]: { status: "loading", output: "" } }));
                                    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
                                      setToolResults((prev) => ({ ...prev, [tool.name]: { status: "error", output: "WebSocket not connected" } }));
                                      return;
                                    }
                                    const callId = Date.now();
                                    const params = paramValues[tool.name] || {};
                                    const callPayload = {
                                      jsonrpc: "2.0", id: callId,
                                      method: "tools/call",
                                      params: { name: tool.name, arguments: params },
                                    };
                                    (wsRef.current as any).__pendingToolCall = tool.name;
                                    wsRef.current.send(JSON.stringify(callPayload));
                                    addLog("info", `Calling tool ${tool.name}...`);
                                  }}
                                  className="text-xs px-3 py-1.5 rounded-md bg-primary text-white hover:bg-primary-hover transition-colors flex items-center gap-1.5 mb-3"
                                  disabled={toolResults[tool.name]?.status === "loading"}
                                >
                                  <Play size={10} fill="currentColor" /> {toolResults[tool.name]?.status === "loading" ? "Calling..." : "Call Tool"}
                                </button>
                                {toolResults[tool.name]?.status === "success" && (
                                  <pre className="text-[10px] bg-background border border-border rounded-md p-2 font-mono text-success overflow-x-auto">{toolResults[tool.name].output}</pre>
                                )}
                                {toolResults[tool.name]?.status === "error" && (
                                  <pre className="text-[10px] bg-background border border-border rounded-md p-2 font-mono text-danger overflow-x-auto">{toolResults[tool.name].output}</pre>
                                )}
                              </div>
                            )}
                          </div>
                        ))
                      )}
                    </div>
                  )}

                  {activeTab === 2 && (
                    <div className="p-4 font-mono text-xs h-80 overflow-y-auto">
                      {config.status === "connected" ? (
                        logs.map((log, i) => (
                          <div key={i} className={`mb-1 ${log.level === "error" ? "text-danger" : log.level === "success" ? "text-success" : "text-muted"}`}>
                            <span className="opacity-50">[{log.time}]</span> {log.message.slice(0, 300)}
                          </div>
                        ))
                      ) : (
                        <p className="text-muted">Connect to a server to view raw JSON-RPC traffic.</p>
                      )}
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Recent Activity */}
            <div className="rounded-xl border border-border bg-surface p-4">
              <h3 className="font-semibold mb-3 flex items-center gap-2">
                <Clock size={18} className="text-muted" />
                Recent Activity
              </h3>
              <div className="space-y-2">
                {recentActivity.length === 0 ? (
                  <p className="text-sm text-muted py-4 text-center">
                    No sessions yet. Connect to an MCP server above and your activity will appear here.
                  </p>
                ) : (
                  recentActivity.map((activity) => (
                    <div key={activity.id} className="flex items-center justify-between p-3 rounded-lg bg-background/50 hover:bg-surface-hover transition-colors">
                      <div className="flex items-center gap-3">
                        <span className={`w-2 h-2 rounded-full ${activity.status === "success" ? "bg-success" : activity.status === "error" ? "bg-danger" : "bg-warning"}`} />
                        <div>
                          <p className="text-sm font-medium">{activity.action}</p>
                          <p className="text-xs text-muted truncate max-w-[200px] sm:max-w-xs">{activity.server}</p>
                        </div>
                      </div>
                      <span className="text-xs text-muted">{activity.time}</span>
                    </div>
                  ))
                )}
              </div>
            </div>
          </main>
        </div>
      </div>
    </div>
  );
}
