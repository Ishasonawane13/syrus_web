# 08 — Risk Engine

## Overview

The risk engine is a **deterministic** Python module that evaluates orders against a set of rules. It operates entirely independently of the LLM — it cannot be influenced, bypassed, or overridden by AI output.

**Location:** `backend/app/risk/engine.py`

The risk engine is called after tool validation but before creating an order proposal in the database.

---

## Risk Check Flow

```
Order Parameters
        │
        ▼
1. symbol_check()
        │
        ▼
2. quantity_check()
        │
        ▼
3. price_check()
        │
        ▼
4. cash_check() [BUY only]
        │
        ▼
5. holdings_check() [SELL only]
        │
        ▼
6. order_value_check()
        │
        ▼
7. position_exposure_check()
        │
        ▼
8. daily_loss_check()
        │
        ▼
PASSED or REJECTED
```

If any rule returns REJECTED, the order proposal is created with `risk_status=REJECTED` and the execution flow stops. The frontend will show the rejection reason.

---

## Rules

### R01 — Symbol Check

**Rule:** The symbol must be in the list of supported, active instruments.

**Input:** `symbol: str`

**Logic:**
```python
if symbol not in active_instrument_symbols:
    return REJECTED("INVALID_SYMBOL", f"{symbol} is not a supported instrument")
```

**Example PASS:** `symbol="TCS"` → TCS is in instruments, is_active=True  
**Example REJECT:** `symbol="AAPL"` → AAPL not in instruments

---

### R02 — Quantity Check

**Rule:** Quantity must be a positive integer within allowed range.

**Input:** `quantity: int`

**Logic:**
```python
if quantity <= 0:
    return REJECTED("INVALID_QUANTITY", "Quantity must be greater than 0")
if quantity > MAX_QUANTITY:  # default: 10,000
    return REJECTED("MAX_QUANTITY_EXCEEDED", 
                    f"Max quantity is {MAX_QUANTITY}, requested {quantity}")
```

**Example PASS:** `quantity=50` → 0 < 50 < 10000  
**Example REJECT:** `quantity=0` → Not positive  
**Example REJECT:** `quantity=15000` → Exceeds maximum

---

### R03 — Price Check (Limit Orders)

**Rule:** For limit orders, the limit price must be a positive number within a reasonable range of current price.

**Input:** `order_type: str, limit_price: float, current_price: float`

**Logic:**
```python
if order_type == "LIMIT":
    if limit_price <= 0:
        return REJECTED("INVALID_PRICE", "Limit price must be positive")
    
    # Reject prices more than 20% away from current
    deviation = abs(limit_price - current_price) / current_price
    if deviation > 0.20:
        return REJECTED("PRICE_OUT_OF_RANGE", 
                        f"Limit price deviates {deviation*100:.1f}% from current price")
```

**Example PASS:** Current ₹3,500, limit ₹3,450 (1.4% deviation)  
**Example REJECT:** Current ₹3,500, limit ₹100 (massive deviation)

---

### R04 — Cash Check (BUY)

**Rule:** Available cash must be sufficient to cover the full estimated order value.

**Input:** `side: str, estimated_value: float, available_cash: float`

**Logic:**
```python
if side == "BUY":
    if estimated_value > available_cash:
        return REJECTED("INSUFFICIENT_CASH",
                        f"Insufficient cash. Required: ₹{estimated_value:,.2f}, "
                        f"Available: ₹{available_cash:,.2f}")
```

**Example PASS:** estimated=₹1,76,025 < available=₹8,07,500  
**Example REJECT:** estimated=₹5,00,000 > available=₹1,00,000

---

### R05 — Holdings Check (SELL)

**Rule:** Account must hold at least the requested quantity of the symbol.

**Input:** `side: str, symbol: str, quantity: int, current_holdings: int`

**Logic:**
```python
if side == "SELL":
    if quantity > current_holdings:
        return REJECTED("INSUFFICIENT_HOLDINGS",
                        f"Insufficient holdings. Requested to sell: {quantity}, "
                        f"Current holding: {current_holdings}")
```

**Example PASS:** Sell 20, hold 50 → 20 ≤ 50  
**Example REJECT:** Sell 100, hold 30 → 100 > 30  
**Example REJECT:** Sell 10, hold 0 → No position

---

### R06 — Order Value Check

**Rule:** A single order's estimated value must not exceed the maximum allowed order value.

**Input:** `estimated_value: float`

**Config:** `MAX_ORDER_VALUE = 500000` (₹5,00,000 default)

**Logic:**
```python
if estimated_value > MAX_ORDER_VALUE:
    return REJECTED("MAX_ORDER_VALUE_EXCEEDED",
                    f"Order value ₹{estimated_value:,.0f} exceeds "
                    f"maximum ₹{MAX_ORDER_VALUE:,.0f}")
```

**Example PASS:** 50 × ₹3,500 = ₹1,75,000 < ₹5,00,000  
**Example REJECT:** 200 × ₹3,500 = ₹7,00,000 > ₹5,00,000

---

### R07 — Position Exposure Check

**Rule:** A single position must not exceed a maximum percentage of the total portfolio value.

**Input:** `symbol: str, new_position_value: float, total_portfolio_value: float`

**Config:** `MAX_POSITION_EXPOSURE_PCT = 0.40` (40% default)

**Logic:**
```python
new_exposure = new_position_value / total_portfolio_value
if new_exposure > MAX_POSITION_EXPOSURE_PCT:
    return REJECTED("POSITION_EXPOSURE_EXCEEDED",
                    f"This order would give {symbol} a {new_exposure*100:.1f}% "
                    f"portfolio allocation, exceeding the {MAX_POSITION_EXPOSURE_PCT*100:.0f}% limit")
```

**Example PASS:** New position = ₹4,00,000, portfolio = ₹20,00,000 → 20%  
**Example REJECT:** New position = ₹9,00,000, portfolio = ₹20,00,000 → 45% > 40%

---

### R08 — Daily Loss Limit Check

**Rule:** If today's realized + unrealized P&L has fallen below the daily loss limit, reject new orders.

**Input:** `daily_pnl: float`

**Config:** `MAX_DAILY_LOSS = -100000` (₹1,00,000 loss limit)

**Logic:**
```python
if daily_pnl < MAX_DAILY_LOSS:
    return REJECTED("DAILY_LOSS_LIMIT",
                    f"Daily loss limit reached. Today's P&L: ₹{daily_pnl:,.0f}, "
                    f"Limit: ₹{MAX_DAILY_LOSS:,.0f}")
```

**Example PASS:** Daily P&L = -₹50,000 > -₹1,00,000  
**Example REJECT:** Daily P&L = -₹1,20,000 < -₹1,00,000

---

## Risk Result Format

```python
@dataclass
class RuleResult:
    rule_id: str       # e.g., "R04"
    rule_name: str     # e.g., "cash_check"
    status: str        # "PASSED" or "REJECTED"
    message: str       # Human-readable explanation
    details: dict      # Relevant values

@dataclass
class RiskResult:
    status: str              # "PASSED" or "REJECTED"
    rules: List[RuleResult]  # All rules evaluated
    rejected_by: Optional[str]  # Rule ID that caused rejection
    reason: Optional[str]    # Human-readable rejection reason
```

**Example PASSED result:**
```json
{
  "status": "PASSED",
  "rules": [
    {"rule_id": "R01", "rule_name": "symbol_check", "status": "PASSED", "message": "Symbol TCS is valid"},
    {"rule_id": "R02", "rule_name": "quantity_check", "status": "PASSED", "message": "Quantity 50 is valid"},
    {"rule_id": "R04", "rule_name": "cash_check", "status": "PASSED", "message": "Sufficient cash ₹8,07,500"}
  ],
  "rejected_by": null,
  "reason": null
}
```

**Example REJECTED result:**
```json
{
  "status": "REJECTED",
  "rules": [
    {"rule_id": "R01", "rule_name": "symbol_check", "status": "PASSED"},
    {"rule_id": "R06", "rule_name": "order_value_check", "status": "REJECTED",
     "message": "Order value ₹7,00,000 exceeds maximum ₹5,00,000",
     "details": {"requested": 700000, "limit": 500000}}
  ],
  "rejected_by": "R06",
  "reason": "Maximum order value exceeded. Allowed: ₹5,00,000, Requested: ₹7,00,000"
}
```

---

## Risk Configuration

Risk limits are configurable via environment variables or the `risk_rules` database table:

| Variable | Default | Description |
|----------|---------|-------------|
| `RISK_MAX_ORDER_VALUE` | 500000 | Max single order value (₹) |
| `RISK_MAX_QUANTITY` | 10000 | Max shares per order |
| `RISK_MAX_DAILY_LOSS` | -100000 | Daily loss limit (₹) |
| `RISK_MAX_POSITION_PCT` | 0.40 | Max portfolio allocation per symbol |
| `RISK_MAX_PRICE_DEVIATION` | 0.20 | Max limit price deviation from market |

---

## Adding New Rules

To add a risk rule:

1. Add a new method to `RiskEngine` in `backend/app/risk/engine.py`
2. Call it in the `evaluate()` method
3. Document it in this file
4. Add a test case in `backend/tests/unit/test_risk_engine.py`
