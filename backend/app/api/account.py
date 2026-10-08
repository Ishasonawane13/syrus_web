"""Account and portfolio API endpoints."""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.account import Account
from app.api.deps import get_demo_account
from app.schemas.account import AccountResponse, PositionsListResponse, PnLResponse
from app.services.portfolio_service import (
    get_account_summary,
    get_all_positions,
    get_pnl_summary,
)

router = APIRouter(prefix="/account", tags=["Account"])


@router.get("", response_model=AccountResponse)
async def get_account(
    account: Account = Depends(get_demo_account),
    db: AsyncSession = Depends(get_db),
):
    """Get the current demo account summary with balances and P&L."""
    summary = await get_account_summary(db, account)
    return summary


@router.get("/positions", response_model=PositionsListResponse)
async def get_positions(
    account: Account = Depends(get_demo_account),
    db: AsyncSession = Depends(get_db),
):
    """Get all current portfolio positions with real-time valuation."""
    positions = await get_all_positions(db, account)
    return positions


@router.get("/pnl", response_model=PnLResponse)
async def get_pnl(
    account: Account = Depends(get_demo_account),
    db: AsyncSession = Depends(get_db),
):
    """Get P&L breakdown (realized, unrealized, and today's return)."""
    pnl = await get_pnl_summary(db, account)
    return pnl
