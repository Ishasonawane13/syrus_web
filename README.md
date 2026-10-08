# 🤖 AI Trading Copilot

> A safe, paper-trading platform where users interact with a trading account using natural language.

[![Phase](https://img.shields.io/badge/Phase-1%20Foundation-blue)]()
[![Stack](https://img.shields.io/badge/Stack-Next.js%20%7C%20FastAPI%20%7C%20PostgreSQL-green)]()
[![Safety](https://img.shields.io/badge/Safety-Paper%20Trading%20Only-red)]()

---

## ⚠️ Important Notice

**This is a PAPER TRADING system only.**  
No real money, no real brokerage connections, no real trade execution.  
All trading is fully simulated for educational and demo purposes.

---

## What Is This?

AI Trading Copilot is a demo-grade fintech application that allows users to:

- Ask natural-language questions about their portfolio ("What is my available cash?")
- Request trades in plain English ("Buy 50 TCS at market price")
- Receive structured order proposals with risk analysis
- **Explicitly confirm** before any trade executes
- View portfolio performance, P&L, and audit history

The AI understands intent — but **never** directly executes trades. Every action passes through a deterministic risk engine and requires explicit user approval.

---

## Major Features

| Feature | Status |
|---------|--------|
| Paper trading account with seed data | ✅ Phase 1 |
| Simulated market with tick prices | ✅ Phase 2 |
| Portfolio dashboard (value, cash, P&L) | ✅ Phase 2 |
| AI Copilot chat interface | ✅ Phase 3 |
| LLM tool/function calling | ✅ Phase 3 |
| Deterministic risk engine | ✅ Phase 4 |
| Order preview & explicit confirmation | ✅ Phase 4 |
| Audit log | ✅ Phase 4 |
| Limit orders & stop-loss | 🔄 Phase 5 |
| WebSocket real-time updates | 🔄 Phase 5 |
| C++ matching engine | 🔄 Phase 7 |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 15, TypeScript, Tailwind CSS |
| Backend | Python 3.13, FastAPI, Pydantic v2 |
| Database | PostgreSQL 16 |
| AI | Configurable LLM (OpenAI / Gemini) with function calling |
| Cache | Redis (optional, future) |
| Infra | Docker, Docker Compose |

---

## Architecture Overview

```
User (Browser)
    │
    ▼
Next.js Frontend
    │  REST / WebSocket
    ▼
FastAPI Backend
    ├── AI Layer (LLM Tool Calling)
    ├── Risk Engine (deterministic)
    ├── Trading Engine (paper execution)
    └── PostgreSQL Database
```

Full architecture: [docs/03-ARCHITECTURE.md](docs/03-ARCHITECTURE.md)

---

## Quick Start

### Prerequisites
- Docker & Docker Compose
- Node.js 20+ (for local frontend dev)
- Python 3.13+ (for local backend dev)

### With Docker (recommended)

```bash
cp .env.example .env
# Edit .env with your LLM API key
docker-compose up --build
```

App: http://localhost:3000  
API: http://localhost:8000  
API Docs: http://localhost:8000/docs

### Manual Setup

See [docs/02-SETUP-GUIDE.md](docs/02-SETUP-GUIDE.md) for full local development instructions.

---

## Demo Credentials

The application seeds a demo account automatically on first run.

| Field | Value |
|-------|-------|
| Demo User | `demo@tradingcopilot.ai` |
| Starting Cash | ₹10,00,000 |
| Pre-seeded Positions | TCS, INFY, RELIANCE, HDFCBANK |

See [docs/12-DEMO-GUIDE.md](docs/12-DEMO-GUIDE.md) for the complete demo walkthrough.

---

## Documentation

| Doc | Description |
|-----|-------------|
| [01-PROJECT-OVERVIEW](docs/01-PROJECT-OVERVIEW.md) | What and why |
| [02-SETUP-GUIDE](docs/02-SETUP-GUIDE.md) | Installation & local dev |
| [03-ARCHITECTURE](docs/03-ARCHITECTURE.md) | System design & data flow |
| [04-FEATURES](docs/04-FEATURES.md) | Feature checklist |
| [05-API](docs/05-API.md) | REST API reference |
| [06-DATABASE](docs/06-DATABASE.md) | Schema & relationships |
| [07-AI-COPILOT](docs/07-AI-COPILOT.md) | LLM integration & tools |
| [08-RISK-ENGINE](docs/08-RISK-ENGINE.md) | Risk rules documentation |
| [09-TRADING-ENGINE](docs/09-TRADING-ENGINE.md) | Order lifecycle |
| [10-SECURITY](docs/10-SECURITY.md) | Trust model & safety |
| [11-TESTING](docs/11-TESTING.md) | Test suite guide |
| [12-DEMO-GUIDE](docs/12-DEMO-GUIDE.md) | Hackathon demo script |
| [13-ROADMAP](docs/13-ROADMAP.md) | MVP & future plans |
| [14-DECISIONS](docs/14-DECISIONS.md) | Architecture decisions |
| [15-CHANGELOG](docs/15-CHANGELOG.md) | Implementation history |

---

## Safety Principles

```
NEVER:
✗ LLM → database mutation
✗ LLM → direct trade execution  
✗ Bypass risk checks
✗ Bypass user approval
✗ Real money / real brokerage

ALWAYS:
✓ AI → Intent → Validation → Risk → Approval → Execution
✓ Every order requires explicit user confirmation
✓ Risk engine is deterministic, not LLM-driven
✓ Full audit trail for every action
```
