"use client";

import React, { useState, useEffect } from "react";
import {
  Zap, Key, Plus, Copy, Trash2, Shield,
  CheckCircle, AlertTriangle, ChevronRight, Activity, X
} from "lucide-react";
// ─── Types ───────────────────────────────────────────────────────
type ApiKey = {
  id: number;
  name: string;
  key_prefix: string;
  created_at: string;
  last_used_at: string | null;
  is_active: boolean;
};

const navItems = [
  { href: "/dashboard", label: "Overview", icon: <Activity size={18} /> },
  { href: "/dashboard/subscription", label: "Subscription", icon: <Shield size={18} /> },
  { href: "/dashboard/api-keys", label: "API Keys", icon: <Key size={18} /> },
  { href: "/dashboard/settings", label: "Settings", icon: <Zap size={18} /> },
];

function fmtDate(iso: string | null): string {
  if (!iso) return "Never";
  const d = new Date(iso);
  if (isNaN(d.getTime())) return "Never";
  return d.toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" });
}

// ─── Components ──────────────────────────────────────────────────
export default function ApiKeysPage() {
  const [apiKeys, setApiKeys] = useState<ApiKey[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newKeyName, setNewKeyName] = useState("");
  const [generatedKey, setGeneratedKey] = useState("");
  const [copiedId, setCopiedId] = useState<number | null>(null);
  const [error, setError] = useState("");
  const [showMobileMenu, setShowMobileMenu] = useState(false);
  const [userEmail, setUserEmail] = useState("");
  const [userTier, setUserTier] = useState("Free");

  const token = typeof window !== "undefined" ? localStorage.getItem("mcpwb_token") : null;
  const authHeaders = { Authorization: `Bearer ${token}` };

  useEffect(() => {
    if (!token) {
      window.location.href = "/login";
      return;
    }
    const userRaw = localStorage.getItem("mcpwb_user");
    if (userRaw) {
      try {
        setUserEmail(JSON.parse(userRaw).email || "");
      } catch {}
    }
    fetch("/api/subscriptions", { headers: authHeaders })
      .then((r) => (r.ok ? r.json() : null))
      .then((data) => {
        if (data && data.subscription) {
          const t = data.subscription.tier;
          setUserTier(t.charAt(0).toUpperCase() + t.slice(1));
        }
      })
      .catch(() => {});
    loadKeys();
  }, []);

  const loadKeys = () => {
    setLoading(true);
    fetch("/api/api-keys", { headers: authHeaders })
      .then((r) => (r.ok ? r.json() : null))
      .then((data) => {
        setApiKeys(data && Array.isArray(data.keys) ? data.keys : []);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  };

  const handleCreateKey = async () => {
    if (!newKeyName.trim()) return;
    setError("");
    try {
      const res = await fetch("/api/api-keys", {
        method: "POST",
        headers: { "Content-Type": "application/json", ...authHeaders },
        body: JSON.stringify({ name: newKeyName.trim() }),
      });
      const data = await res.json();
      if (!res.ok) {
        setError(data.error || "Failed to create key");
        return;
      }
      setGeneratedKey(data.key || "");
      setShowCreateModal(false);
      setNewKeyName("");
      loadKeys();
    } catch {
      setError("Network error. Please try again.");
    }
  };

  const handleRevokeKey = async (id: number) => {
    if (!confirm("Revoke this API key? It will stop working immediately.")) return;
    try {
      const res = await fetch(`/api/api-keys/${id}`, {
        method: "DELETE",
        headers: authHeaders,
      });
      if (res.ok) loadKeys();
    } catch {}
  };

  const handleCopy = async (text: string, id: number) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopiedId(id);
      setTimeout(() => setCopiedId(null), 2000);
    } catch {}
  };

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
            <a href="/dashboard" className="hover:text-foreground transition-colors">Dashboard</a>
            <a href="/" className="hover:text-foreground transition-colors">Home</a>
            <a href="https://github.com/s63jp/mcp-workbench" className="hover:text-foreground transition-colors">GitHub</a>
          </div>
          <div className="flex items-center gap-3">
            <button className="md:hidden text-muted" onClick={() => setShowMobileMenu(!showMobileMenu)}>
              <Shield size={20} />
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

      {/* ─── Main Content ───────────────────────────────── */}
      <div className="max-w-5xl mx-auto px-4 py-6">
        {/* Header */}
        <div className="mb-6">
          <div className="flex items-center gap-2 text-sm text-muted mb-2">
            <a href="/dashboard" className="hover:text-foreground">Dashboard</a>
            <ChevronRight size={14} />
            <span>API Keys</span>
          </div>
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <div>
              <h1 className="text-2xl font-bold mb-1">API Keys</h1>
              <p className="text-sm text-muted">Manage API keys for programmatic access to MCP Workbench.</p>
            </div>
            <button
              onClick={() => setShowCreateModal(true)}
              className="px-4 py-2 rounded-lg bg-primary text-white hover:bg-primary-hover transition-colors flex items-center gap-2 font-medium"
            >
              <Plus size={18} /> Create API Key
            </button>
          </div>
        </div>

        {/* Info Banner */}
        <div className="p-4 rounded-xl border border-warning/30 bg-warning/10 mb-6">
          <div className="flex items-start gap-3">
            <AlertTriangle size={20} className="text-warning shrink-0 mt-0.5" />
            <div>
              <h3 className="font-semibold text-warning mb-1">Keep your API keys secure</h3>
              <p className="text-sm text-muted">
                API keys have full access to your account. Never share them or commit them to version control.
                Keys are only shown once after creation — make sure to copy them immediately.
              </p>
            </div>
          </div>
        </div>

        {/* API Keys List */}
        <div className="rounded-xl border border-border overflow-hidden mb-6">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border bg-surface">
                  <th className="text-left px-4 py-3 font-semibold text-muted">Name</th>
                  <th className="text-left px-4 py-3 font-semibold text-muted">API Key</th>
                  <th className="text-left px-4 py-3 font-semibold text-muted">Created</th>
                  <th className="text-left px-4 py-3 font-semibold text-muted">Last Used</th>
                  <th className="text-left px-4 py-3 font-semibold text-muted">Status</th>
                  <th className="text-right px-4 py-3 font-semibold text-muted">Actions</th>
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  <tr>
                    <td colSpan={6} className="px-4 py-8 text-center text-muted">Loading keys…</td>
                  </tr>
                ) : apiKeys.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="px-4 py-8 text-center text-muted">
                      No API keys yet. Create one to access MCP Workbench programmatically.
                    </td>
                  </tr>
                ) : (
                  apiKeys.map((apiKey) => (
                    <tr key={apiKey.id} className="border-b border-border/50 hover:bg-surface-hover/50 transition-colors">
                      <td className="px-4 py-3 font-medium">{apiKey.name}</td>
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-2">
                          <code className="text-xs bg-background border border-border rounded px-2 py-1 font-mono">
                            {apiKey.key_prefix}…
                          </code>
                          <button
                            onClick={() => handleCopy(apiKey.key_prefix, apiKey.id)}
                            className="text-muted hover:text-foreground transition-colors"
                            title="Copy prefix"
                          >
                            {copiedId === apiKey.id ? <CheckCircle size={14} className="text-success" /> : <Copy size={14} />}
                          </button>
                        </div>
                      </td>
                      <td className="px-4 py-3 text-muted">{fmtDate(apiKey.created_at)}</td>
                      <td className="px-4 py-3 text-muted">{fmtDate(apiKey.last_used_at)}</td>
                      <td className="px-4 py-3">
                        {apiKey.is_active ? (
                          <span className="inline-flex items-center gap-1.5 text-xs text-success">
                            <span className="w-1.5 h-1.5 rounded-full bg-success" /> Active
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1.5 text-xs text-muted">
                            <span className="w-1.5 h-1.5 rounded-full bg-muted" /> Revoked
                          </span>
                        )}
                      </td>
                      <td className="px-4 py-3 text-right">
                        {apiKey.is_active && (
                          <button
                            onClick={() => handleRevokeKey(apiKey.id)}
                            className="text-xs px-3 py-1.5 rounded-md bg-danger/10 text-danger hover:bg-danger/20 transition-colors inline-flex items-center gap-1"
                          >
                            <Trash2 size={12} /> Revoke
                          </button>
                        )}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* ─── Create Key Modal ───────────────────────────── */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
          <div className="bg-surface border border-border rounded-xl p-6 w-full max-w-md">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-bold">Create API Key</h2>
              <button onClick={() => setShowCreateModal(false)} className="text-muted hover:text-foreground">
                <X size={18} />
              </button>
            </div>
            <label className="block text-sm font-medium mb-1.5">Key Name</label>
            <input
              type="text"
              value={newKeyName}
              onChange={(e) => setNewKeyName(e.target.value)}
              placeholder="e.g., Production Server"
              className="w-full bg-background border border-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-primary transition-colors mb-4"
            />
            {error && <p className="text-sm text-danger mb-3">{error}</p>}
            <div className="flex justify-end gap-2">
              <button
                onClick={() => setShowCreateModal(false)}
                className="px-4 py-2 rounded-lg border border-border hover:bg-surface-hover transition-colors text-sm"
              >
                Cancel
              </button>
              <button
                onClick={handleCreateKey}
                disabled={!newKeyName.trim()}
                className="px-4 py-2 rounded-lg bg-primary text-white hover:bg-primary-hover transition-colors text-sm disabled:opacity-60"
              >
                Create Key
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ─── Generated Key Modal ────────────────────────── */}
      {generatedKey && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
          <div className="bg-surface border border-border rounded-xl p-6 w-full max-w-md">
            <div className="flex items-center gap-2 mb-3">
              <CheckCircle size={20} className="text-success" />
              <h2 className="text-lg font-bold">API Key Created</h2>
            </div>
            <p className="text-sm text-muted mb-4">
              Copy your key now. For security, it won&apos;t be shown again.
            </p>
            <div className="flex items-center gap-2 mb-4">
              <code className="flex-1 text-xs bg-background border border-border rounded-lg px-3 py-2 font-mono break-all">
                {generatedKey}
              </code>
              <button
                onClick={() => handleCopy(generatedKey, -1)}
                className="p-2 rounded-lg border border-border hover:bg-surface-hover transition-colors"
              >
                {copiedId === -1 ? <CheckCircle size={16} className="text-success" /> : <Copy size={16} />}
              </button>
            </div>
            <button
              onClick={() => setGeneratedKey("")}
              className="w-full px-4 py-2 rounded-lg bg-primary text-white hover:bg-primary-hover transition-colors text-sm"
            >
              Done
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
