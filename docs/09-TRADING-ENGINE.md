# 09 — Trading Engine

## Overview

The Trading Engine handles the full lifecycle of paper orders — from creation through execution to portfolio update. It simulates realistic market behavior without connecting to any real exchange.

**Location:** `backend/app/trading/`

---

## Architecture

```
Order Proposal (PENDING_APPROVAL)
        │
        │ User confirms → POST /orders/{id}/execute
        ▼
TradingEngine.execute_approved_order(order_id)
        │
        ├── Verify order status = PENDING_APPROVAL
        ├── Verify account ownership
        ├── Get current market price (simulator)
        │
        ├── [MARKET ORDER] → fill immediately at market price
        ├── [LIMIT ORDER] → check if price condition met
        │       If met: fill immediately
        │       If not: set status=OPEN, schedule for check
        │
        ├── Create Execution record
        ├── Update Position (avg price, quantity)
        ├── Update Account (cash balance)
        ├── Create Transaction record
        ├── Update Order status (FILLED / OPEN)
        └── Create Audit Log entry
```

---

## Market Simulator

**Location:** `backend/app/trading/simulator.py`

The simulator generates deterministic, realistic-looking price data.

### Base Prices (Seeded)

| Symbol | Base Price | Typical Range |
|--------|-----------|---------------|
| RELIANCE | ₹2,800 | ₹2,700–₹2,900 |
| TCS | ₹3,500 | ₹3,400–₹3,600 |
| INFY | ₹1,500 | ₹1,450–₹1,550 |
| HDFCBANK | ₹1,650 | ₹1,600–₹1,700 |
| ICICIBANK | ₹1,100 | ₹1,050–₹1,150 |
| SBIN | ₹620 | ₹600–₹640 |
| ITC | ₹450 | ₹440–₹460 |
| TATAMOTORS | ₹950 | ₹920–₹980 |

### Tick Simulation

```python
def generate_tick(symbol: str, base_price: float, seed: int) -> Tick:
    """
    Generates a deterministic price tick using a seeded random walk.
    
    - Uses time-based seed for reproducibility
    - Applies bounded random walk (max ±2% per tick)
    - Spread: ask = price + 0.05%, bid = price - 0.05%
    - Volume: random within typical range
    """
```

Prices are updated every 30 seconds (configurable). The seed ensures the same price sequence for a given day, making the demo reproducible.

---

## Order Lifecycle

```
PENDING_APPROVAL
    │
    ├── User cancels → CANCELLED
    │
    └── User confirms → execute_approved_order()
            │
            ├── MARKET order: immediate fill → FILLED
            │
            └── LIMIT order:
                    ├── Price condition met now → FILLED
                    └── Price condition not met → OPEN
                            │
                            ├── Price met later → FILLED
                            └── User cancels → CANCELLED
```

**Status transitions:**
- `PENDING_APPROVAL` → `CANCELLED` (user cancels before confirmation)
- `PENDING_APPROVAL` → `FILLED` (market order confirmed)
- `PENDING_APPROVAL` → `OPEN` (limit order, price not yet met)
- `OPEN` → `FILLED` (limit condition met)
- `OPEN` → `CANCELLED` (user cancels open order)

---

## Market Order Execution

```python
def execute_market_order(order: Order, account: Account) -> ExecutionResult:
    # 1. Get current simulated price
    price = MarketSimulator.get_price(order.symbol)
    
    # 2. Apply slippage (0.05% for large orders)
    effective_price = apply_slippage(price, order.quantity)
    
    # 3. Calculate totals
    gross_value = effective_price * order.quantity
    fees = calculate_fees(gross_value)
    total_cost = gross_value + fees  # for BUY
    
    # 4. Final cash check (price may have moved)
    if order.side == "BUY" and total_cost > account.cash_balance:
        raise InsufficientCashError(...)
    
    # 5. Create execution record
    execution = Execution(
        order_id=order.id,
        execution_price=effective_price,
        execution_quantity=order.quantity,
        fees=fees,
        total_value=gross_value
    )
    
    # 6. Update position
    update_position(account, order.symbol, order.quantity, effective_price, order.side)
    
    # 7. Update cash
    if order.side == "BUY":
        account.cash_balance -= total_cost
    else:
        account.cash_balance += (gross_value - fees)
    
    # 8. Record transaction
    create_transaction(account, execution, order.side)
    
    return ExecutionResult(
        order_id=order.id,
        status="FILLED",
        execution_price=effective_price,
        execution_quantity=order.quantity,
        fees=fees
    )
```

---

## Position Updates

### BUY — Average Price Calculation

When buying into an existing position, the average price is recalculated:

```
new_avg_price = (
    (existing_quantity × existing_avg_price) + (new_quantity × execution_price)
) / (existing_quantity + new_quantity)
```

Example:
- Existing: 50 × ₹3,450 = ₹1,72,500
- New buy: 20 × ₹3,520 = ₹70,400
- New avg: (₹1,72,500 + ₹70,400) / 70 = **₹3,469.29**

### SELL — Realized P&L Calculation

```
realized_pnl = (execution_price - avg_price) × quantity_sold
```

Example:
- Sell 20 TCS at ₹3,520, avg cost ₹3,469.29
- Realized P&L = (₹3,520 - ₹3,469.29) × 20 = **+₹1,014.20**

After sell:
- Remaining quantity: 30 shares
- Avg price: unchanged (₹3,469.29)
- Account: +₹70,400 cash (minus fees)

---

## Fees

Simulated brokerage fees:

| Fee | Rate | Notes |
|-----|------|-------|
| Brokerage | 0.05% of trade value | Min ₹20 per order |
| STT (BUY) | 0.1% | Securities Transaction Tax |
| STT (SELL) | 0.1% | |
| Exchange fee | 0.00325% | NSE transaction charge |

Total effective fee: ~0.155% per trade (realistic for Indian markets).

---

## Unrealized P&L Calculation

Calculated at query time (not stored):

```
unrealized_pnl = (current_price - avg_price) × quantity
unrealized_pnl_pct = unrealized_pnl / (avg_price × quantity) × 100
```

---

## Partial Fills (Phase 5)

Partial fills simulate orders filling across multiple price levels:

```
Order: BUY 1000 TCS

Fills:
  300 @ ₹3,520  =  ₹10,56,000
  400 @ ₹3,521  =  ₹14,08,400
  300 @ ₹3,522  =  ₹10,56,600

Weighted avg execution price:
  (₹10,56,000 + ₹14,08,400 + ₹10,56,600) / 1000 = ₹3,521.00

Status: PARTIALLY_FILLED during execution, FILLED when complete
```

Partial fills are not implemented in Phase 1/2 — all market orders fill 100% at one price.

---

## Daily P&L Tracking

At midnight (or first request of the day), a snapshot of portfolio value is taken and stored as `daily_pnl_start` in the account table.

```
daily_pnl = current_total_value - daily_pnl_start
```

---

## Future: C++ Engine Interface

The `TradingEngine` class exposes this interface:

```python
class TradingEngineInterface(Protocol):
    def execute_approved_order(self, order_id: str) -> ExecutionResult: ...
    def cancel_order(self, order_id: str) -> CancelResult: ...
    def get_order_status(self, order_id: str) -> OrderStatus: ...
```

A future C++ engine accessed via Python FFI (ctypes) or gRPC would implement the same interface. The rest of the system is unaffected.
