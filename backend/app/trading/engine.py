"""
Paper Trading Engine.

Handles order execution, position updates, P&L calculation.
All operations are paper trades — no real money or real exchanges.
"""
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.models.order import Order, OrderStatus, OrderSide
from app.models.execution import Execution
from app.models.position import Position
from app.models.transaction import Transaction
from app.models.account import Account
from app.models.instrument import Instrument
from app.trading.simulator import simulator


# Fee schedule (realistic Indian market rates)
BROKERAGE_RATE = Decimal("0.0005")    # 0.05%
MIN_BROKERAGE = Decimal("20.00")       # ₹20 minimum
STT_RATE = Decimal("0.001")           # 0.1% STT
EXCHANGE_FEE_RATE = Decimal("0.0000325")  # 0.00325% NSE fee


def calculate_fees(trade_value: Decimal, side: str) -> Decimal:
    """Calculate realistic brokerage fees for Indian markets."""
    brokerage = max(trade_value * BROKERAGE_RATE, MIN_BROKERAGE)
    stt = trade_value * STT_RATE
    exchange_fee = trade_value * EXCHANGE_FEE_RATE
    total = brokerage + stt + exchange_fee
    return total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


@dataclass
class ExecutionResult:
    order_id: str
    status: str
    execution_price: float
    execution_quantity: int
    fees: float
    cash_after: float
    message: str
    execution_id: Optional[str] = None


class TradingEngine:
    """
    Paper trading engine.
    
    IMPORTANT SAFETY PROPERTIES:
    - Only processes orders with status=PENDING_APPROVAL
    - Verifies order belongs to the account
    - All changes are within a single DB transaction (atomic)
    - Audit trail created for every execution
    """

    async def execute_approved_order(
        self,
        db: AsyncSession,
        order_id: str,
        account_id: str,
    ) -> ExecutionResult:
        """
        Execute a paper trade for an approved order.
        
        Safety checks:
        1. Order must exist
        2. Order must belong to account_id
        3. Order status must be PENDING_APPROVAL
        4. Cash/holdings re-verified at execution time
        """
        # 1. Fetch and verify order
        result = await db.execute(
            select(Order).where(
                and_(Order.id == order_id, Order.account_id == account_id)
            )
        )
        order = result.scalar_one_or_none()

        if order is None:
            raise ValueError(f"Order {order_id} not found for account {account_id}")

        if order.status != OrderStatus.PENDING_APPROVAL:
            raise ValueError(
                f"Order {order_id} cannot be executed. "
                f"Status: {order.status} (expected: PENDING_APPROVAL)"
            )

        # 2. Fetch account
        acct_result = await db.execute(select(Account).where(Account.id == account_id))
        account = acct_result.scalar_one_or_none()
        if account is None:
            raise ValueError(f"Account {account_id} not found")

        # 3. Fetch instrument
        instr_result = await db.execute(
            select(Instrument).where(Instrument.id == order.instrument_id)
        )
        instrument = instr_result.scalar_one_or_none()
        if instrument is None:
            raise ValueError(f"Instrument {order.instrument_id} not found")

        # 4. Get execution price from simulator/redis
        from app.services.market_service import get_instrument_price
        data = await get_instrument_price(instrument.symbol)
        raw_price = data["price"] if data else 0.0
        exec_price = Decimal(str(simulator.apply_slippage(raw_price, order.quantity, order.side)))
        quantity = order.quantity
        trade_value = exec_price * quantity
        fees = calculate_fees(trade_value, order.side)

        # 5. Re-verify cash/holdings at execution time
        if order.side == OrderSide.BUY:
            total_cost = trade_value + fees
            if total_cost > account.cash_balance:
                order.status = OrderStatus.CANCELLED
                await db.commit()
                raise ValueError(
                    f"Insufficient cash at execution time. "
                    f"Required: ₹{total_cost:.2f}, Available: ₹{account.cash_balance:.2f}"
                )
        else:  # SELL
            pos = await self._get_position(db, account_id, order.instrument_id)
            if pos is None or pos.quantity < quantity:
                order.status = OrderStatus.CANCELLED
                await db.commit()
                raise ValueError(
                    f"Insufficient holdings at execution time. "
                    f"Requested: {quantity}, Held: {pos.quantity if pos else 0}"
                )

        # 6. Create execution record
        execution = Execution(
            order_id=order.id,
            execution_price=exec_price,
            execution_quantity=quantity,
            fees=fees,
            total_value=trade_value,
            executed_at=datetime.now(timezone.utc),
        )
        db.add(execution)

        # 7. Update position
        await self._update_position(db, account, instrument, order.side, quantity, exec_price)

        # 8. Update account cash
        balance_before = account.cash_balance
        if order.side == OrderSide.BUY:
            account.cash_balance -= trade_value + fees
        else:
            account.cash_balance += trade_value - fees

        # 9. Create transaction record
        txn_type = "BUY_FILL" if order.side == OrderSide.BUY else "SELL_FILL"
        transaction = Transaction(
            account_id=account_id,
            execution_id=execution.id,
            type=txn_type,
            amount=-(trade_value + fees) if order.side == OrderSide.BUY else (trade_value - fees),
            balance_before=balance_before,
            balance_after=account.cash_balance,
            description=(
                f"{order.side} {quantity} {instrument.symbol} @ ₹{exec_price:.2f}"
                f" | Fees: ₹{fees:.2f}"
            ),
        )
        db.add(transaction)

        # 10. Update order status
        order.status = OrderStatus.FILLED
        order.updated_at = datetime.now(timezone.utc)

        await db.commit()
        await db.refresh(execution)

        return ExecutionResult(
            order_id=order_id,
            status=OrderStatus.FILLED,
            execution_price=float(exec_price),
            execution_quantity=quantity,
            fees=float(fees),
            cash_after=float(account.cash_balance),
            message=f"Order executed: {order.side} {quantity} {instrument.symbol} @ ₹{exec_price:.2f}",
            execution_id=execution.id,
        )

    async def cancel_order(
        self,
        db: AsyncSession,
        order_id: str,
        account_id: str,
    ) -> dict:
        """Cancel a PENDING_APPROVAL or OPEN order."""
        result = await db.execute(
            select(Order).where(
                and_(Order.id == order_id, Order.account_id == account_id)
            )
        )
        order = result.scalar_one_or_none()

        if order is None:
            raise ValueError(f"Order {order_id} not found")

        if order.status not in (OrderStatus.PENDING_APPROVAL, OrderStatus.OPEN):
            raise ValueError(
                f"Order {order_id} cannot be cancelled. Status: {order.status}"
            )

        order.status = OrderStatus.CANCELLED
        order.updated_at = datetime.now(timezone.utc)
        await db.commit()

        return {"order_id": order_id, "status": OrderStatus.CANCELLED, "message": "Order cancelled"}

    async def _get_position(
        self, db: AsyncSession, account_id: str, instrument_id: str
    ) -> Optional[Position]:
        """Fetch current position for an instrument."""
        result = await db.execute(
            select(Position).where(
                and_(
                    Position.account_id == account_id,
                    Position.instrument_id == instrument_id,
                )
            )
        )
        return result.scalar_one_or_none()

    async def _update_position(
        self,
        db: AsyncSession,
        account: Account,
        instrument: Instrument,
        side: str,
        quantity: int,
        exec_price: Decimal,
    ) -> None:
        """Update position with weighted average price calculation."""
        pos = await self._get_position(db, account.id, instrument.id)

        if side == OrderSide.BUY:
            if pos is None:
                pos = Position(
                    account_id=account.id,
                    instrument_id=instrument.id,
                    quantity=quantity,
                    avg_price=exec_price,
                    realized_pnl=Decimal("0"),
                )
                db.add(pos)
            else:
                # Weighted average price
                old_value = Decimal(str(pos.quantity)) * pos.avg_price
                new_value = Decimal(str(quantity)) * exec_price
                new_qty = pos.quantity + quantity
                pos.avg_price = (old_value + new_value) / Decimal(str(new_qty))
                pos.quantity = new_qty
        else:  # SELL
            if pos is None or pos.quantity < quantity:
                raise ValueError("Insufficient holdings for sell")

            # Calculate realized P&L
            realized = (exec_price - pos.avg_price) * Decimal(str(quantity))
            pos.realized_pnl += realized
            account.realized_pnl += realized
            pos.quantity -= quantity
            # avg_price stays the same after sell

        pos.updated_at = datetime.now(timezone.utc)


# Singleton instance
trading_engine = TradingEngine()
