"""Order service — create and manage order proposals."""
import uuid
from decimal import Decimal
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.models.order import Order, OrderStatus, OrderSide, OrderType
from app.models.instrument import Instrument
from app.models.position import Position
from app.models.account import Account
from app.risk.engine import risk_engine, RiskResult
from app.services.portfolio_service import get_portfolio_value, get_daily_pnl
from app.trading.simulator import simulator


async def create_order_proposal(
    db: AsyncSession,
    account: Account,
    symbol: str,
    side: str,
    quantity: int,
    order_type: str,
    limit_price: Optional[float] = None,
) -> tuple[Order, RiskResult]:
    """
    Create an order proposal after risk validation.
    
    Returns (order, risk_result).
    Order status = PENDING_APPROVAL if risk passed, REJECTED if not.
    DOES NOT execute anything.
    """
    # Fetch instrument
    instr_result = await db.execute(
        select(Instrument).where(
            and_(Instrument.symbol == symbol.upper(), Instrument.is_active == True)
        )
    )
    instrument = instr_result.scalar_one_or_none()

    # Get active symbols for risk check
    sym_result = await db.execute(
        select(Instrument.symbol).where(Instrument.is_active == True)
    )
    active_symbols = [row[0] for row in sym_result.all()]

    # Get current price
    current_price = simulator.get_price(symbol.upper()) if instrument else 0.0

    # Get current holdings for SELL check
    current_holdings = 0
    if instrument:
        pos_result = await db.execute(
            select(Position).where(
                and_(
                    Position.account_id == account.id,
                    Position.instrument_id == instrument.id,
                )
            )
        )
        pos = pos_result.scalar_one_or_none()
        current_holdings = pos.quantity if pos else 0

    # Get portfolio metrics for risk checks
    portfolio_value = float(await get_portfolio_value(db, account))
    daily_pnl = float(await get_daily_pnl(db, account))
    total_value = portfolio_value + float(account.cash_balance)

    # Run risk engine
    risk_result = risk_engine.evaluate(
        side=side.upper(),
        symbol=symbol.upper(),
        quantity=quantity,
        order_type=order_type.upper(),
        current_price=current_price,
        available_cash=float(account.cash_balance),
        current_holdings=current_holdings,
        portfolio_value=total_value,
        daily_pnl=daily_pnl,
        limit_price=limit_price,
        active_symbols=active_symbols,
    )

    # Determine order status
    status = OrderStatus.PENDING_APPROVAL if risk_result.status == "PASSED" else OrderStatus.REJECTED
    estimated_value = Decimal(str(current_price * quantity))

    order = Order(
        account_id=account.id,
        instrument_id=instrument.id if instrument else "UNKNOWN",
        side=side.upper(),
        order_type=order_type.upper(),
        quantity=quantity,
        limit_price=Decimal(str(limit_price)) if limit_price else None,
        estimated_value=estimated_value,
        status=status,
        risk_status=risk_result.status,
        risk_details=risk_result.to_dict(),
    )
    db.add(order)
    await db.commit()
    await db.refresh(order)

    return order, risk_result


async def get_orders_for_account(
    db: AsyncSession,
    account_id: str,
    status_filter: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[dict], int]:
    """Get orders with instrument details."""
    query = (
        select(Order, Instrument)
        .join(Instrument, Order.instrument_id == Instrument.id)
        .where(Order.account_id == account_id)
    )
    if status_filter:
        query = query.where(Order.status == status_filter.upper())

    query = query.order_by(Order.created_at.desc()).offset(offset).limit(limit)
    result = await db.execute(query)
    rows = result.all()

    orders = []
    for order, instrument in rows:
        order_dict = {
            "id": order.id,
            "symbol": instrument.symbol,
            "name": instrument.name,
            "side": order.side,
            "order_type": order.order_type,
            "quantity": order.quantity,
            "limit_price": float(order.limit_price) if order.limit_price else None,
            "estimated_value": float(order.estimated_value),
            "status": order.status,
            "risk_status": order.risk_status,
            "risk_details": order.risk_details,
            "created_at": order.created_at.isoformat(),
            "updated_at": order.updated_at.isoformat(),
        }
        orders.append(order_dict)

    return orders, len(orders)
