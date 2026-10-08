# 04 — Features

> This file is the source of truth for feature status. Update after every implementation milestone.
> **Last updated: 2026-10-07** (Phase 0 — Documentation complete, Phase 1 in progress)

---

## Legend

- ✅ Implemented and tested
- 🔄 In progress
- ⏳ Planned (next phase)
- 🔮 Future (later phase)
- ❌ Explicitly not implemented (with reason)

---

## Phase 1 — Foundation

| Feature | Status | Location | Notes |
|---------|--------|----------|-------|
| Project directory structure | ✅ | `/` root | Frontend, backend, docs, tests |
| Docker Compose setup | ✅ | `docker-compose.yml` | Postgres + Backend + Frontend |
| Environment configuration | ✅ | `.env.example` | LLM, DB, CORS vars |
| FastAPI backend scaffold | ✅ | `backend/app/main.py` | With CORS, lifespan |
| PostgreSQL connection | ✅ | `backend/app/database.py` | SQLAlchemy async |
| Database migrations (Alembic) | ✅ | `backend/migrations/` | Full schema |
| Demo seed data | ✅ | `backend/app/seed.py` | Account, positions, instruments |
| Health check endpoint | ✅ | `GET /health` | Returns version + DB status |
| Next.js frontend scaffold | ✅ | `frontend/` | App Router, TypeScript, Tailwind |
| Basic navigation layout | ✅ | `frontend/src/components/layout/` | Sidebar, header |

## Phase 2 — Paper Trading Core

| Feature | Status | Location | Notes |
|---------|--------|----------|-------|
| Instrument model | ✅ | `backend/app/models/instrument.py` | 8 NSE instruments |
| Market price simulator | ✅ | `backend/app/trading/simulator.py` | Deterministic tick simulation |
| Account model | ✅ | `backend/app/models/account.py` | Cash, portfolio value |
| Position model | ✅ | `backend/app/models/position.py` | Avg price, P&L |
| Order model | ✅ | `backend/app/models/order.py` | Full lifecycle states |
| Execution model | ✅ | `backend/app/models/execution.py` | Fill records |
| Portfolio service | ✅ | `backend/app/services/portfolio_service.py` | Unrealized P&L calc |
| Market order execution | ✅ | `backend/app/trading/engine.py` | Immediate fill at market |
| GET /account | ✅ | `backend/app/api/account.py` | Cash, value, P&L |
| GET /account/positions | ✅ | `backend/app/api/account.py` | All positions |
| GET /market/{symbol}/price | ✅ | `backend/app/api/market.py` | Simulated price |
| Portfolio dashboard UI | ✅ | `frontend/src/app/dashboard/` | Value, cash, P&L |
| Positions table UI | ✅ | `frontend/src/components/dashboard/` | Holdings view |

## Phase 3 — AI Copilot

| Feature | Status | Location | Notes |
|---------|--------|----------|-------|
| Chat interface UI | ✅ | `frontend/src/app/copilot/` | Message history |
| LLM integration | ✅ | `backend/app/ai/copilot.py` | OpenAI / Gemini |
| System prompt | ✅ | `backend/app/ai/prompts.py` | Safety-first prompt |
| Tool definitions | ✅ | `backend/app/ai/tools.py` | All tool schemas |
| get_account() tool | ✅ | `backend/app/ai/tools.py` | Account summary |
| get_positions() tool | ✅ | `backend/app/ai/tools.py` | All positions |
| get_position(symbol) tool | ✅ | `backend/app/ai/tools.py` | Single position |
| get_market_price(symbol) tool | ✅ | `backend/app/ai/tools.py` | Simulated price |
| get_orders() tool | ✅ | `backend/app/ai/tools.py` | Order history |
| get_pnl() tool | ✅ | `backend/app/ai/tools.py` | P&L summary |
| create_order_proposal() tool | ✅ | `backend/app/ai/tools.py` | Structured order intent |
| POST /ai/chat | ✅ | `backend/app/api/ai.py` | Main chat endpoint |
| Account questions (NL) | ✅ | Via AI tools | "What is my cash?" |
| Market questions (NL) | ✅ | Via AI tools | "What is TCS price?" |
| Trade requests (NL) | ✅ | Via AI tools | "Buy 50 TCS" |

## Phase 4 — Safety

| Feature | Status | Location | Notes |
|---------|--------|----------|-------|
| Risk engine | ✅ | `backend/app/risk/engine.py` | Deterministic rules |
| Max order value rule | ✅ | Risk engine | ₹5,00,000 default |
| Max quantity rule | ✅ | Risk engine | 10,000 shares default |
| Insufficient cash check | ✅ | Risk engine | Exact balance check |
| Insufficient holdings check | ✅ | Risk engine | For SELL orders |
| Position exposure limit | ✅ | Risk engine | 40% of portfolio |
| Daily loss limit | ✅ | Risk engine | ₹1,00,000 default |
| Invalid quantity check | ✅ | Risk engine | Must be > 0, integer |
| Invalid symbol check | ✅ | Risk engine | Must be in instruments |
| Order preview UI | ✅ | `frontend/src/components/copilot/` | Confirmation card |
| Explicit confirmation | ✅ | Frontend + backend | Button + API verify |
| POST /orders/{id}/execute | ✅ | `backend/app/api/orders.py` | Approval required |
| Audit log model | ✅ | `backend/app/models/audit_log.py` | Complete trail |
| Audit log UI | ✅ | `frontend/src/app/audit/` | All AI actions |
| Tool input validation | ✅ | `backend/app/ai/tools.py` | Server-side checks |
| Prompt injection resistance | ✅ | `backend/app/ai/prompts.py` | System prompt design |

## Phase 5 — Advanced Trading

| Feature | Status | Location | Notes |
|---------|--------|----------|-------|
| Limit orders | ⏳ | Planned | Backend + UI |
| Stop-loss orders | ⏳ | Planned | Backend + UI |
| Order book simulation | ⏳ | Planned | Bid/ask levels |
| Partial fills | ⏳ | Planned | For large orders |
| WebSocket price updates | ⏳ | Planned | Real-time ticks |
| cancel_order() tool | ⏳ | Planned | Cancel open orders |

## Phase 6 — Polish

| Feature | Status | Location | Notes |
|---------|--------|----------|-------|
| P&L charts | ⏳ | Planned | Recharts / Chart.js |
| Portfolio allocation chart | ⏳ | Planned | Pie/donut chart |
| Loading states | ⏳ | Planned | Skeleton loaders |
| Error states | ⏳ | Planned | User-friendly errors |
| Empty states | ⏳ | Planned | No positions etc |
| Responsive mobile design | ⏳ | Planned | Mobile breakpoints |
| Backend unit tests | ⏳ | Planned | Pytest suite |
| Frontend tests | 🔮 | Future | Vitest / Playwright |

## Phase 7 — Quant/Engineering Upgrade

| Feature | Status | Notes |
|---------|--------|-------|
| C++ matching engine | 🔮 | After stable MVP |
| gRPC interface | 🔮 | C++ communication |
| Order book (full) | 🔮 | Multiple price levels |
| Redis caching | 🔮 | Live state |

## Explicitly Not Implemented

| Feature | Reason |
|---------|--------|
| Real brokerage connection | Paper trading only — by design |
| Real market data | Simulated market — no external dependency |
| User authentication (multi-user) | Single demo account for MVP simplicity |
| Real money | Never — core safety principle |
