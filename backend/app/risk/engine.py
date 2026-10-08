"""
Deterministic Risk Engine.

Evaluates orders against a set of hardcoded rules.
No LLM involvement — purely algorithmic.

Rules:
  R01 - Symbol check
  R02 - Quantity check
  R03 - Price check (limit orders)
  R04 - Cash check (BUY)
  R05 - Holdings check (SELL)
  R06 - Order value check
  R07 - Position exposure check
  R08 - Daily loss check
"""
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Optional

from app.config import settings


@dataclass
class RuleResult:
    rule_id: str
    rule_name: str
    status: str  # PASSED | REJECTED
    message: str
    details: dict = field(default_factory=dict)


@dataclass
class RiskResult:
    status: str  # PASSED | REJECTED
    rules: list[RuleResult] = field(default_factory=list)
    rejected_by: Optional[str] = None
    reason: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "status": self.status,
            "rules": [
                {
                    "rule_id": r.rule_id,
                    "rule_name": r.rule_name,
                    "status": r.status,
                    "message": r.message,
                    "details": r.details,
                }
                for r in self.rules
            ],
            "rejected_by": self.rejected_by,
            "reason": self.reason,
        }


class RiskEngine:
    """
    Evaluates trading orders against deterministic risk rules.
    Called after tool validation, before order proposal creation.
    """

    def __init__(
        self,
        max_order_value: float = settings.RISK_MAX_ORDER_VALUE,
        max_quantity: int = settings.RISK_MAX_QUANTITY,
        max_daily_loss: float = settings.RISK_MAX_DAILY_LOSS,
        max_position_pct: float = settings.RISK_MAX_POSITION_PCT,
        max_price_deviation: float = settings.RISK_MAX_PRICE_DEVIATION,
    ):
        self.max_order_value = max_order_value
        self.max_quantity = max_quantity
        self.max_daily_loss = max_daily_loss
        self.max_position_pct = max_position_pct
        self.max_price_deviation = max_price_deviation

    def evaluate(
        self,
        *,
        side: str,
        symbol: str,
        quantity: int,
        order_type: str,
        current_price: float,
        available_cash: float,
        current_holdings: int,
        portfolio_value: float,
        daily_pnl: float,
        limit_price: Optional[float] = None,
        active_symbols: Optional[list[str]] = None,
    ) -> RiskResult:
        """
        Run all risk rules against the order parameters.
        Returns on first rejection (fail-fast).
        """
        rules: list[RuleResult] = []

        def add_pass(rule_id: str, name: str, message: str, details: dict | None = None) -> None:
            rules.append(RuleResult(rule_id, name, "PASSED", message, details or {}))

        def reject(rule_id: str, name: str, message: str, details: dict | None = None) -> RiskResult:
            rule = RuleResult(rule_id, name, "REJECTED", message, details or {})
            rules.append(rule)
            return RiskResult(status="REJECTED", rules=rules, rejected_by=rule_id, reason=message)

        estimated_value = current_price * quantity

        # R01 — Symbol Check
        if active_symbols is not None and symbol not in active_symbols:
            return reject(
                "R01", "symbol_check",
                f"'{symbol}' is not a supported instrument. "
                f"Supported: {', '.join(sorted(active_symbols))}",
                {"symbol": symbol}
            )
        add_pass("R01", "symbol_check", f"Symbol '{symbol}' is valid")

        # R02 — Quantity Check
        if quantity <= 0:
            return reject("R02", "quantity_check", "Quantity must be greater than 0",
                          {"quantity": quantity})
        if quantity > self.max_quantity:
            return reject(
                "R02", "quantity_check",
                f"Quantity {quantity:,} exceeds maximum allowed {self.max_quantity:,}",
                {"requested": quantity, "max": self.max_quantity}
            )
        add_pass("R02", "quantity_check", f"Quantity {quantity:,} is within limits")

        # R03 — Price Check (limit orders)
        if order_type == "LIMIT":
            if limit_price is None or limit_price <= 0:
                return reject("R03", "price_check", "Limit price must be a positive number",
                              {"limit_price": limit_price})
            deviation = abs(limit_price - current_price) / current_price
            if deviation > self.max_price_deviation:
                return reject(
                    "R03", "price_check",
                    f"Limit price ₹{limit_price:,.2f} deviates {deviation * 100:.1f}% from "
                    f"current price ₹{current_price:,.2f}. Maximum deviation: {self.max_price_deviation * 100:.0f}%",
                    {"limit_price": limit_price, "current_price": current_price,
                     "deviation_pct": round(deviation * 100, 2), "max_deviation_pct": self.max_price_deviation * 100}
                )
            add_pass("R03", "price_check", f"Limit price ₹{limit_price:,.2f} is within acceptable range")
        else:
            add_pass("R03", "price_check", "Price check not applicable for market orders")

        # R04 — Cash Check (BUY only)
        if side == "BUY":
            # Estimate with fees (0.155%)
            estimated_with_fees = estimated_value * 1.00155
            if estimated_with_fees > available_cash:
                return reject(
                    "R04", "cash_check",
                    f"Insufficient cash. Required: ₹{estimated_with_fees:,.2f} "
                    f"(incl. fees), Available: ₹{available_cash:,.2f}",
                    {"required": round(estimated_with_fees, 2), "available": round(available_cash, 2)}
                )
            add_pass("R04", "cash_check",
                     f"Sufficient cash: ₹{available_cash:,.2f} available, "
                     f"₹{estimated_with_fees:,.2f} required")
        else:
            add_pass("R04", "cash_check", "Cash check not applicable for SELL orders")

        # R05 — Holdings Check (SELL only)
        if side == "SELL":
            if quantity > current_holdings:
                return reject(
                    "R05", "holdings_check",
                    f"Insufficient holdings. Trying to sell {quantity:,} {symbol}, "
                    f"but only hold {current_holdings:,} shares",
                    {"requested": quantity, "held": current_holdings}
                )
            if current_holdings == 0:
                return reject(
                    "R05", "holdings_check",
                    f"No {symbol} position. Cannot sell what you don't hold.",
                    {"requested": quantity, "held": 0}
                )
            add_pass("R05", "holdings_check",
                     f"Holdings sufficient: selling {quantity:,} of {current_holdings:,} held")
        else:
            add_pass("R05", "holdings_check", "Holdings check not applicable for BUY orders")

        # R06 — Order Value Check
        if estimated_value > self.max_order_value:
            return reject(
                "R06", "order_value_check",
                f"Order value ₹{estimated_value:,.0f} exceeds maximum allowed ₹{self.max_order_value:,.0f}. "
                f"Consider reducing quantity.",
                {"estimated_value": round(estimated_value, 2), "max_order_value": self.max_order_value}
            )
        add_pass("R06", "order_value_check",
                 f"Order value ₹{estimated_value:,.0f} within limit ₹{self.max_order_value:,.0f}")

        # R07 — Position Exposure Check
        if portfolio_value > 0:
            # For BUY: calculate what new position value would be
            current_position_value = current_holdings * current_price
            if side == "BUY":
                new_position_value = current_position_value + estimated_value
            else:
                new_position_value = current_position_value - estimated_value

            new_exposure = new_position_value / portfolio_value if portfolio_value > 0 else 0
            if new_exposure > self.max_position_pct:
                return reject(
                    "R07", "position_exposure_check",
                    f"This order would give {symbol} a {new_exposure * 100:.1f}% portfolio allocation, "
                    f"exceeding the {self.max_position_pct * 100:.0f}% limit.",
                    {
                        "new_exposure_pct": round(new_exposure * 100, 2),
                        "max_exposure_pct": self.max_position_pct * 100,
                        "new_position_value": round(new_position_value, 2),
                        "portfolio_value": round(portfolio_value, 2),
                    }
                )
            add_pass("R07", "position_exposure_check",
                     f"{symbol} allocation would be {new_exposure * 100:.1f}% (limit: {self.max_position_pct * 100:.0f}%)")
        else:
            add_pass("R07", "position_exposure_check", "Portfolio exposure check skipped (no portfolio)")

        # R08 — Daily Loss Check
        if daily_pnl < self.max_daily_loss:
            return reject(
                "R08", "daily_loss_check",
                f"Daily loss limit reached. Today's P&L: ₹{daily_pnl:,.0f}, "
                f"Limit: ₹{self.max_daily_loss:,.0f}. No new orders allowed today.",
                {"daily_pnl": round(daily_pnl, 2), "limit": self.max_daily_loss}
            )
        add_pass("R08", "daily_loss_check", f"Daily P&L ₹{daily_pnl:,.0f} within daily loss limit")

        return RiskResult(status="PASSED", rules=rules)


# Singleton instance
risk_engine = RiskEngine()
