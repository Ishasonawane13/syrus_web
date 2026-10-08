# 12 — Demo Guide

> Use this script for hackathon presentations. Follow the steps in order.

---

## Pre-Demo Checklist

- [ ] Application is running (`docker-compose up`)
- [ ] Browser open at http://localhost:3000
- [ ] LLM API key is configured
- [ ] Demo account has seeded data

---

## Demo Script (~10 minutes)

### Step 1: Open the Dashboard (1 min)

**Show:** Dashboard page at http://localhost:3000/dashboard

**Say:**
> "This is the AI Trading Copilot — a paper trading platform where you interact with your portfolio using natural language. The dashboard shows portfolio value, cash, P&L, and current positions."

**Point out:**
- Total portfolio value (₹~20L)
- Available cash (₹8,07,500)
- Today's P&L (positive, green)
- Position table with 4 holdings

---

### Step 2: Ask About Cash Balance (1 min)

**Navigate to:** http://localhost:3000/copilot

**Type:**
> "What is my available cash?"

**Show:**
- AI responds with exact cash amount from `get_account()` tool call
- Response comes from tool data, not invented

**Say:**
> "The AI calls a validated backend tool — it never invents financial data."

---

### Step 3: Ask About a Position (1 min)

**Type:**
> "Show me my TCS position"

**Show:**
- AI calls `get_position("TCS")`
- Returns: quantity, avg price, current price, unrealized P&L

**Say:**
> "Every number comes from the database through approved tools."

---

### Step 4: Ask for Market Price (1 min)

**Type:**
> "What's the current price of INFY?"

**Show:**
- AI calls `get_market_price("INFY")`
- Returns price with bid/ask spread

---

### Step 5: Create a BUY Order (2 min)

**Type:**
> "Buy 50 TCS at market price"

**Show:**
1. AI creates order proposal
2. Risk engine runs (show PASSED checkmarks)
3. **Order Confirmation Card appears:**
   - BUY · TCS · 50 shares
   - Market Order
   - Estimated value: ₹1,76,025
   - Cash after: ₹6,31,475
   - Risk: PASSED ✓
   - [Confirm Order] [Cancel]

**Say:**
> "Nothing has happened yet. The AI has only proposed the order. The user must explicitly confirm."

**Click: [Confirm Order]**

**Show:**
- Order executes at simulated market price
- Portfolio updates (more TCS, less cash)
- Execution confirmation message

---

### Step 6: Show the Audit Trail (1 min)

**Navigate to:** http://localhost:3000/audit

**Show:**
- The buy order is fully logged:
  - User request: "Buy 50 TCS at market price"
  - Interpreted intent: {action: BUY, symbol: TCS, qty: 50}
  - Risk result: PASSED
  - User approved: Yes
  - Execution result: FILLED

**Say:**
> "Every AI action is auditable. This is critical for safety and explainability."

---

### Step 7: Demonstrate Risk Rejection (2 min)

**Navigate back to:** Copilot

**Type:**
> "Buy 2000 TCS at market price"

**Show:**
1. AI attempts to create proposal
2. Risk engine runs
3. **Risk Rejection:**
   - REJECTED ✗
   - Reason: "Order value ₹70,40,000 exceeds maximum ₹5,00,000"

**Say:**
> "The risk engine is deterministic — no AI involved. The LLM cannot bypass it. Even if someone prompt-injected the AI, the risk engine would still reject the order."

**Type:**
> "Sell 500 SBIN"

**Show:**
- Risk engine: REJECTED — "Insufficient holdings. You have 0 SBIN shares."

---

### Step 8: Ask P&L Summary (1 min)

**Type:**
> "How much have I made today? And overall?"

**Show:**
- AI calls `get_pnl()`
- Returns: daily P&L, unrealized P&L, realized P&L, total

---

### Step 9: Show Order History (30 sec)

**Navigate to:** http://localhost:3000/orders

**Show:**
- All orders with statuses (FILLED, PENDING_APPROVAL, etc.)
- The TCS order we just placed is at the top

---

### Step 10: Explain the Safety Architecture (1 min)

**Show the architecture slide / diagram or explain verbally:**

```
User → "Buy 50 TCS"
    → AI (understands intent)
    → Tool call (structured, validated)
    → Risk Engine (deterministic rules)
    → Order Proposal (not executed)
    → User confirms (mandatory)
    → Trading Engine (paper execution)
    → Portfolio/P&L update
    → Audit log
```

**Key safety points:**
1. LLM never touches the database directly
2. Risk engine is pure Python, no AI
3. User confirmation is mandatory — no bypass
4. Full audit trail

---

## Backup Demo Points

If asked about tech stack:
- Frontend: Next.js 15 + TypeScript + Tailwind CSS
- Backend: FastAPI + Python 3.13
- Database: PostgreSQL
- AI: OpenAI GPT-4o with function calling (configurable)
- Infrastructure: Docker Compose

If asked about AI safety:
- Point to the trust model in Security docs
- Emphasize tool whitelist — LLM can only call approved functions
- Server-side validation catches malformed tool args
- Risk engine is independent of LLM

If asked about real trading:
- This is explicitly PAPER TRADING ONLY
- No brokerage connections, no real money
- Designed to demonstrate safe AI-financial system architecture

---

## Troubleshooting During Demo

| Problem | Fix |
|---------|-----|
| AI slow to respond | LLM API latency — explain it's calling GPT-4o |
| Order not showing | Refresh the orders page |
| Price seems off | Expected — simulator, not real market |
| DB error | `docker-compose restart backend` |
