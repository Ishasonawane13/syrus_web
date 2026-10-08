# 14 — Architecture Decisions

> Architecture Decision Record (ADR) style log. Each entry records a significant decision, its rationale, alternatives considered, and trade-offs accepted.

---

## ADR-001: Python + FastAPI for Backend

**Decision:** Use Python 3.13 with FastAPI as the backend framework.

**Reason:**
- FastAPI has first-class Pydantic integration for input validation
- Auto-generated OpenAPI/Swagger docs simplify development
- Async support for future WebSocket integration
- Python is the standard for AI/ML integration work
- SQLAlchemy 2.0 has excellent async ORM support

**Alternatives considered:**
- Node.js/Express — less natural for Python AI libraries
- Django — heavier, less suitable for API-first architecture
- Go — good performance but worse AI/ML ecosystem

**Trade-offs:**
- Python GIL limits CPU concurrency (acceptable for MVP; C++ engine addresses this in Phase 7)

---

## ADR-002: PostgreSQL for Database

**Decision:** Use PostgreSQL 16 as the primary database.

**Reason:**
- JSONB support for storing risk details and audit payloads
- ACID transactions critical for financial data integrity
- SQLAlchemy ORM supports it excellently
- Industry standard for financial applications
- Free and open source

**Alternatives considered:**
- SQLite — insufficient for concurrent access, no JSONB
- MongoDB — document DB fine but less natural for relational financial data
- MySQL — JSONB support weaker than Postgres

**Trade-offs:**
- Requires Docker or local Postgres installation (vs. zero-config SQLite for dev)
- Addressed with Docker Compose for easy local setup

---

## ADR-003: LLM Tool/Function Calling

**Decision:** Use structured LLM function/tool calling instead of parsing free-text responses.

**Reason:**
- Free-text parsing is fragile and error-prone
- Tool calling produces structured JSON that is validated server-side
- Modern LLMs (GPT-4o, Gemini) have excellent tool calling support
- Safer: LLM outputs are constrained to known tool schemas
- Easier to test and audit

**Alternatives considered:**
- Free-text parsing with regex — too fragile
- Always asking LLM to output JSON — unreliable without tool schemas
- No LLM, just intent classification — loses natural language flexibility

**Trade-offs:**
- Requires a capable LLM (GPT-4o or equivalent)
- Slightly higher latency than simpler models

---

## ADR-004: Deterministic Risk Engine (Not LLM-Evaluated)

**Decision:** Risk rules are implemented in Python code, not evaluated by the LLM.

**Reason:**
- LLM reasoning is probabilistic — unacceptable for financial safety rules
- Prompt injection could potentially manipulate LLM-evaluated rules
- Deterministic code is testable, auditable, and predictable
- Rules in code are version-controlled and reviewable
- Matches industry practice: risk engines are always deterministic code

**Alternatives considered:**
- Ask LLM to check if order is safe — fundamentally unsafe
- Hybrid: LLM + code — code still must be authoritative

**Trade-offs:**
- More code to write vs. asking LLM
- Worth it for correctness and safety guarantees

---

## ADR-005: Mandatory User Confirmation (Frontend Enforced)

**Decision:** The LLM can only create order proposals. Execution requires an explicit user click that calls a separate API endpoint.

**Reason:**
- Critical safety principle: AI cannot execute unilaterally
- Protects against prompt injection attacks
- Matches regulatory/compliance expectations
- Users understand what will happen before it happens
- Auditable: every execution has a user approval event

**Alternatives considered:**
- Allow LLM to auto-confirm "safe" orders — rejected on safety grounds
- Two-click confirmation — considered but single clear confirmation is sufficient

**Trade-offs:**
- Extra UX step for the user
- Worth it for safety — this is the core differentiator of the system

---

## ADR-006: Next.js App Router for Frontend

**Decision:** Use Next.js 15 with App Router and TypeScript.

**Reason:**
- React Server Components enable efficient data fetching
- App Router is the current Next.js standard
- TypeScript provides type safety matching backend Pydantic schemas
- Tailwind CSS included by default, matching the requirement

**Alternatives considered:**
- Vite + React — simpler but loses Next.js features
- Remix — good alternative but less ecosystem

**Trade-offs:**
- Steeper learning curve than plain React
- App Router patterns are still evolving

---

## ADR-007: Simulated Market (No Real Data)

**Decision:** Use a deterministic price simulator rather than a real market data API.

**Reason:**
- Eliminates external API dependency (no API keys, no quotas, no cost)
- Demo works consistently without network access
- Prices are reproducible, enabling consistent testing
- Avoids regulatory/legal questions about displaying real financial data

**Alternatives considered:**
- Free market data APIs (Alpha Vantage, Yahoo Finance) — rate limits, reliability issues
- Paid APIs — cost and complexity for a demo

**Trade-offs:**
- Prices are not real (accepted — this is paper trading)
- Users must understand this is simulated (clearly labeled in UI)

---

## ADR-008: Single Demo Account (No Multi-User Auth)

**Decision:** For MVP, implement a single hardcoded demo account. No login required.

**Reason:**
- Simplifies development significantly for Phase 1
- Focus is on AI trading logic, not authentication flows
- Demo/hackathon use case doesn't require multi-user
- Can be added in a later phase without architectural changes

**Alternatives considered:**
- JWT authentication from the start — delays core features
- Magic link auth — simpler but still adds complexity

**Trade-offs:**
- Not production-ready (accepted for MVP)
- All demo sessions share the same account state

---

## ADR-009: Architecture for Future C++ Engine

**Decision:** Design the trading engine with a Protocol/interface that can be swapped.

**Reason:**
- C++ would provide significantly better performance for order matching
- The swap should be transparent to the rest of the system
- Python engine works for MVP; C++ can come later without disruption

**Implementation:**
- `TradingEngineInterface` Protocol in Python
- Python engine implements it for Phase 1–6
- C++ engine (via gRPC or ctypes) implements same interface in Phase 7

**Trade-offs:**
- Minor overhead from interface abstraction
- Worth it for future extensibility

---

## ADR-010: Alembic for Database Migrations

**Decision:** Use Alembic for database schema migrations.

**Reason:**
- Standard SQLAlchemy migration tool
- Version-controlled schema changes
- Automatic migration generation from model changes
- Reproducible database setup across environments

**Trade-offs:**
- Adds boilerplate vs. SQLAlchemy create_all()
- Worth it for any project beyond a prototype
