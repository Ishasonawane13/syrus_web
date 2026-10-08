# 13 — Roadmap

## Current Phase: MVP Complete (Phases 1–4) ✅

---

## MVP (Phases 1–4)

The MVP delivers the complete end-to-end demo flow:

```
Natural language → AI intent → Risk check → Proposal → Approval → Execution → Portfolio update → Audit
```

### Phase 1 — Foundation ✅
- [x] Project structure
- [x] Environment configuration (`.env.example`, `.env`)
- [x] Database schema (SQLAlchemy async models)
- [x] Demo seed data (`backend/app/seed.py`)
- [x] Health check endpoint (`GET /health`)
- [x] Frontend scaffold with navigation layout

### Phase 2 — Paper Trading Core ✅
- [x] Instrument model and API (`GET /market/instruments`)
- [x] Market price simulator (`backend/app/trading/simulator.py`)
- [x] Account and position models (`backend/app/models/`)
- [x] Portfolio dashboard UI (`frontend/src/components/PortfolioSummary.tsx`)
- [x] P&L calculation (`backend/app/services/portfolio_service.py`)
- [x] Market order execution (`backend/app/trading/engine.py`)
- [x] `GET /account`, `GET /account/positions`, `GET /market/{symbol}/price`

### Phase 3 — AI Copilot ✅
- [x] Chat interface UI (`frontend/src/components/CopilotChat.tsx`)
- [x] LLM integration (OpenAI / Gemini + deterministic fallback)
- [x] Tool/function calling architecture (`backend/app/ai/tools.py`)
- [x] All query tools (account, positions, market, orders, P&L)
- [x] `create_order_proposal()` tool
- [x] `POST /ai/chat` endpoint

### Phase 4 — Safety ✅
- [x] Deterministic risk engine with all 8 rules (`backend/app/risk/engine.py`)
- [x] Order preview / confirmation card UI (`frontend/src/components/OrderConfirmationCard.tsx`)
- [x] `POST /orders/{id}/execute` endpoint with status validation
- [x] Rejection flow UI with clear risk rule feedback
- [x] Audit log model and API (`GET /audit/logs`)
- [x] Audit log UI (`frontend/src/components/AuditLogView.tsx`)
- [x] Tool input validation (`backend/app/ai/tools.py`)
- [x] Prompt injection resistance (`backend/app/ai/prompts.py`)

---

## Next (Phase 5 — Advanced Trading)

- [ ] Limit orders with order book matching
- [ ] Stop-loss orders
- [ ] Order book depth visualization
- [ ] Partial fills for large orders
- [ ] WebSocket price streaming
- [ ] cancel_order() via AI
- [ ] Order status checking via AI

---

## Near Future (Phase 6 — Polish)

- [ ] P&L charts (portfolio over time)
- [ ] Portfolio allocation pie chart
- [ ] Loading/skeleton states
- [ ] Better error messages and empty states
- [ ] Responsive mobile design
- [x] Full backend test suite (pytest — 15/15 passing)
- [ ] Frontend tests (Vitest)
- [ ] Docker build optimization
- [ ] Proper API rate limiting

---

## Future (Phase 7 — Engineering Upgrade)

- [ ] C++ matching/execution engine
- [ ] gRPC interface between Python and C++
- [ ] Full order book with multiple price levels
- [ ] Redis for price caching
- [ ] Multi-user authentication (JWT)
- [ ] Paper trading competitions
- [ ] Strategy backtesting

---

## Not On Roadmap (By Design)

| Feature | Reason |
|---------|--------|
| Real brokerage integration | Paper trading only — fundamental safety principle |
| Real market data | Simulated market is sufficient for demo; avoids API costs |
| Real money | Never |
| Production deployment | Demo/hackathon scope |

---

## Version History

| Version | Phase | Status |
|---------|-------|--------|
| 0.1.0 | Phase 0 (Documentation) | ✅ Complete |
| 0.2.0 | Phase 1 (Foundation) | ✅ Complete |
| 0.3.0 | Phase 2 (Trading Core) | ✅ Complete |
| 0.4.0 | Phase 3 (AI Copilot) | ✅ Complete |
| 0.5.0 | Phase 4 (Safety) | ✅ Complete |
| 1.0.0 | MVP Complete | ✅ Complete |
