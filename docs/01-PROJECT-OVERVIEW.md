# 01 — Project Overview

## What Is AI Trading Copilot?

AI Trading Copilot is a **paper-trading platform** that lets users interact with a simulated trading account using plain English.

Instead of clicking through complex order forms, you simply type:

> "Buy 50 TCS at market price"
> "What is my available cash?"
> "Show me my biggest positions"
> "How much did I make today?"

The AI understands your intent, structures it into a validated order, runs it through a deterministic risk engine, shows you a clear confirmation card — and only executes after you explicitly click **Confirm**.

---

## Problem

Retail trading platforms are complex. New investors struggle with:
- Understanding order types (market, limit, stop-loss)
- Navigating cluttered UIs
- Understanding risk before placing orders
- Reviewing portfolio performance clearly

Additionally, AI-assisted trading raises serious safety concerns — LLMs can hallucinate, be prompt-injected, or produce malformed outputs. Most demos ignore this completely.

---

## Solution

AI Trading Copilot solves both problems:

1. **Natural language interface** — users express intent in plain English
2. **Safe execution model** — the LLM never directly executes anything
3. **Deterministic risk engine** — rules are enforced in code, not by the AI
4. **Mandatory confirmation** — every order requires explicit user approval
5. **Full audit trail** — every AI action is logged for transparency

---

## Who Is This For?

- **Demo / Hackathon**: shows a complete AI+fintech+safety architecture
- **Students**: learn about trading without risking real money
- **Developers**: reference architecture for safe LLM-powered financial systems

---

## Major Components

```
┌─────────────────────────────────────────────────────┐
│                    Next.js Frontend                  │
│  ┌─────────────┐  ┌────────────┐  ┌──────────────┐  │
│  │  Dashboard  │  │  AI Chat   │  │ Order Preview│  │
│  │  Portfolio  │  │  Copilot   │  │ Confirmation │  │
│  └─────────────┘  └────────────┘  └──────────────┘  │
└──────────────────────────┬──────────────────────────┘
                           │ REST API
┌──────────────────────────▼──────────────────────────┐
│                    FastAPI Backend                   │
│  ┌──────────┐  ┌──────────┐  ┌────────────────────┐ │
│  │ AI Layer │  │ Risk     │  │  Trading Engine    │ │
│  │ LLM Tools│  │ Engine   │  │  Paper Execution   │ │
│  └──────────┘  └──────────┘  └────────────────────┘ │
│  ┌──────────────────────────────────────────────┐    │
│  │         PostgreSQL Database                  │    │
│  │  users | accounts | orders | positions | ... │    │
│  └──────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────┘
```

---

## Complete Request-to-Execution Flow

```
1. User types: "Buy 50 TCS at market"
        │
        ▼
2. AI Copilot receives message
   → Calls tool: create_order_proposal(action=BUY, symbol=TCS, qty=50, type=MARKET)
        │
        ▼
3. Backend validates tool arguments
   → Symbol exists? ✓
   → Quantity > 0? ✓
   → Order type supported? ✓
        │
        ▼
4. Risk Engine runs deterministic checks
   → Cash sufficient? ✓
   → Position exposure OK? ✓
   → Order value within limit? ✓
   → Trading hours OK? ✓
        │
        ▼
5. Order Proposal created (status: PENDING_APPROVAL)
   → Proposal ID generated
   → Estimated value calculated
   → Risk summary attached
        │
        ▼
6. Frontend shows Order Confirmation Card
   ┌──────────────────────────┐
   │  BUY · TCS · 50 shares   │
   │  MARKET ORDER            │
   │  Est. Value: ₹1,92,500   │
   │  Cash After: ₹8,07,500   │
   │  Risk: PASSED ✓          │
   │  [Confirm] [Cancel]      │
   └──────────────────────────┘
        │
        ▼ (User clicks Confirm)
7. Frontend calls execute_approved_order(proposal_id)
        │
        ▼
8. Trading Engine executes paper trade
   → Gets simulated market price
   → Fills order
   → Updates cash balance
   → Updates position
   → Calculates P&L
        │
        ▼
9. Audit Log entry created
   → User request, AI intent, tool call, risk result,
     approval, execution — all recorded
        │
        ▼
10. Dashboard refreshes with updated portfolio
```

---

## What Makes It Safe

| Principle | Implementation |
|-----------|---------------|
| LLM cannot write to DB | All DB mutations go through validated service layer |
| LLM cannot execute orders | Only `execute_approved_order` does this, requires backend-generated ID |
| Risk engine is deterministic | Written in Python, not LLM-evaluated |
| Confirmation is mandatory | Frontend enforces it; backend checks approval status |
| Audit trail is complete | Every step logged with timestamps |
| Secrets never in code | All keys via environment variables |
