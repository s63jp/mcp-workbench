# Stripe Integration for MCP Workbench

This module provides Stripe subscription management for MCP Workbench with four tiers:

| Tier | Price | Features |
|------|-------|----------|
| Free | £0/mo | Basic features |
| Pro | £10/mo | Advanced features |
| Team | £50/mo | Collaboration features |
| Enterprise | £200/mo | Full features + support |

## Quick Start

### 1. Install Dependencies

```bash
cd /home/kali/mcp-workbench
source .venv/bin/activate
pip install stripe
```

### 2. Configure Environment Variables

Copy `.env.example` to `.env` and add your Stripe test API keys:

```bash
cp .env.example .env
```

Get your test keys from: https://dashboard.stripe.com/test/apikeys

```env
STRIPE_SECRET_KEY=sk_test_your_key_here
STRIPE_WEBHOOK_SECRET=whsec_your_secret_here
STRIPE_SUCCESS_URL=http://localhost:3000/success
STRIPE_CANCEL_URL=http://localhost:3000/cancel
```

### 3. Create Products and Prices

Run the setup command to create Stripe products and prices:

```bash
source .venv/bin/activate
python stripe_integration.py --setup
```

This will output product and price IDs. Add them to your `.env` file:

```env
STRIPE_PRODUCT_FREE=prod_xxx
STRIPE_PRODUCT_PRO=prod_xxx
STRIPE_PRODUCT_TEAM=prod_xxx
STRIPE_PRODUCT_ENTERPRISE=prod_xxx
STRIPE_PRICE_FREE=price_xxx
STRIPE_PRICE_PRO=price_xxx
STRIPE_PRICE_TEAM=price_xxx
STRIPE_PRICE_ENTERPRISE=price_xxx
```

## API Reference

### `create_checkout_session(customer_email, tier, customer_id, metadata)`

Create a checkout session for a subscription.

```python
from stripe_integration import create_checkout_session

result = create_checkout_session(
    customer_email="user@example.com",
    tier="pro",
    metadata={"user_id": "12345"},
)

# Redirect user to checkout URL
print(result["url"])
```

Returns:
```json
{
  "url": "https://checkout.stripe.com/...",
  "session_id": "cs_...",
  "tier": "pro",
  "customer_id": "cus_..."
}
```

### `handle_webhook(payload, sig_header, webhook_secret)`

Process Stripe webhook events.

```python
from stripe_integration import handle_webhook
from flask import request

@app.route('/webhook', methods=['POST'])
def webhook():
    payload = request.get_data(as_text=True)
    sig_header = request.headers.get('Stripe-Signature')
    
    try:
        result = handle_webhook(payload, sig_header)
        
        if result['event_type'] == 'customer.subscription.updated':
            # Update user's subscription status in database
            pass
        elif result['event_type'] == 'customer.subscription.deleted':
            # Downgrade user to free tier
            pass
            
        return {'status': 'success'}, 200
    except Exception as e:
        return {'error': str(e)}, 400
```

Supported events:
- `checkout.session.completed`
- `customer.subscription.created`
- `customer.subscription.updated`
- `customer.subscription.deleted`
- `invoice.payment_succeeded`
- `invoice.payment_failed`

### `get_subscription_status(subscription_id, customer_id)`

Get subscription status and details.

```python
from stripe_integration import get_subscription_status

# By subscription ID
status = get_subscription_status(subscription_id="sub_123")

# By customer ID (gets first subscription)
status = get_subscription_status(customer_id="cus_123")

print(status)
```

Returns:
```json
{
  "subscription_id": "sub_123",
  "customer_id": "cus_123",
  "status": "active",
  "tier": "pro",
  "current_period_start": "2026-08-01T00:00:00",
  "current_period_end": "2026-09-01T00:00:00",
  "cancel_at_period_end": false,
  "items": [{"price_id": "price_xxx", "quantity": 1}]
}
```

### `cancel_subscription(subscription_id, at_period_end)`

Cancel a subscription.

```python
from stripe_integration import cancel_subscription

# Cancel at end of billing period (default)
result = cancel_subscription(subscription_id="sub_123")

# Cancel immediately
result = cancel_subscription(subscription_id="sub_123", at_period_end=False)
```

### `get_customer_subscriptions(customer_id)`

Get all subscriptions for a customer.

```python
from stripe_integration import get_customer_subscriptions

subscriptions = get_customer_subscriptions(customer_id="cus_123")
```

### `create_customer_portal_session(customer_id)`

Create a billing portal session for customer self-service.

```python
from stripe_integration import create_customer_portal_session

result = create_customer_portal_session(customer_id="cus_123")
# Redirect user to result["url"] for self-service billing management
```

## Webhook Setup

1. Go to Stripe Dashboard → Developers → Webhooks
2. Add endpoint: `https://your-domain.com/webhook`
3. Select events:
   - `checkout.session.completed`
   - `customer.subscription.created`
   - `customer.subscription.updated`
   - `customer.subscription.deleted`
   - `invoice.payment_succeeded`
   - `invoice.payment_failed`
4. Copy the webhook secret to `STRIPE_WEBHOOK_SECRET`

## Testing

Run the test suite:

```bash
source .venv/bin/activate
python stripe_integration.py
```

Use Stripe's test cards:
- `4242 4242 4242 4242` - Success
- `4000 0000 0000 9995` - Declined
- `4000 0025 0000 3155` - Requires authentication

## Integration Example (FastAPI)

```python
from fastapi import FastAPI, Request, HTTPException
from stripe_integration import (
    create_checkout_session,
    handle_webhook,
    get_subscription_status,
)

app = FastAPI()

@app.post("/create-checkout")
async def create_checkout(email: str, tier: str = "pro"):
    result = create_checkout_session(
        customer_email=email,
        tier=tier,
        metadata={"user_id": "current_user_id"},
    )
    return {"checkout_url": result["url"]}

@app.post("/webhook")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get("Stripe-Signature")
    
    try:
        event = handle_webhook(payload, sig_header)
        
        if event["event_type"] == "checkout.session.completed":
            # Activate subscription
            pass
        elif event["event_type"] == "customer.subscription.deleted":
            # Deactivate subscription
            pass
            
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/subscription/{user_id}")
async def get_user_subscription(user_id: str):
    # Get customer_id from your database
    customer_id = get_customer_id_from_db(user_id)
    return get_subscription_status(customer_id=customer_id)
```

## Security Notes

- Never expose your Stripe secret key in client-side code
- Always verify webhook signatures
- Use test keys during development
- Store environment variables securely (e.g., `.env` in `.gitignore`)
