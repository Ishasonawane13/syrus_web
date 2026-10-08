# 02 — Setup Guide

> This guide assumes you may be returning to the project months later and need to start from scratch.

---

## Prerequisites

| Tool | Version | Install |
|------|---------|---------|
| Docker | 24+ | https://www.docker.com/get-started |
| Docker Compose | v2+ | Included with Docker Desktop |
| Node.js | 20+ | https://nodejs.org |
| Python | 3.13+ | https://python.org |
| PostgreSQL client | any | Optional (for manual DB inspection) |

---

## 1. Clone / Open the Project

```bash
# If cloning from Git
git clone <repo-url> ai-trading-copilot
cd ai-trading-copilot

# If already in the directory
cd c:\Users\ishas\Desktop\code
```

---

## 2. Environment Variables

```bash
cp .env.example .env
```

Edit `.env` with your values:

```env
# LLM Provider (choose one)
LLM_PROVIDER=openai           # or: gemini, anthropic
OPENAI_API_KEY=sk-...         # if using OpenAI
GEMINI_API_KEY=...            # if using Google Gemini

# Database
DATABASE_URL=postgresql://trader:trader_pass@localhost:5432/trading_copilot

# Backend
SECRET_KEY=change-me-in-production
BACKEND_CORS_ORIGINS=http://localhost:3000

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000
```

**Never commit `.env` to source control.**

---

## 3. Docker Setup (Recommended)

This is the easiest way to run the full stack.

```bash
docker-compose up --build
```

This starts:
- **PostgreSQL** on port 5432
- **FastAPI backend** on port 8000
- **Next.js frontend** on port 3000

Wait for all services to be healthy, then open http://localhost:3000.

**First-run database migration and seed data run automatically.**

To stop:
```bash
docker-compose down
```

To reset the database:
```bash
docker-compose down -v   # -v removes volumes (wipes DB)
docker-compose up --build
```

---

## 4. Manual Local Development

### 4a. Database (PostgreSQL)

Option A — Use Docker just for the DB:
```bash
docker-compose up postgres -d
```

Option B — Use your local PostgreSQL:
```bash
# Create database
createdb trading_copilot
createuser trader --pwprompt   # set password: trader_pass
psql -c "GRANT ALL ON DATABASE trading_copilot TO trader;"
```

### 4b. Backend (FastAPI)

```bash
cd backend

# Create virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac/Linux

# Install dependencies
pip install -r requirements.txt

# Run database migrations
alembic upgrade head

# Seed demo data
python -m app.seed

# Start development server
uvicorn app.main:app --reload --port 8000
```

Backend available at: http://localhost:8000  
API docs at: http://localhost:8000/docs

### 4c. Frontend (Next.js)

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

Frontend available at: http://localhost:3000

---

## 5. Verify Setup

### Health Check
```bash
curl http://localhost:8000/health
# Expected: {"status": "ok", "version": "1.0.0"}
```

### API Docs
Open http://localhost:8000/docs in your browser — you should see the FastAPI Swagger UI.

### Demo Account
The seed script creates:
- User: `demo@tradingcopilot.ai`
- Starting cash: ₹10,00,000
- Pre-seeded positions in TCS, INFY, RELIANCE, HDFCBANK

---

## 6. Running Tests

```bash
# Backend tests
cd backend
pytest tests/ -v

# Run specific test file
pytest tests/unit/test_risk_engine.py -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html
```

---

## 7. Environment Variables Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `LLM_PROVIDER` | Yes | `openai` | LLM backend: `openai`, `gemini` |
| `OPENAI_API_KEY` | If openai | — | OpenAI API key |
| `GEMINI_API_KEY` | If gemini | — | Google Gemini API key |
| `LLM_MODEL` | No | provider default | Model name override |
| `DATABASE_URL` | Yes | — | PostgreSQL connection string |
| `SECRET_KEY` | Yes | — | JWT signing key |
| `BACKEND_CORS_ORIGINS` | Yes | — | Allowed CORS origins |
| `NEXT_PUBLIC_API_URL` | Yes | — | Frontend → Backend URL |
| `SEED_DEMO_DATA` | No | `true` | Auto-seed on startup |

---

## 8. Troubleshooting

### "Database connection refused"
- Check PostgreSQL is running: `docker-compose ps`
- Check `DATABASE_URL` in `.env` is correct
- Ensure the database exists: `createdb trading_copilot`

### "LLM API error"
- Verify your API key is set in `.env`
- Check you have credits/quota on the LLM provider
- The app has a fallback mode for basic queries without LLM

### "Port already in use"
```bash
# Find and kill process on port 8000
netstat -ano | findstr :8000
taskkill /PID <pid> /F
```

### Frontend "API not reachable"
- Ensure backend is running on port 8000
- Check `NEXT_PUBLIC_API_URL` in `.env`
- Check CORS settings in backend `.env`

### Resetting Everything
```bash
docker-compose down -v --remove-orphans
docker-compose up --build
```
