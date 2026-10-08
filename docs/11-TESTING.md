# 11 — Testing

## Overview

Tests are organized into unit tests and integration tests.

**Framework:** Pytest  
**Location:** `backend/tests/`

---

## Running Tests

```bash
cd backend
pip install -r requirements.txt

# All tests
pytest tests/ -v

# Unit tests only
pytest tests/unit/ -v

# Integration tests only
pytest tests/integration/ -v

# With coverage
pytest tests/ --cov=app --cov-report=html
open htmlcov/index.html

# Specific file
pytest tests/unit/test_risk_engine.py -v

# Specific test
pytest tests/unit/test_risk_engine.py::test_insufficient_cash_rejected -v
```

---

## Test Structure

```
backend/tests/
├── conftest.py              # Fixtures, test DB setup
├── unit/
│   ├── test_risk_engine.py      # Risk rule tests
│   ├── test_trading_engine.py   # Order execution tests
│   ├── test_market_simulator.py # Price simulation tests
│   ├── test_ai_tools.py         # Tool validation tests
│   └── test_portfolio_service.py # P&L calculation tests
└── integration/
    ├── test_account_api.py      # Account endpoint tests
    ├── test_orders_api.py       # Order lifecycle tests
    ├── test_ai_chat_api.py      # AI chat endpoint tests
    └── test_execution_flow.py   # End-to-end order flow
```

---

## Critical Test Cases

### Account Tests

```python
# test_account_api.py

def test_get_account_returns_balance():
    """Account endpoint returns correct cash balance."""
    
def test_get_positions_returns_holdings():
    """Positions endpoint returns seeded demo positions."""
    
def test_pnl_calculation_correct():
    """P&L is correctly calculated from positions and market prices."""
```

### Risk Engine Tests

```python
# test_risk_engine.py

def test_valid_buy_order_passes():
    """A well-formed BUY order within limits passes all rules."""

def test_invalid_symbol_rejected():
    """Unknown symbol is rejected by R01."""

def test_zero_quantity_rejected():
    """Zero quantity is rejected by R02."""

def test_negative_quantity_rejected():
    """Negative quantity is rejected by R02."""

def test_insufficient_cash_rejected():
    """BUY order with insufficient cash is rejected by R04."""

def test_exact_cash_boundary_passes():
    """BUY order with exactly available cash passes R04."""

def test_insufficient_holdings_rejected():
    """SELL order for more shares than held is rejected by R05."""

def test_sell_no_position_rejected():
    """SELL order with zero holdings is rejected by R05."""

def test_max_order_value_exceeded_rejected():
    """Order exceeding max value is rejected by R06."""

def test_max_order_value_exact_boundary_passes():
    """Order exactly at max value limit passes R06."""

def test_position_exposure_exceeded_rejected():
    """Order causing >40% portfolio concentration is rejected by R07."""

def test_daily_loss_limit_rejected():
    """Order placed when daily loss exceeds limit is rejected by R08."""
```

### Trading Engine Tests

```python
# test_trading_engine.py

def test_market_buy_updates_cash():
    """Market BUY reduces cash by correct amount."""

def test_market_buy_creates_position():
    """Market BUY creates position with correct quantity and avg price."""

def test_market_sell_increases_cash():
    """Market SELL increases cash by correct amount."""

def test_market_sell_reduces_position():
    """Market SELL reduces position quantity."""

def test_sell_all_closes_position():
    """Selling all shares sets position quantity to 0."""

def test_avg_price_calculation_on_additional_buy():
    """Buying more shares updates average price correctly."""

def test_realized_pnl_on_sell():
    """Selling at profit records correct realized P&L."""

def test_realized_pnl_loss_on_sell():
    """Selling at a loss records negative realized P&L."""

def test_fees_deducted_correctly():
    """Brokerage fees are deducted from cash."""

def test_order_status_updated_to_filled():
    """Executed order status changes to FILLED."""

def test_execution_record_created():
    """Execution record is created with correct details."""

def test_transaction_record_created():
    """Transaction record is created with balance before/after."""
```

### Safety Tests (Critical)

```python
# test_orders_api.py

def test_pending_approval_order_executes():
    """Order in PENDING_APPROVAL status can be executed."""

def test_rejected_order_cannot_execute():
    """Order in REJECTED status cannot be executed — returns 400."""

def test_cancelled_order_cannot_execute():
    """Cancelled order cannot be executed — returns 400."""

def test_filled_order_cannot_execute_again():
    """Already FILLED order cannot be re-executed."""

def test_execute_nonexistent_order_returns_404():
    """Executing a fake order ID returns 404."""

def test_execute_requires_correct_account():
    """Order belonging to another account cannot be executed."""

# test_ai_chat_api.py

def test_ai_cannot_execute_directly():
    """
    The AI chat endpoint never directly executes orders.
    Even if asked, execution requires the separate /orders/{id}/execute endpoint.
    """

def test_ai_tool_validation_rejects_negative_quantity():
    """AI tool call with negative quantity is rejected server-side."""

def test_ai_tool_validation_rejects_unknown_symbol():
    """AI tool call with unknown symbol is rejected server-side."""

def test_ai_tool_validation_rejects_unknown_tool():
    """AI invoking a tool not in the whitelist is rejected."""
```

### AI Tests

```python
# test_ai_chat_api.py

def test_account_question_returns_data():
    """'What is my cash balance?' returns account data."""

def test_market_price_question_returns_price():
    """'What is TCS price?' returns simulated price data."""

def test_buy_request_creates_proposal():
    """'Buy 50 TCS' creates a PENDING_APPROVAL order proposal."""

def test_rejected_buy_shows_reason():
    """Oversized buy request shows rejection reason to user."""

def test_sell_question_creates_proposal():
    """'Sell 20 INFY' creates a PENDING_APPROVAL sell proposal."""
```

---

## Test Fixtures

```python
# conftest.py

@pytest.fixture
def test_db():
    """In-memory SQLite database for tests."""
    
@pytest.fixture
def demo_account(test_db):
    """Returns a seeded demo account with known state."""

@pytest.fixture
def demo_positions(test_db, demo_account):
    """Returns standard test positions (TCS:50, INFY:100)."""

@pytest.fixture
def risk_engine():
    """Returns RiskEngine with test configuration."""

@pytest.fixture  
def trading_engine(test_db):
    """Returns TradingEngine with test DB."""
```

---

## Test Data

Tests use an isolated in-memory SQLite database (not the real PostgreSQL).

Standard test account state:
- Cash: ₹5,00,000
- TCS position: 50 shares @ ₹3,450 (value: ₹1,72,500)
- INFY position: 100 shares @ ₹1,485 (value: ₹1,48,500)
- Total portfolio: ₹8,21,000

This state is reproducible for all tests.

---

## Coverage Goals

| Module | Target Coverage |
|--------|----------------|
| Risk Engine | 100% |
| Trading Engine | 95% |
| API Routes | 85% |
| AI Tools | 90% |
| Services | 85% |
| Market Simulator | 80% |
