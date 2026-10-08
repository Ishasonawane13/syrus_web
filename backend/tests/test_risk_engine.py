"""Unit tests for deterministic Risk Engine (all 8 rules)."""
import pytest
from app.risk.engine import RiskEngine


@pytest.fixture
def risk():
    return RiskEngine()


def test_rule_1_symbol_check_pass(risk):
    res = risk.evaluate(
        side="BUY",
        symbol="TCS",
        quantity=10,
        order_type="MARKET",
        current_price=3500.0,
        available_cash=100000.0,
        current_holdings=0,
        portfolio_value=1000000.0,
        daily_pnl=0.0,
        active_symbols=["TCS", "INFY", "RELIANCE"],
    )
    assert res.status == "PASSED"


def test_rule_1_symbol_check_fail(risk):
    res = risk.evaluate(
        side="BUY",
        symbol="UNKNOWN_STOCK",
        quantity=10,
        order_type="MARKET",
        current_price=100.0,
        available_cash=100000.0,
        current_holdings=0,
        portfolio_value=1000000.0,
        daily_pnl=0.0,
        active_symbols=["TCS", "INFY"],
    )
    assert res.status == "REJECTED"
    assert res.rejected_by == "R01"


def test_rule_2_quantity_check_zero_or_negative(risk):
    res = risk.evaluate(
        side="BUY",
        symbol="TCS",
        quantity=0,
        order_type="MARKET",
        current_price=3500.0,
        available_cash=100000.0,
        current_holdings=0,
        portfolio_value=1000000.0,
        daily_pnl=0.0,
        active_symbols=["TCS"],
    )
    assert res.status == "REJECTED"
    assert res.rejected_by == "R02"


def test_rule_3_limit_price_deviation(risk):
    # Current price 3500, limit price 5000 (>20% deviation)
    res = risk.evaluate(
        side="BUY",
        symbol="TCS",
        quantity=10,
        order_type="LIMIT",
        current_price=3500.0,
        available_cash=100000.0,
        current_holdings=0,
        portfolio_value=1000000.0,
        daily_pnl=0.0,
        limit_price=5000.0,
        active_symbols=["TCS"],
    )
    assert res.status == "REJECTED"
    assert res.rejected_by == "R03"


def test_rule_4_insufficient_cash(risk):
    # Required: 50 * 3500 = 175,000, Available: 50,000
    res = risk.evaluate(
        side="BUY",
        symbol="TCS",
        quantity=50,
        order_type="MARKET",
        current_price=3500.0,
        available_cash=50000.0,
        current_holdings=0,
        portfolio_value=1000000.0,
        daily_pnl=0.0,
        active_symbols=["TCS"],
    )
    assert res.status == "REJECTED"
    assert res.rejected_by == "R04"


def test_rule_5_insufficient_holdings_sell(risk):
    # Try to sell 50 when holding only 20
    res = risk.evaluate(
        side="SELL",
        symbol="TCS",
        quantity=50,
        order_type="MARKET",
        current_price=3500.0,
        available_cash=100000.0,
        current_holdings=20,
        portfolio_value=1000000.0,
        daily_pnl=0.0,
        active_symbols=["TCS"],
    )
    assert res.status == "REJECTED"
    assert res.rejected_by == "R05"


def test_rule_6_max_order_value_exceeded(risk):
    # 200 * 3500 = 700,000 > MAX_ORDER_VALUE (500,000)
    res = risk.evaluate(
        side="BUY",
        symbol="TCS",
        quantity=200,
        order_type="MARKET",
        current_price=3500.0,
        available_cash=1000000.0,
        current_holdings=0,
        portfolio_value=2000000.0,
        daily_pnl=0.0,
        active_symbols=["TCS"],
    )
    assert res.status == "REJECTED"
    assert res.rejected_by == "R06"


def test_rule_7_position_exposure_exceeded(risk):
    # New position value 500,000 on 1,000,000 portfolio = 50% > 40% max
    res = risk.evaluate(
        side="BUY",
        symbol="TCS",
        quantity=100,
        order_type="MARKET",
        current_price=3500.0,
        available_cash=500000.0,
        current_holdings=50,  # existing 50*3500 = 175,000 + 350,000 = 525,000 / 1,000,000 = 52.5%
        portfolio_value=1000000.0,
        daily_pnl=0.0,
        active_symbols=["TCS"],
    )
    assert res.status == "REJECTED"
    assert res.rejected_by == "R07"


def test_rule_8_daily_loss_limit(risk):
    # Daily loss = -150,000 < limit (-100,000)
    res = risk.evaluate(
        side="BUY",
        symbol="TCS",
        quantity=10,
        order_type="MARKET",
        current_price=3500.0,
        available_cash=500000.0,
        current_holdings=0,
        portfolio_value=1000000.0,
        daily_pnl=-150000.0,
        active_symbols=["TCS"],
    )
    assert res.status == "REJECTED"
    assert res.rejected_by == "R08"
