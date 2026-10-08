"""Account, Position, and PnL schemas."""
from typing import List, Optional
from pydantic import BaseModel, ConfigDict


class PositionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    symbol: str
    name: str
    quantity: int
    avg_price: float
    current_price: float
    market_value: float
    unrealized_pnl: float
    unrealized_pnl_pct: float
    allocation_pct: float


class PositionsListResponse(BaseModel):
    positions: List[PositionResponse]


class AccountResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_email: str
    cash_balance: float
    portfolio_value: float
    total_value: float
    available_cash: float
    realized_pnl: float
    unrealized_pnl: float
    daily_pnl: float
    daily_pnl_pct: float
    total_pnl: Optional[float] = None


class PnLResponse(BaseModel):
    realized_pnl: float
    unrealized_pnl: float
    daily_pnl: float
    daily_pnl_pct: float
    total_pnl: float
