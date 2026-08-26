# Stripe Setup Guide — MCP Workbench (Revenue Unlock)

The entire billing pipeline is already built and verified. The ONLY missing piece is a
real Stripe account. This guide takes ~20 minutes.

## Step 1 — Create the Stripe account (5 min)

1. Go to https://dashboard.stripe.com/register
2. Sign up with your email (s63jp1988@gmail.com works fine)
3. You can stay in **Test mode** to verify the flow end-to-end first, then flip to Live.

## Step 2 — Create Products & Prices (5 min)

In the Stripe Dashboard → **Product catalog** → **Add product**:

| Product | Price | Billing |
|---|---|---|
| MCP Workbench Pro | £9.00 | Recurring, monthly |
| MCP Workbench Team | £29.00 | Recurring, monthly |

For each product, after creating the price, copy the **Price ID** (looks like `price_1AbCdEf...`).

## Step 3 — Get API keys (2 min)

Dashboard → **Developers** → **API keys**:

- **Publishable key** → `pk_test_...` (or `pk_live_...`)
- **Secret key** → `sk_test_...` (or `sk_live_...`)

## Step 4 — Webhook endpoint (5 min)

Dashboard → **Developers** → **Webhooks** → **Add endpoint**:

- **Endpoint URL:** `https://mcp-workbench.uk/api/webhooks/stripe`
- **Events to send:**
  - `checkout.session.completed`
  - `customer.subscription.updated`
  - `customer.subscription.deleted`
- After creating, click **Reveal** on the signing secret → `whsec_...`

## Step 5 — Put the keys in .env (2 min)

Edit `/home/kali/mcp-workbench/.env` on the Kali VM:

```
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PRICE_PRO=price_...
STRIPE_PRICE_TEAM=price_...
```

(The server auto-loads `.env` on start — no code changes needed.)

## Step 6 — Restart the service (1 min)

```bash
export XDG_RUNTIME_DIR=/run/user/1000
export DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus
systemctl --user restart mcp-workbench.service
```

## Step 7 — Verify

1. Register/login at https://mcp-workbench.uk
2. Dashboard → Subscription → click a plan → Stripe Checkout opens
3. Pay with test card `4242 4242 4242 4242` (test mode)
4. Webhook fires → DB `subscriptions` table flips to `pro`/`active`
5. Dashboard shows "Pro Plan"

## Going live

- In Stripe: **Activate your account** (business details, bank account for payouts)
- Switch keys to `pk_live_...` / `sk_live_...` in `.env`, restart service
- Re-create the webhook endpoint with the live signing secret

## Notes

- The checkout handler already rejects placeholder keys with a clean 503, so the
  site degrades gracefully until keys are in place.
- Webhook handler updates: `checkout.session.completed` → tier upgrade,
  `customer.subscription.deleted` → downgrade to free, `customer.subscription.updated` → status sync.
- Prices are hardcoded in the frontend (£9/£29) — keep the Stripe prices matching.
