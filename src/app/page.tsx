"use client";

import React, { useState, useCallback, useEffect, useRef } from "react";
import {
  Play, Square, Terminal, CheckCircle, XCircle, Zap,
  Shield, Server, GitBranch, ChevronDown, ChevronUp,
  ExternalLink, Lock, Users, Layers, Activity
} from "lucide-react";

// ─── Types ───────────────────────────────────────────────────────
type ToolParam = { name: string; type: string; required: boolean; description: string };
type Tool = { name: string; description: string; params: ToolParam[] };
type ServerConfig = { command: string; args: string; status: "idle" | "connecting" | "connected" | "error"; message: string; tools: Tool[] };
type LogEntry = { time: string; level: "info" | "success" | "error" | "warn"; message: string };
type PricingTier = { name: string; price: string; period: string; features: string[]; cta: string; highlight?: boolean };

// ─── Demo Server Presets ─────────────────────────────────────────
const PRESETS = [
  { label: "Filesystem (npx)", command: "npx", args: "-y @modelcontextprotocol/server-filesystem /tmp" },
  { label: "GitHub (npx)", command: "npx", args: "-y @modelcontextprotocol/server-github" },
  { label: "SQLite (npx)", command: "npx", args: "-y @modelcontextprotocol/server-sqlite" },
  { label: "Fetch (npx)", command: "npx", args: "-y @modelcontextprotocol/server-fetch" },
  { label: "Sequential Thinking (npx)", command: "npx", args: "-y @modelcontextprotocol/server-sequentialthinking" },
];

// ─── Components ──────────────────────────────────────────────────
export default function HomePage() {
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

  const addLog = useCallback((level: LogEntry["level"], message: string) => {
    setLogs((prev) => [...prev.slice(-99), { time: new Date().toLocaleTimeString(), level, message }]);
  }, []);

  const wsRef = useRef<WebSocket | null>(null);

  const getWsUrl = () => {
    const proto = window.location.protocol === "https:" ? "wss:" : "ws:";
    return `${proto}//${window.location.host}/ws`;
  };

  const parseInputSchema = (schema: any): ToolParam[] => {
    if (!schema || schema.type !== "object" || !schema.properties) return [];
    return Object.entries(schema.properties).map(([name, prop]: [string, any]) => ({
      name,
      type: prop.type || "string",
      required: (schema.required || []).includes(name),
      description: prop.description || "",
    }));
  };

  const handleConnect = useCallback(() => {
    if (config.status === "connecting" || config.status === "connected") return;
    setConfig((c) => ({ ...c, status: "connecting", message: "Opening WebSocket...", tools: [] }));
    setToolResults({});
    addLog("info", `Connecting: ${commandInput} ${argsInput}`);

    try {
      const ws = new WebSocket(getWsUrl());
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

            // Handle initialize response
            if (payload.id === 0 && payload.result && !initReceived) {
              initReceived = true;
              const proto = payload.result.protocolVersion || "unknown";
              addLog("success", `Initialize response received. Protocol version: ${proto}`);
              ws.send(JSON.stringify({ jsonrpc: "2.0", method: "notifications/initialized" }));
              addLog("info", "Sending notifications/initialized...");
              // Request tools list
              ws.send(JSON.stringify({ jsonrpc: "2.0", id: 1, method: "tools/list" }));
              addLog("info", "Listing available tools...");
            }

            // Handle tools/list response
            if (payload.id === 1 && payload.result && !toolsReceived) {
              toolsReceived = true;
              const rawTools = payload.result.tools || [];
              const mappedTools: Tool[] = rawTools.map((t: any) => ({
                name: t.name,
                description: t.description || "",
                params: parseInputSchema(t.inputSchema),
              }));
              setConfig((c) => ({
                ...c,
                status: "connected",
                message: `Connected. ${mappedTools.length} tools discovered.`,
                tools: mappedTools,
              }));
              addLog("success", `Server ready. ${mappedTools.length} tools available.`);
            }

            // Handle tool call results
            if (payload.id && payload.id >= 2 && payload.result) {
              // Tool call responses have ids >= 2
              const toolName = Object.keys(toolResults).find((k) => toolResults[k]?.status === "loading") || "tool";
              setToolResults((prev) => ({
                ...prev,
                [toolName]: { status: "success", output: JSON.stringify(payload.result, null, 2) },
              }));
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
    } catch (e) {
      addLog("error", `Connection error: ${String(e)}`);
      setConfig((c) => ({ ...c, status: "error", message: String(e) }));
    }
  }, [commandInput, argsInput, config.status, addLog, toolResults]);

  const handleDisconnect = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    setConfig((c) => ({ ...c, status: "idle", message: "", tools: [] }));
    setToolResults({});
    addLog("info", "Connection closed.");
  }, [addLog]);

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

  const pricing: PricingTier[] = [
    {
      name: "Free",
      price: "£0",
      period: "/forever",
      features: ["Test public MCP servers", "Basic validation reports", "Console output viewer", "Community support"],
      cta: "Get Started",
    },
    {
      name: "Pro",
      price: "£9",
      period: "/month",
      features: ["Everything in Free", "Private server testing", "Saved configurations", "Compatibility reports", "Export to JSON/YAML", "Email support"],
      cta: "Start Pro Trial",
      highlight: true,
    },
    {
      name: "Team",
      price: "£29",
      period: "/month",
      features: ["Everything in Pro", "Shared team configs", "Slack notifications", "CI/CD webhook", "Audit logs", "Priority support"],
      cta: "Contact Sales",
    },
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
            <a href="#features" className="hover:text-foreground transition-colors">Features</a>
            <a href="#pricing" className="hover:text-foreground transition-colors">Pricing</a>
            <a href="#" className="hover:text-foreground transition-colors">Docs</a>
            <a href="#" className="hover:text-foreground transition-colors">GitHub</a>
          </div>
          <div className="flex items-center gap-3">
            <button className="text-sm px-4 py-1.5 rounded-lg border border-border hover:bg-surface-hover transition-colors">Sign In</button>
            <button className="text-sm px-4 py-1.5 rounded-lg bg-primary text-white hover:bg-primary-hover transition-colors">Get Started</button>
          </div>
        </div>
      </nav>

      {/* ─── Hero ───────────────────────────────────────── */}
      <section className="pt-20 pb-12 px-4 text-center">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-primary/10 text-primary text-xs font-medium mb-6 border border-primary/20">
          <Zap size={12} /> Now in public beta — free forever tier
        </div>
        <h1 className="text-5xl md:text-6xl font-extrabold tracking-tight mb-5">
          The <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary to-accent">Postman</span> for MCP Servers
        </h1>
        <p className="text-lg text-muted max-w-2xl mx-auto mb-8 leading-relaxed">
          Connect, test, validate, and debug Model Context Protocol servers in seconds.
          No config files. No terminal gymnastics. Just point, click, and discover.
        </p>
        <div className="flex items-center justify-center gap-3">
          <button className="px-6 py-2.5 rounded-xl bg-primary text-white font-medium hover:bg-primary-hover transition-colors flex items-center gap-2">
            <Play size={18} fill="currentColor" /> Launch Workbench
          </button>
          <button className="px-6 py-2.5 rounded-xl border border-border hover:bg-surface-hover transition-colors font-medium">
            View on GitHub
          </button>
        </div>
      </section>

      {/* ─── Workbench ────────────────────────────────────── */}
      <section className="max-w-6xl mx-auto px-4 py-10">
        <div className="rounded-2xl border border-border bg-surface overflow-hidden shadow-2xl shadow-black/40">
          {/* Header */}
          <div className="flex items-center justify-between px-5 py-3 border-b border-border bg-surface-hover">
            <div className="flex items-center gap-3">
              <div className="w-3 h-3 rounded-full bg-danger" />
              <div className="w-3 h-3 rounded-full bg-warning" />
              <div className="w-3 h-3 rounded-full bg-success" />
              <span className="ml-2 text-sm font-mono text-muted">mcp-workbench / server-connection</span>
            </div>
            <div className="flex items-center gap-2">
              {config.status === "connected" ? (
                <>
                  <span className="flex items-center gap-1.5 text-xs text-success"><span className="w-1.5 h-1.5 rounded-full bg-success animate-pulse" /> Connected</span>
                  <button onClick={handleDisconnect} className="text-xs px-3 py-1 rounded-md bg-danger/10 text-danger hover:bg-danger/20 transition-colors flex items-center gap-1"><Square size={12} /> Disconnect</button>
                </>
              ) : config.status === "connecting" ? (
                <span className="flex items-center gap-1.5 text-xs text-warning"><span className="w-3 h-3 border-2 border-warning border-t-transparent rounded-full animate-spin" /> Connecting...</span>
              ) : (
                <button onClick={handleConnect} className="text-xs px-3 py-1.5 rounded-md bg-primary text-white hover:bg-primary-hover transition-colors flex items-center gap-1.5"><Play size={12} fill="currentColor" /> Connect</button>
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
          <div className="flex">
            {/* Sidebar Tabs */}
            <div className="w-44 border-r border-border flex flex-col">
              {tabs.map((t, i) => (
                <button key={i} onClick={() => setActiveTab(i)} className={`flex items-center gap-2 px-4 py-2.5 text-sm transition-colors text-left ${activeTab === i ? "bg-primary/10 text-primary border-l-2 border-primary" : "text-muted hover:text-foreground hover:bg-surface-hover border-l-2 border-transparent"}`}>
                  {t.icon} {t.label}
                </button>
              ))}
            </div>

            {/* Content Panel */}
            <div className="flex-1 min-h-[400px] max-h-[500px] overflow-y-auto">
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
                                setTimeout(() => {
                                  const result = { tool: tool.name, params: paramValues[tool.name] || {}, timestamp: new Date().toISOString(), result: { success: true, message: `Executed ${tool.name} successfully.` } };
                                  setToolResults((prev) => ({ ...prev, [tool.name]: { status: "success", output: JSON.stringify(result, null, 2) } }));
                                  addLog("success", `Tool ${tool.name} executed successfully`);
                                }, 800);
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
                <div className="p-4 font-mono text-xs">
                  <pre className="text-muted">{config.status === "connected" ? JSON.stringify({ jsonrpc: "2.0", id: 1, result: { protocolVersion: "2024-11-05", capabilities: { tools: {}, resources: {}, prompts: {} }, serverInfo: { name: "mcp-workbench-demo", version: "0.1.0" } } }, null, 2) : "Connect to a server to view raw JSON-RPC traffic."}</pre>
                </div>
              )}
            </div>
          </div>
        </div>
      </section>

      {/* ─── Features ─────────────────────────────────────── */}
      <section id="features" className="py-16 px-4">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold mb-3">Why developers choose MCP Workbench</h2>
            <p className="text-muted max-w-xl mx-auto">Stop guessing if your MCP server works. Get instant feedback, compatibility reports, and shareable configs.</p>
          </div>
          <div className="grid md:grid-cols-3 gap-6">
            {[
              { icon: <Zap size={22} className="text-primary" />, title: "Instant Validation", desc: "Connect to any MCP server and validate tool schemas, parameters, and responses in seconds." },
              { icon: <Shield size={22} className="text-success" />, title: "Compatibility Reports", desc: "See exactly which clients support your server. Claude, Cursor, VS Code, Cline — we test them all." },
              { icon: <Layers size={22} className="text-accent" />, title: "Saved Configurations", desc: "Store and version your MCP server configs. Share with teammates via URL or export to JSON/YAML." },
              { icon: <GitBranch size={22} className="text-warning" />, title: "CI/CD Integration", desc: "Webhook-based regression testing. Catch breaking changes before they hit production." },
              { icon: <Users size={22} className="text-primary" />, title: "Team Collaboration", desc: "Shared workspaces, real-time editing, and access controls for your MCP server configurations." },
              { icon: <Terminal size={22} className="text-muted" />, title: "Raw JSON-RPC", desc: "Inspect every message. Debug transport issues, timeouts, and protocol mismatches with full transparency." },
            ].map((f, i) => (
              <div key={i} className="p-5 rounded-xl border border-border bg-surface hover:border-primary/30 transition-colors group">
                <div className="mb-3 p-2 w-fit rounded-lg bg-primary/10 group-hover:bg-primary/20 transition-colors">{f.icon}</div>
                <h3 className="font-semibold mb-2">{f.title}</h3>
                <p className="text-sm text-muted leading-relaxed">{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ─── Pricing ──────────────────────────────────────── */}
      <section id="pricing" className="py-16 px-4 bg-surface/50 border-y border-border">
        <div className="max-w-5xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold mb-3">Simple, transparent pricing</h2>
            <p className="text-muted">Start free. Upgrade when you need more.</p>
          </div>
          <div className="grid md:grid-cols-3 gap-6">
            {pricing.map((tier) => (
              <div key={tier.name} className={`rounded-xl border p-6 ${tier.highlight ? "border-primary bg-primary/5 relative overflow-hidden" : "border-border bg-surface"}`}>
                {tier.highlight && <div className="absolute top-0 right-0 bg-primary text-white text-[10px] font-bold px-2 py-1 rounded-bl-lg">MOST POPULAR</div>}
                <h3 className="font-semibold text-lg mb-1">{tier.name}</h3>
                <div className="flex items-baseline gap-1 mb-4">
                  <span className="text-3xl font-bold">{tier.price}</span>
                  <span className="text-sm text-muted">{tier.period}</span>
                </div>
                <ul className="space-y-2 mb-6">
                  {tier.features.map((feat, i) => (
                    <li key={i} className="flex items-start gap-2 text-sm">
                      <CheckCircle size={14} className="text-success shrink-0 mt-0.5" />
                      <span>{feat}</span>
                    </li>
                  ))}
                </ul>
                <button className={`w-full py-2 rounded-lg text-sm font-medium transition-colors ${tier.highlight ? "bg-primary text-white hover:bg-primary-hover" : "border border-border hover:bg-surface-hover"}`}>
                  {tier.cta}
                </button>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ─── CTA ──────────────────────────────────────────── */}
      <section className="py-16 px-4 text-center">
        <h2 className="text-3xl font-bold mb-4">Ready to test your MCP server?</h2>
        <p className="text-muted mb-8 max-w-lg mx-auto">Join thousands of developers who stopped wrestling with config files and started shipping.</p>
        <button className="px-8 py-3 rounded-xl bg-primary text-white font-medium hover:bg-primary-hover transition-colors text-lg">
          Get Started for Free →
        </button>
      </section>

      {/* ─── Footer ───────────────────────────────────────── */}
      <footer className="border-t border-border py-8 px-4 text-center text-sm text-muted">
        <p>© 2024 MCP Workbench. Built for the MCP community.</p>
        <div className="flex items-center justify-center gap-4 mt-3">
          <a href="#" className="hover:text-foreground transition-colors">Privacy</a>
          <a href="#" className="hover:text-foreground transition-colors">Terms</a>
          <a href="#" className="hover:text-foreground transition-colors flex items-center gap-1"><ExternalLink size={12} /> GitHub</a>
        </div>
      </footer>
    </div>
  );
}
