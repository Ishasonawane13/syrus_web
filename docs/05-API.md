# 05 — API Reference

> Base URL: `http://localhost:8000`  
> All responses are JSON. All monetary values are in Indian Rupees (₹).  
> Authentication: Session-based (demo account auto-loaded for MVP).

---

## Health

### GET /health

Returns backend health status.

**Response:**
```json
{
  "status": "ok",
  "version": "1.0.0",
  "database": "connected",
  "timestamp": "2026-10-07T17:00:00Z"
}
```

---

## Account

### GET /account

Returns the demo account summary.

**Response:**
```json
{
  "id": "uuid",
  "user_email": "demo@tradingcopilot.ai",
  "cash_balance": 807500.00,
  "portfolio_value": 1245750.00,
  "total_value": 2053250.00,
  "available_cash": 807500.00,
  "realized_pnl": 12500.00,
  "unrealized_pnl": 45750.00,
  "daily_pnl": 8250.00,
  "daily_pnl_pct": 0.82
}
```

### GET /account/positions

Returns all current positions.

**Response:**
```json
{
  "positions": [
    {
      "symbol": "TCS",
      "name": "Tata Consultancy Services",
      "quantity": 50,
      "avg_price": 3450.00,
      "current_price": 3520.50,
      "market_value": 176025.00,
      "unrealized_pnl": 3525.00,
      "unrealized_pnl_pct": 2.04,
      "allocation_pct": 14.15
    }
  ]
}
```

### GET /account/pnl

Returns P&L breakdown.

**Response:**
```json
{
  "realized_pnl": 12500.00,
  "unrealized_pnl": 45750.00,
  "daily_pnl": 8250.00,
  "daily_pnl_pct": 0.82,
  "total_pnl": 58250.00
}
```

---

## Market

### GET /market/{symbol}/price

Returns current simulated price for a symbol.

**Path params:** `symbol` — e.g., `TCS`, `INFY`, `RELIANCE`

**Response:**
```json
{
  "symbol": "TCS",
  "name": "Tata Consultancy Services",
  "price": 3520.50,
  "bid": 3519.75,
  "ask": 3521.25,
  "change": 45.50,
  "change_pct": 1.31,
  "volume": 1245800,
  "timestamp": "2026-10-07T17:00:00Z"
}
```

### GET /market/instruments

Returns all supported instruments.

**Response:**
```json
{
  "instruments": [
    {
      "symbol": "TCS",
      "name": "Tata Consultancy Services",
      "exchange": "NSE",
      "lot_size": 1,
      "is_active": true
    }
  ]
}
```

### GET /market/{symbol}/orderbook

Returns simulated order book for a symbol.

**Response:**
```json
{
  "symbol": "TCS",
  "bids": [
    {"price": 3519.75, "quantity": 500},
    {"price": 3519.00, "quantity": 1200}
  ],
  "asks": [
    {"price": 3521.25, "quantity": 300},
    {"price": 3522.00, "quantity": 800}
  ],
  "timestamp": "2026-10-07T17:00:00Z"
}
```

---

## Orders

### GET /orders

Returns all orders.

**Query params:**
- `status` — filter by status (optional)
- `limit` — max results (default 50)
- `offset` — pagination offset

**Response:**
```json
{
  "orders": [
    {
      "id": "uuid",
      "symbol": "TCS",
      "side": "BUY",
      "order_type": "MARKET",
      "quantity": 50,
      "limit_price": null,
      "status": "FILLED",
      "estimated_value": 176025.00,
      "execution_price": 3520.50,
      "execution_quantity": 50,
      "fees": 88.01,
      "risk_status": "PASSED",
      "created_at": "2026-10-07T16:00:00Z",
      "executed_at": "2026-10-07T16:00:05Z"
    }
  ],
  "total": 12
}
```

### GET /orders/{order_id}

Returns a single order with full details.

### POST /orders/{order_id}/execute

Executes an approved order. **Only works if status is PENDING_APPROVAL.**

**Request body:** (empty — approval is identified by order ID)
```json
{}
```

**Response:**
```json
{
  "order_id": "uuid",
  "status": "FILLED",
  "execution_price": 3520.50,
  "execution_quantity": 50,
  "fees": 88.01,
  "cash_after": 807411.99,
  "message": "Order executed successfully"
}
```

**Errors:**
- `404` — Order not found
- `400` — Order not in PENDING_APPROVAL status
- `422` — Validation error

### POST /orders/{order_id}/cancel

Cancels a PENDING_APPROVAL or OPEN order.

---

## AI Copilot

### POST /ai/chat

Main chat endpoint. Sends a user message to the AI copilot.

**Request:**
```json
{
  "message": "Buy 50 TCS at market price",
  "conversation_id": "optional-uuid-for-history"
}
```

**Response:**
```json
{
  "message": "I'll place a market order for 50 shares of TCS. Here's the order proposal:",
  "conversation_id": "uuid",
  "order_proposal": {
    "id": "uuid",
    "symbol": "TCS",
    "side": "BUY",
    "order_type": "MARKET",
    "quantity": 50,
    "estimated_value": 176025.00,
    "risk_status": "PASSED",
    "risk_details": [
      {"rule": "cash_check", "status": "PASSED", "message": "Sufficient cash available"}
    ],
    "warnings": [],
    "status": "PENDING_APPROVAL"
  },
  "tool_calls": [
    {
      "tool": "create_order_proposal",
      "args": {"action": "BUY", "symbol": "TCS", "quantity": 50, "order_type": "MARKET"},
      "result": "proposal_created"
    }
  ]
}
```

### GET /ai/chat/history

Returns conversation history (limited for MVP).

---

## Audit

### GET /audit/logs

Returns audit log entries.

**Query params:**
- `limit` — max results (default 50)
- `offset` — pagination

**Response:**
```json
{
  "logs": [
    {
      "id": "uuid",
      "timestamp": "2026-10-07T16:00:00Z",
      "user_request": "Buy 50 TCS at market price",
      "interpreted_intent": {"action": "BUY", "symbol": "TCS", "quantity": 50},
      "tool_used": "create_order_proposal",
      "order_id": "uuid",
      "risk_result": "PASSED",
      "user_approved": true,
      "execution_result": "FILLED"
    }
  ],
  "total": 45
}
```

---

## Error Responses

All errors follow this format:

```json
{
  "error": "INSUFFICIENT_CASH",
  "message": "Insufficient cash balance for this order",
  "details": {
    "required": 176025.00,
    "available": 50000.00
  }
}
```

Common error codes:
- `INVALID_SYMBOL` — Symbol not in supported instruments
- `INSUFFICIENT_CASH` — Not enough cash for BUY
- `INSUFFICIENT_HOLDINGS` — Not enough shares for SELL
- `RISK_REJECTED` — Risk engine rejected the order
- `ORDER_NOT_APPROVABLE` — Order not in PENDING_APPROVAL status
- `VALIDATION_ERROR` — Input validation failed
