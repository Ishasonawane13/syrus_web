"""Portfolio and account service — P&L calculations."""
from decimal import Decimal
from typing import Optional, List, Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.models.account import Account
from app.models.user import User
from app.models.position import Position
from app.models.instrument import Instrument
from app.trading.simulator import simulator


async def get_portfolio_value(db: AsyncSession, account: Account) -> Decimal:
    """Calculate current portfolio value from all positions × current prices."""
    result = await db.execute(
        select(Position, Instrument)
        .join(Instrument, Position.instrument_id == Instrument.id)
        .where(and_(Position.account_id == account.id, Position.quantity > 0))
    )
    rows = result.all()

    total = Decimal("0")
    for position, instrument in rows:
        price = simulator.get_price(instrument.symbol)
        total += Decimal(str(price)) * position.quantity

    return total


async def get_unrealized_pnl(db: AsyncSession, account: Account) -> Decimal:
    """Calculate total unrealized P&L across all open positions."""
    result = await db.execute(
        select(Position, Instrument)
        .join(Instrument, Position.instrument_id == Instrument.id)
        .where(and_(Position.account_id == account.id, Position.quantity > 0))
    )
    rows = result.all()

    total_unrealized = Decimal("0")
    for position, instrument in rows:
        current_price = Decimal(str(simulator.get_price(instrument.symbol)))
        unrealized = (current_price - position.avg_price) * position.quantity
        total_unrealized += unrealized

    return total_unrealized


async def get_daily_pnl(db: AsyncSession, account: Account) -> Decimal:
    """Calculate today's P&L vs the start-of-day snapshot."""
    portfolio_value = await get_portfolio_value(db, account)
    current_total = portfolio_value + account.cash_balance
    return current_total - account.daily_pnl_start


async def get_account_summary(db: AsyncSession, account: Account) -> Dict[str, Any]:
    """Returns complete account summary matching API spec."""
    portfolio_value = await get_portfolio_value(db, account)
    unrealized_pnl = await get_unrealized_pnl(db, account)
    daily_pnl = await get_daily_pnl(db, account)
    total_value = account.cash_balance + portfolio_value

    daily_pnl_pct = 0.0
    if account.daily_pnl_start > 0:
        daily_pnl_pct = float(daily_pnl / account.daily_pnl_start * 100)

    # Fetch user email
    user_res = await db.execute(select(User).where(User.id == account.user_id))
    user = user_res.scalar_one_or_none()
    email = user.email if user else "demo@tradingcopilot.ai"

    return {
        "id": account.id,
        "user_email": email,
        "cash_balance": float(account.cash_balance),
        "portfolio_value": float(portfolio_value),
        "total_value": float(total_value),
        "available_cash": float(account.cash_balance),
        "realized_pnl": float(account.realized_pnl),
        "unrealized_pnl": float(unrealized_pnl),
        "daily_pnl": float(daily_pnl),
        "daily_pnl_pct": round(daily_pnl_pct, 4),
        "total_pnl": float(account.realized_pnl + unrealized_pnl),
    }


async def get_all_positions(db: AsyncSession, account: Account) -> Dict[str, List[Dict[str, Any]]]:
    """Returns all positions wrapped in positions dict."""
    result = await db.execute(
        select(Position, Instrument)
        .join(Instrument, Position.instrument_id == Instrument.id)
        .where(and_(Position.account_id == account.id, Position.quantity > 0))
        .order_by(Position.updated_at.desc())
    )
    rows = result.all()

    portfolio_value = await get_portfolio_value(db, account)
    total_value = account.cash_balance + portfolio_value

    positions = []
    for position, instrument in rows:
        current_price = simulator.get_price(instrument.symbol)
        market_value = current_price * position.quantity
        unrealized = (current_price - float(position.avg_price)) * position.quantity
        unrealized_pct = (
            unrealized / (float(position.avg_price) * position.quantity) * 100
            if position.avg_price > 0 else 0.0
        )
        allocation_pct = (market_value / float(total_value) * 100) if total_value > 0 else 0.0

        positions.append({
            "symbol": instrument.symbol,
            "name": instrument.name,
            "quantity": position.quantity,
            "avg_price": float(position.avg_price),
            "current_price": round(current_price, 2),
            "market_value": round(market_value, 2),
            "unrealized_pnl": round(unrealized, 2),
            "unrealized_pnl_pct": round(unrealized_pct, 4),
            "allocation_pct": round(allocation_pct, 4),
        })

    return {"positions": positions}


async def get_position_for_symbol(
    db: AsyncSession, account: Account, symbol: str
) -> Optional[Dict[str, Any]]:
    """Returns position details for a specific instrument symbol."""
    result = await db.execute(
        select(Position, Instrument)
        .join(Instrument, Position.instrument_id == Instrument.id)
        .where(
            and_(
                Position.account_id == account.id,
                Instrument.symbol == symbol.upper(),
                Position.quantity > 0,
            )
        )
    )
    row = result.first()
    if not row:
        return None

    position, instrument = row
    current_price = simulator.get_price(instrument.symbol)
    market_value = current_price * position.quantity
    unrealized = (current_price - float(position.avg_price)) * position.quantity
    unrealized_pct = (
        unrealized / (float(position.avg_price) * position.quantity) * 100
        if position.avg_price > 0 else 0.0
    )

    portfolio_value = await get_portfolio_value(db, account)
    total_value = account.cash_balance + portfolio_value
    allocation_pct = (market_value / float(total_value) * 100) if total_value > 0 else 0.0

    return {
        "symbol": instrument.symbol,
        "name": instrument.name,
        "quantity": position.quantity,
        "avg_price": float(position.avg_price),
        "current_price": round(current_price, 2),
        "market_value": round(market_value, 2),
        "unrealized_pnl": round(unrealized, 2),
        "unrealized_pnl_pct": round(unrealized_pct, 4),
        "allocation_pct": round(allocation_pct, 4),
    }


async def get_pnl_summary(db: AsyncSession, account: Account) -> Dict[str, Any]:
    """Returns P&L summary."""
    summary = await get_account_summary(db, account)
    return {
        "realized_pnl": summary["realized_pnl"],
        "unrealized_pnl": summary["unrealized_pnl"],
        "daily_pnl": summary["daily_pnl"],
        "daily_pnl_pct": summary["daily_pnl_pct"],
        "total_pnl": summary["total_pnl"],
    }


# Backwards compatibility aliases
get_full_account_summary = get_account_summary
get_positions_with_pnl = get_all_positions
