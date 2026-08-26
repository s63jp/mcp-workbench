"use client";

import React, { useState, useEffect } from "react";
import {
  Zap, Settings, User, Shield, Save, CheckCircle, AlertCircle,
  ChevronRight, Key, LogOut, Trash2, Eye, EyeOff, Activity
} from "lucide-react";

const navItems = [
  { href: "/dashboard", label: "Overview", icon: <Activity size={18} /> },
  { href: "/dashboard/subscription", label: "Subscription", icon: <Shield size={18} /> },
  { href: "/dashboard/api-keys", label: "API Keys", icon: <Key size={18} /> },
  { href: "/dashboard/settings", label: "Settings", icon: <Settings size={18} /> },
];

// ─── Components ──────────────────────────────────────────────────
export default function SettingsPage() {
  const [activeSection, setActiveSection] = useState("profile");
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState("");
  const [showMobileMenu, setShowMobileMenu] = useState(false);
  const [userEmail, setUserEmail] = useState("");
  const [userTier, setUserTier] = useState("Free");
  const [createdAt, setCreatedAt] = useState("");

  // Profile form state
  const [email, setEmail] = useState("");

  // Password form state
  const [passwords, setPasswords] = useState({ current: "", new: "", confirm: "" });
  const [showNewPassword, setShowNewPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

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
    fetch("/api/users/me", { headers: authHeaders })
      .then((r) => (r.ok ? r.json() : null))
      .then((data) => {
        if (data) {
          setEmail(data.email || "");
          setUserEmail(data.email || "");
          setCreatedAt(data.created_at || "");
        }
      })
      .catch(() => {});
  }, []);

  const flashSaved = () => {
    setSaved(true);
    setTimeout(() => setSaved(false), 3000);
  };

  const handleSaveProfile = async () => {
    setError("");
    if (!email.trim()) return;
    try {
      const res = await fetch("/api/users/me", {
        method: "PUT",
        headers: { "Content-Type": "application/json", ...authHeaders },
        body: JSON.stringify({ email: email.trim() }),
      });
      const data = await res.json();
      if (!res.ok) {
        setError(data.error || "Failed to update email");
        return;
      }
      setUserEmail(email.trim());
      const userRaw = localStorage.getItem("mcpwb_user");
      if (userRaw) {
        try {
          const u = JSON.parse(userRaw);
          u.email = email.trim();
          localStorage.setItem("mcpwb_user", JSON.stringify(u));
        } catch {}
      }
      flashSaved();
    } catch {
      setError("Network error. Please try again.");
    }
  };

  const handlePasswordChange = async () => {
    setError("");
    if (passwords.new !== passwords.confirm) {
      setError("New passwords do not match.");
      return;
    }
    if (passwords.new.length < 8) {
      setError("Password must be at least 8 characters.");
      return;
    }
    try {
      const res = await fetch("/api/users/me", {
        method: "PUT",
        headers: { "Content-Type": "application/json", ...authHeaders },
        body: JSON.stringify({ password: passwords.new }),
      });
      const data = await res.json();
      if (!res.ok) {
        setError(data.error || "Failed to change password");
        return;
      }
      setPasswords({ current: "", new: "", confirm: "" });
      flashSaved();
    } catch {
      setError("Network error. Please try again.");
    }
  };

  const handleDeleteAccount = async () => {
    setError("");
    try {
      const res = await fetch("/api/users/me", {
        method: "DELETE",
        headers: authHeaders,
      });
      if (res.ok) {
        localStorage.removeItem("mcpwb_token");
        localStorage.removeItem("mcpwb_user");
        window.location.href = "/";
      } else {
        const data = await res.json().catch(() => ({}));
        setError(data.error || "Failed to delete account");
      }
    } catch {
      setError("Network error. Please try again.");
    }
  };

  const handleSignOut = () => {
    localStorage.removeItem("mcpwb_token");
    localStorage.removeItem("mcpwb_user");
    window.location.href = "/";
  };

  const sections = [
    { id: "profile", label: "Profile", icon: <User size={18} /> },
    { id: "security", label: "Security", icon: <Shield size={18} /> },
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
        <div className="flex items-center gap-2 text-sm text-muted mb-2">
          <a href="/dashboard" className="hover:text-foreground">Dashboard</a>
          <ChevronRight size={14} />
          <span>Settings</span>
        </div>
        <h1 className="text-2xl font-bold mb-6">Settings</h1>

        {saved && (
          <div className="flex items-center gap-2 p-3 rounded-lg bg-success/10 border border-success/20 text-success text-sm mb-4">
            <CheckCircle size={16} /> Changes saved successfully.
          </div>
        )}
        {error && (
          <div className="flex items-center gap-2 p-3 rounded-lg bg-danger/10 border border-danger/20 text-danger text-sm mb-4">
            <AlertCircle size={16} /> {error}
          </div>
        )}

        <div className="flex flex-col md:flex-row gap-6">
          {/* Sidebar */}
          <aside className="md:w-48 shrink-0">
            <nav className="flex md:flex-col gap-1 overflow-x-auto">
              {sections.map((s) => (
                <button
                  key={s.id}
                  onClick={() => setActiveSection(s.id)}
                  className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm transition-colors whitespace-nowrap ${
                    activeSection === s.id
                      ? "bg-primary/10 text-primary"
                      : "text-muted hover:text-foreground hover:bg-surface-hover"
                  }`}
                >
                  {s.icon} {s.label}
                </button>
              ))}
              <button
                onClick={handleSignOut}
                className="flex items-center gap-2 px-3 py-2 rounded-lg text-sm text-muted hover:text-danger transition-colors whitespace-nowrap"
              >
                <LogOut size={18} /> Sign Out
              </button>
            </nav>
          </aside>

          {/* Content */}
          <div className="flex-1 min-w-0">
            {activeSection === "profile" && (
              <div className="rounded-xl border border-border bg-surface p-6">
                <h2 className="text-lg font-bold mb-1">Profile</h2>
                <p className="text-sm text-muted mb-6">Your account information.</p>

                <div className="space-y-5">
                  <div>
                    <label className="block text-sm font-medium mb-1.5">Email</label>
                    <input
                      type="email"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      className="w-full bg-background border border-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-primary transition-colors"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1.5">Member since</label>
                    <p className="text-sm text-muted">
                      {createdAt ? new Date(createdAt).toLocaleDateString("en-GB", { day: "numeric", month: "long", year: "numeric" }) : "—"}
                    </p>
                  </div>
                  <button
                    onClick={handleSaveProfile}
                    className="px-4 py-2 rounded-lg bg-primary text-white hover:bg-primary-hover transition-colors text-sm flex items-center gap-2"
                  >
                    <Save size={16} /> Save Changes
                  </button>
                </div>
              </div>
            )}

            {activeSection === "security" && (
              <div className="space-y-6">
                <div className="rounded-xl border border-border bg-surface p-6">
                  <h2 className="text-lg font-bold mb-1">Change Password</h2>
                  <p className="text-sm text-muted mb-6">Use at least 8 characters.</p>
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium mb-1.5">New Password</label>
                      <div className="relative">
                        <input
                          type={showNewPassword ? "text" : "password"}
                          value={passwords.new}
                          onChange={(e) => setPasswords((p) => ({ ...p, new: e.target.value }))}
                          className="w-full bg-background border border-border rounded-lg px-3 py-2 pr-10 text-sm focus:outline-none focus:border-primary transition-colors"
                        />
                        <button
                          type="button"
                          onClick={() => setShowNewPassword(!showNewPassword)}
                          className="absolute right-3 top-1/2 -translate-y-1/2 text-muted hover:text-foreground"
                        >
                          {showNewPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                        </button>
                      </div>
                    </div>
                    <div>
                      <label className="block text-sm font-medium mb-1.5">Confirm New Password</label>
                      <div className="relative">
                        <input
                          type={showConfirmPassword ? "text" : "password"}
                          value={passwords.confirm}
                          onChange={(e) => setPasswords((p) => ({ ...p, confirm: e.target.value }))}
                          className="w-full bg-background border border-border rounded-lg px-3 py-2 pr-10 text-sm focus:outline-none focus:border-primary transition-colors"
                        />
                        <button
                          type="button"
                          onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                          className="absolute right-3 top-1/2 -translate-y-1/2 text-muted hover:text-foreground"
                        >
                          {showConfirmPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                        </button>
                      </div>
                    </div>
                    <button
                      onClick={handlePasswordChange}
                      disabled={!passwords.new || !passwords.confirm}
                      className="px-4 py-2 rounded-lg bg-primary text-white hover:bg-primary-hover transition-colors text-sm flex items-center gap-2 disabled:opacity-60"
                    >
                      <Save size={16} /> Update Password
                    </button>
                  </div>
                </div>

                <div className="rounded-xl border border-danger/30 bg-danger/5 p-6">
                  <h2 className="text-lg font-bold text-danger mb-1">Danger Zone</h2>
                  <p className="text-sm text-muted mb-4">
                    Deleting your account removes all your data permanently. This cannot be undone.
                  </p>
                  <button
                    onClick={() => setShowDeleteModal(true)}
                    className="px-4 py-2 rounded-lg bg-danger text-white hover:bg-danger/90 transition-colors text-sm flex items-center gap-2"
                  >
                    <Trash2 size={16} /> Delete Account
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* ─── Delete Account Modal ───────────────────────── */}
      {showDeleteModal && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
          <div className="bg-surface border border-border rounded-xl p-6 w-full max-w-md">
            <h2 className="text-lg font-bold mb-2">Delete your account?</h2>
            <p className="text-sm text-muted mb-6">
              This will permanently delete your account, API keys, and all associated data. This action cannot be undone.
            </p>
            <div className="flex justify-end gap-2">
              <button
                onClick={() => setShowDeleteModal(false)}
                className="px-4 py-2 rounded-lg border border-border hover:bg-surface-hover transition-colors text-sm"
              >
                Cancel
              </button>
              <button
                onClick={handleDeleteAccount}
                className="px-4 py-2 rounded-lg bg-danger text-white hover:bg-danger/90 transition-colors text-sm"
              >
                Delete Permanently
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
