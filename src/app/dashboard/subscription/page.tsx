"use client";

import React, { useState } from "react";
import {
  Zap, CreditCard, CheckCircle, ChevronRight,
  Shield, Star, AlertCircle
} from "lucide-react";

// ─── Types ───────────────────────────────────────────────────────
type PricingTier = { name: string; price: string; period: string; tagline: string; features: string[]; cta: string; highlight?: boolean };

// ─── Demo Data ───────────────────────────────────────────────────
const currentPlan = {
  name: "Pro",
  price: "£9",
  period: "/month",
  nextBilling: "September 3, 2024",
  features: [
    "Everything in Free",
    "Private server testing",
    "Full HVE verification suite",
    "Performance history & graphs",
    "Saved configurations (unlimited)",
    "Export reports (PDF/JSON)",
    "Email support",
  ],
};

const pricingTiers: PricingTier[] = [
  {
    name: "Free",
    price: "£0",
    period: "/forever",
    tagline: "For individual developers",
    features: [
      "Test public MCP servers",
      "Basic startup validation",
      "Console output viewer",
      "3 saved configurations",
      "Community support",
    ],
    cta: "Downgrade",
  },
  {
    name: "Pro",
    price: "£9",
    period: "/month",
    tagline: "For power users",
    features: [
      "Everything in Free",
      "Private server testing",
      "Full HVE verification suite",
      "Performance history & graphs",
      "Saved configurations (unlimited)",
      "Export reports (PDF/JSON)",
      "Email support",
    ],
    cta: "Current Plan",
    highlight: true,
  },
  {
    name: "Team",
    price: "£29",
    period: "/month",
    tagline: "Per seat — growing teams",
    features: [
      "Everything in Pro",
      "Shared team workspaces",
      "CI/CD webhook integration",
      "Custom verification pipelines",
      "Audit logs",
      "Slack notifications",
      "Priority support",
    ],
    cta: "Upgrade to Team",
  },
  {
    name: "Enterprise",
    price: "Custom",
    period: "",
    tagline: "For large organizations",
    features: [
      "Everything in Team",
      "On-premise deployment",
      "Custom security policies",
      "SSO (SAML, OIDC)",
      "Dedicated account manager",
      "SLA guarantee",
      "Custom integrations",
    ],
    cta: "Contact Sales",
  },
];

const navItems = [
  { href: "/dashboard", label: "Overview", icon: <Zap size={18} /> },
  { href: "/dashboard/subscription", label: "Subscription", icon: <CreditCard size={18} /> },
  { href: "/dashboard/api-keys", label: "API Keys", icon: <Shield size={18} /> },
  { href: "/dashboard/settings", label: "Settings", icon: <Star size={18} /> },
];

// ─── Components ──────────────────────────────────────────────────
export default function SubscriptionPage() {
  const [selectedTier, setSelectedTier] = useState<string | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [showMobileMenu, setShowMobileMenu] = useState(false);
  const [error, setError] = useState("");
  const [plan, setPlan] = useState<{ tier: string; status: string } | null>(null);

  React.useEffect(() => {
    const token = localStorage.getItem("mcpwb_token");
    if (!token) return;
    fetch("/api/subscriptions", {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((r) => (r.ok ? r.json() : null))
      .then((data) => {
        if (data && data.subscription) {
          setPlan({ tier: data.subscription.tier, status: data.subscription.status });
        }
      })
      .catch(() => {});
  }, []);

  const handlePlanChange = async (tierName: string) => {
    if (tierName === (plan?.tier ?? "free")) return;
    setError("");
    setIsProcessing(true);
    try {
      const token = localStorage.getItem("mcpwb_token");
      if (!token) {
        window.location.href = "/login";
        return;
      }
      const res = await fetch("/api/subscriptions/checkout", {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({ tier: tierName.toLowerCase() }),
      });
      const data = await res.json();
      if (!res.ok) {
        setError(data.error || "Could not start checkout. Please try again.");
        setIsProcessing(false);
        return;
      }
      if (data.url) {
        window.location.href = data.url;
      } else {
        setError("Checkout session created but no redirect URL returned.");
        setIsProcessing(false);
      }
    } catch (err) {
      setError("Network error. Please try again.");
      setIsProcessing(false);
    }
  };

  const handleOpenPortal = async () => {
    setError("");
    setIsProcessing(true);
    try {
      const token = localStorage.getItem("mcpwb_token");
      if (!token) {
        window.location.href = "/login";
        return;
      }
      const res = await fetch("/api/subscriptions/portal", {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
      });
      const data = await res.json();
      if (!res.ok) {
        setError(data.error || "Could not open billing portal.");
        setIsProcessing(false);
        return;
      }
      if (data.url) {
        window.location.href = data.url;
      } else {
        setError("No portal URL returned.");
        setIsProcessing(false);
      }
    } catch {
      setError("Network error. Please try again.");
      setIsProcessing(false);
    }
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
              <span className="text-sm text-muted">Pro Plan</span>
              <div className="w-8 h-8 rounded-full bg-primary/20 flex items-center justify-center text-primary font-semibold text-sm">
                JD
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
            <span>Subscription</span>
          </div>
          <h1 className="text-2xl font-bold mb-1">Subscription & Billing</h1>
          <p className="text-sm text-muted">Manage your plan, billing, and payment methods.</p>
        </div>

        {/* Current Plan Card */}
        <div className="p-6 rounded-xl border border-primary/30 bg-gradient-to-r from-primary/10 to-primary/5 mb-8">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-4">
            <div className="flex items-center gap-4">
              <div className="p-3 rounded-xl bg-primary/20">
                <Star size={24} className="text-primary" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h2 className="text-xl font-bold">{(plan?.tier ?? "free").charAt(0).toUpperCase() + (plan?.tier ?? "free").slice(1)} Plan</h2>
                  <span className="text-xs px-2 py-0.5 rounded-full bg-primary/20 text-primary border border-primary/30">Active</span>
                </div>
                <p className="text-sm text-muted mt-1">
                  {plan?.tier && plan.tier !== "free"
                    ? "Manage your subscription from the Stripe billing portal."
                    : "Free forever. Upgrade when you need more."}
                </p>
              </div>
            </div>
            <div className="text-right">
              <div className="flex items-baseline justify-end gap-1">
                <span className="text-3xl font-bold">
                  {(plan?.tier ?? "free") === "free" ? "£0" : (plan?.tier ?? "free") === "team" ? "£29" : (plan?.tier ?? "free") === "enterprise" ? "Custom" : "£9"}
                </span>
                <span className="text-sm text-muted">/month</span>
              </div>
            </div>
          </div>

          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3 mt-4">
            {currentPlan.features.slice(0, 6).map((feature, i) => (
              <div key={i} className="flex items-center gap-2 text-sm">
                <CheckCircle size={14} className="text-success shrink-0" />
                <span>{feature}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Plan Selection */}
        <section className="mb-10">
          <div className="text-center mb-6">
            <h2 className="text-xl font-bold mb-2">Change Plan</h2>
            <p className="text-sm text-muted">Upgrade or downgrade at any time. Changes take effect immediately.</p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-4">
            {pricingTiers.map((tier) => (
              <div
                key={tier.name}
                className={`rounded-xl border p-5 flex flex-col transition-all ${
                  tier.highlight
                    ? "border-primary bg-primary/5 shadow-lg shadow-primary/10"
                    : selectedTier === tier.name
                    ? "border-primary bg-surface"
                    : "border-border bg-surface"
                }`}
              >
                {tier.name.toLowerCase() === (plan?.tier ?? "free") && (
                  <div className="absolute -mt-8 right-5 bg-primary text-white text-[10px] font-bold px-2 py-1 rounded-bl-lg">
                    CURRENT PLAN
                  </div>
                )}
                <div className="mb-3">
                  <h3 className="font-semibold text-lg mb-0.5">{tier.name}</h3>
                  <p className="text-xs text-muted">{tier.tagline}</p>
                </div>
                <div className="flex items-baseline gap-1 mb-4">
                  <span className="text-3xl font-bold">{tier.price}</span>
                  {tier.period && <span className="text-sm text-muted">{tier.period}</span>}
                </div>
                <ul className="space-y-2 mb-6 flex-1">
                  {tier.features.slice(0, 5).map((feat, i) => (
                    <li key={i} className="flex items-start gap-2 text-sm">
                      <CheckCircle size={14} className="text-success shrink-0 mt-0.5" />
                      <span>{feat}</span>
                    </li>
                  ))}
                </ul>
                <button
                  onClick={() => handlePlanChange(tier.name)}
                  disabled={tier.name.toLowerCase() === (plan?.tier ?? "free") || isProcessing}
                  className={`w-full py-2 rounded-lg text-sm font-medium transition-colors ${
                    tier.name.toLowerCase() === (plan?.tier ?? "free")
                      ? "bg-border text-muted cursor-not-allowed"
                      : tier.highlight
                      ? "bg-primary text-white hover:bg-primary-hover"
                      : "border border-border hover:bg-surface-hover"
                  }`}
                >
                  {isProcessing ? "Processing..." : tier.cta}
                </button>
              </div>
            ))}
          </div>
          {error && (
            <div className="mt-4 flex items-start gap-3 p-3 rounded-lg bg-danger/10 border border-danger/20">
              <AlertCircle size={16} className="text-danger shrink-0 mt-0.5" />
              <p className="text-sm text-danger">{error}</p>
            </div>
          )}
        </section>

        {/* Billing Management */}
        <section className="mb-10">
          <div className="mb-4">
            <h2 className="text-xl font-bold">Billing Management</h2>
            <p className="text-sm text-muted">
              Invoices, payment methods, and billing details are managed securely through Stripe.
            </p>
          </div>

          <div className="rounded-xl border border-border bg-surface p-6">
            {plan?.tier && plan.tier !== "free" ? (
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                <div className="flex items-center gap-4">
                  <div className="p-3 rounded-xl bg-primary/20">
                    <CreditCard size={24} className="text-primary" />
                  </div>
                  <div>
                    <p className="font-medium">Stripe Billing Portal</p>
                    <p className="text-sm text-muted">
                      View invoices, update your payment method, and manage billing details.
                    </p>
                  </div>
                </div>
                <button
                  onClick={handleOpenPortal}
                  disabled={isProcessing}
                  className="px-4 py-2 rounded-lg bg-primary text-white hover:bg-primary-hover transition-colors text-sm flex items-center gap-2 disabled:opacity-60"
                >
                  <CreditCard size={14} /> {isProcessing ? "Opening…" : "Open Billing Portal"}
                </button>
              </div>
            ) : (
              <div className="flex items-start gap-3">
                <AlertCircle size={20} className="text-muted shrink-0 mt-0.5" />
                <div>
                  <p className="font-medium mb-1">You&apos;re on the Free plan</p>
                  <p className="text-sm text-muted">
                    Upgrade to Pro or Team above to unlock billing management, invoices, and payment methods.
                  </p>
                </div>
              </div>
            )}
          </div>
        </section>

        {/* Help Section */}
        <div className="mt-8 p-4 rounded-xl border border-border bg-surface/50">
          <div className="flex items-start gap-3">
            <AlertCircle size={20} className="text-muted shrink-0 mt-0.5" />
            <div>
              <h3 className="font-semibold mb-1">Need help with billing?</h3>
              <p className="text-sm text-muted">
                Contact us at{" "}
                <a href="mailto:gizmo50009@agentmail.ai" className="text-primary hover:underline">
                  gizmo50009@agentmail.ai
                </a>{" "}
                for any questions about your subscription or invoices.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
