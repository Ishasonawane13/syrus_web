"""FastAPI dependencies for user and account context."""
from decimal import Decimal
from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.user import User
from app.models.account import Account

DEMO_USER_EMAIL = "demo@tradingcopilot.ai"


async def get_demo_account(db: AsyncSession = Depends(get_db)) -> Account:
    """Retrieve or automatically initialize the demo account for MVP."""
    result = await db.execute(select(User).where(User.email == DEMO_USER_EMAIL))
    user = result.scalar_one_or_none()

    if not user:
        # Create user if not present
        user = User(email=DEMO_USER_EMAIL, name="Demo Trader", is_active=True)
        db.add(user)
        await db.flush()

        account = Account(
            user_id=user.id,
            cash_balance=Decimal("1000000.00"),
            realized_pnl=Decimal("0.00"),
            daily_pnl_start=Decimal("1000000.00"),
        )
        db.add(account)
        await db.commit()
        await db.refresh(account)
        return account

    acct_result = await db.execute(select(Account).where(Account.user_id == user.id))
    account = acct_result.scalar_one_or_none()

    if not account:
        account = Account(
            user_id=user.id,
            cash_balance=Decimal("1000000.00"),
            realized_pnl=Decimal("0.00"),
            daily_pnl_start=Decimal("1000000.00"),
        )
        db.add(account)
        await db.commit()
        await db.refresh(account)

    return account
