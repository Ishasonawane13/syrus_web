# AI Trading Copilot

## Title
AI Trading Copilot: Natural-Language Trading with Human-in-the-Loop Safety

## Domain
FinTech

## Problem Statement
Trading interfaces demand multiple screens, order jargon, and manual order construction. A plain AI chatbot removes friction but adds risks: hallucinated data, ambiguous commands, malicious prompts, and accidental execution. We must build a chatbot that understands market/account queries and creates orders from natural language, with no trade without explicit user approval.

## Abstract
AI Trading Copilot is a paper-trading assistant that lets traders manage a simulated brokerage account through plain English. A trader types "Buy 50 TCS at market" and the system responds — not by executing blindly, but by extracting the intent, validating it deterministically, screening it through a risk engine, and presenting an exact order preview that the trader must confirm before anything executes. The LLM is restricted solely to intent extraction; it cannot touch any order or account API. All critical logic — validation, risk checks, and execution — is handled by deterministic code. This architecture eliminates hallucinated trades, ambiguous commands, prompt-injection attacks embedded in stock names, and accidental execution. Every request, risk decision, approval, and trade is written to an immutable audit log.

## Features
- **Read-Only Queries**: Traders query today's P&L, positions down more than 5%, average purchase price, and NIFTY options near the money in plain English, answered from live simulated market data.
- **Order Placement with Mandatory Confirmation**: LLM function-calling converts natural language into a structured order {action, symbol, quantity, order_type}. A deterministic validator checks symbol validity, available cash, and lot-size rules. A risk engine rejects unsafe orders (e.g., oversized positions, thin liquidity). The trader then sees an exact order preview with Confirm and Reject — no approval means no trade, ever.
- **Standing Instructions**: Conditional triggers such as "Alert me if RELIANCE drops below ₹2,800" are persisted in a database table and evaluated continuously against a live simulated price feed by a background worker. Each condition fires at most once via an atomic cooldown guard and survives server restarts.
- **Multi-Step Plans**: The copilot proposes basket or hedging plans as a full-plan preview requiring a single approval. Outcomes for every leg — including partial fills and rejected orders — are reported individually in the chat.
- **Malicious Input Defense**: An input-sanitization layer intercepts prompt-injection attempts embedded in stock names or order fields before they reach the LLM or execution path.
- **Web Chat Interface**: Real-time WebSocket-backed chat streams copilot responses, order previews, and execution confirmations to the trader in under 100 ms.
- **Audit Trail**: Every request, validation result, risk decision, approval event, and execution is appended to an immutable log — full traceability with zero silent failures.

## Setup Instructions
1. Clone the repository.
2. Navigate to the backend directory.
3. Create a virtual environment: `python -m venv .venv`
4. Activate the virtual environment: `.venv\Scripts\activate`
5. Install dependencies: `pip install -r requirements.txt`
6. Run the application: `uvicorn main:app --reload`

## Conclusion
This document outlines the architecture and features of the AI Trading Copilot backend. For further details, refer to the codebase and API documentation.
