"""
Demo data seeder for AI Trading Copilot.
Populates demo user, account, instruments, initial holdings, and sample audit trail.
"""
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user import User
from app.models.account import Account
from app.models.instrument import Instrument
from app.models.position import Position
from app.models.order import Order, OrderStatus, OrderSide, OrderType
from app.models.execution import Execution
from app.models.transaction import Transaction
from app.models.audit_log import AuditLog
from app.models.market_tick import MarketTick
from app.trading.simulator import INSTRUMENT_CONFIG, simulator


DEMO_USER_EMAIL = "demo@tradingcopilot.ai"

INITIAL_POSITIONS = [
    {"symbol": "TCS", "quantity": 50, "avg_price": Decimal("3450.00")},
    {"symbol": "INFY", "quantity": 100, "avg_price": Decimal("1485.00")},
    {"symbol": "RELIANCE", "quantity": 30, "avg_price": Decimal("2800.00")},
    {"symbol": "HDFCBANK", "quantity": 40, "avg_price": Decimal("1650.00")},
]


async def seed_database(db: AsyncSession) -> None:
    """Idempotently seed the database with initial demo data."""
    # 1. Check if instruments already exist
    inst_result = await db.execute(select(Instrument))
    instruments = inst_result.scalars().all()

    inst_map = {inst.symbol: inst for inst in instruments}

    if not instruments:
        for sym, cfg in INSTRUMENT_CONFIG.items():
            inst = Instrument(
                symbol=sym,
                name=cfg["name"],
                exchange=cfg.get("exchange", "NSE"),
                lot_size=cfg.get("lot_size", 1),
                is_active=True,
            )
            db.add(inst)
            inst_map[sym] = inst
        await db.flush()

    # Seed initial market ticks for each instrument
    now = datetime.now(timezone.utc)
    for sym, inst in inst_map.items():
        tick_check = await db.execute(
            select(MarketTick).where(MarketTick.instrument_id == inst.id).limit(1)
        )
        if not tick_check.scalar_one_or_none():
            price_data = simulator.get_tick(sym)
            tick = MarketTick(
                instrument_id=inst.id,
                price=Decimal(str(price_data.price)),
                bid=Decimal(str(price_data.bid)),
                ask=Decimal(str(price_data.ask)),
                volume=price_data.volume,
                change=Decimal(str(price_data.change)),
                change_pct=Decimal(str(price_data.change_pct)),
                timestamp=now,
            )
            db.add(tick)
    await db.flush()

    # 2. Check if demo user already exists
    user_result = await db.execute(select(User).where(User.email == DEMO_USER_EMAIL))
    user = user_result.scalar_one_or_none()

    if not user:
        user = User(
            email=DEMO_USER_EMAIL,
            name="Demo Trader",
            is_active=True,
        )
        db.add(user)
        await db.flush()

    # 3. Check Account
    acct_result = await db.execute(select(Account).where(Account.user_id == user.id))
    account = acct_result.scalar_one_or_none()

    if not account:
        account = Account(
            user_id=user.id,
            cash_balance=Decimal("807500.00"),
            realized_pnl=Decimal("12500.00"),
            daily_pnl_start=Decimal("1000000.00"),
        )
        db.add(account)
        await db.flush()

        # 4. Populate positions
        balance_tracker = Decimal("1000000.00")
        for pos_data in INITIAL_POSITIONS:
            sym = pos_data["symbol"]
            inst = inst_map.get(sym)
            if not inst:
                continue

            pos = Position(
                account_id=account.id,
                instrument_id=inst.id,
                quantity=pos_data["quantity"],
                avg_price=pos_data["avg_price"],
                realized_pnl=Decimal("0.00"),
            )
            db.add(pos)

            # Create corresponding historical order & execution
            order_cost = pos_data["avg_price"] * Decimal(str(pos_data["quantity"]))
            order = Order(
                account_id=account.id,
                instrument_id=inst.id,
                side=OrderSide.BUY,
                order_type=OrderType.MARKET,
                quantity=pos_data["quantity"],
                estimated_value=order_cost,
                status=OrderStatus.FILLED,
                risk_status="PASSED",
                risk_details={"status": "PASSED", "rules": []},
            )
            db.add(order)
            await db.flush()

            exec_record = Execution(
                order_id=order.id,
                execution_price=pos_data["avg_price"],
                execution_quantity=pos_data["quantity"],
                fees=Decimal("50.00"),
                total_value=order_cost,
                executed_at=now - timedelta(hours=2),
            )
            db.add(exec_record)
            await db.flush()

            balance_before = balance_tracker
            balance_tracker -= (order_cost + Decimal("50.00"))
            txn = Transaction(
                account_id=account.id,
                execution_id=exec_record.id,
                type="BUY_FILL",
                amount=-(order_cost + Decimal("50.00")),
                balance_before=balance_before,
                balance_after=balance_tracker,
                description=f"BUY {pos_data['quantity']} {sym} @ ₹{pos_data['avg_price']} (Initial Seed)",
            )
            db.add(txn)

        # 5. Add initial sample audit log entries
        sample_audit_1 = AuditLog(
            account_id=account.id,
            user_request="Show my portfolio positions and cash",
            interpreted_intent={"action": "QUERY_PORTFOLIO"},
            tool_used="get_positions",
            tool_args={},
            tool_result={"status": "SUCCESS", "count": 4},
            risk_result="N/A",
            user_approved=True,
            execution_result="N/A",
        )
        sample_audit_2 = AuditLog(
            account_id=account.id,
            user_request="Buy 50 TCS at market price",
            interpreted_intent={"action": "BUY", "symbol": "TCS", "quantity": 50},
            tool_used="create_order_proposal",
            tool_args={"action": "BUY", "symbol": "TCS", "quantity": 50},
            tool_result={"proposal_id": "demo-seed-1", "risk_status": "PASSED"},
            risk_result="PASSED",
            risk_details={"status": "PASSED", "reason": "All 8 risk rules verified"},
            user_approved=True,
            execution_result="FILLED",
        )
        db.add_all([sample_audit_1, sample_audit_2])

    await db.commit()
