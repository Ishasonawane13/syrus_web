"""Order schemas."""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict


class OrderProposalRequest(BaseModel):
    action: str  # BUY or SELL
    symbol: str
    quantity: int
    order_type: str = "MARKET"  # MARKET or LIMIT
    limit_price: Optional[float] = None


class OrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    symbol: str
    name: Optional[str] = None
    side: str
    order_type: str
    quantity: int
    limit_price: Optional[float] = None
    estimated_value: float
    status: str
    risk_status: Optional[str] = None
    risk_details: Optional[Dict[str, Any]] = None
    execution_price: Optional[float] = None
    execution_quantity: Optional[int] = None
    fees: Optional[float] = None
    created_at: str
    updated_at: Optional[str] = None
    executed_at: Optional[str] = None


class OrderListResponse(BaseModel):
    orders: List[OrderResponse]
    total: int


class OrderExecutionResponse(BaseModel):
    order_id: str
    status: str
    execution_price: float
    execution_quantity: int
    fees: float
    cash_after: float
    message: str


class OrderCancelResponse(BaseModel):
    order_id: str
    status: str
    message: str
