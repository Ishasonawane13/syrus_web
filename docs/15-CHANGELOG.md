# 15 — Changelog

All significant implementation milestones are recorded here.

---

## 2026-10-07

### Completed
- **Full MVP Implementation (Phases 1–4) Complete & Verified**:
  - **Phase 1 (Foundation)**: FastAPI application scaffold, async database models, demo seed data, environment configurations, and health check.
  - **Phase 2 (Paper Trading Core)**: Simulated NSE price generator (8 instruments: TCS, INFY, RELIANCE, HDFCBANK, ICICIBANK, SBIN, ITC, TATAMOTORS), portfolio service, P&L calculations, market order execution, position tracking with weighted average cost.
  - **Phase 3 (AI Copilot)**: Full AI Copilot service supporting OpenAI & Gemini function calling with intelligent deterministic fallback engine, system prompt guardrails, and server-side tool validation.
  - **Phase 4 (Safety)**: 8-rule deterministic Python risk engine (insufficient cash, holdings, single order value, daily loss limit, position exposure %, price deviation, quantity, and symbol checks), interactive order confirmation cards, explicit approval flow, and immutable audit logs.
  - **Frontend Application**: Vite + React 18 + TypeScript modern dark-mode trading desk featuring live market ticker, real-time portfolio metrics, holdings table, interactive AI Copilot chat with quick prompt pills, order history, and audit trail viewer.
  - **Automated Test Suite**: 15/15 tests passing across all risk engine rules and end-to-end API workflows.
