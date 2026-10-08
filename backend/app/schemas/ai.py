"""AI Copilot schemas."""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None


class ToolCallRecord(BaseModel):
    tool: str
    args: Dict[str, Any]
    result: Any


class OrderProposalCard(BaseModel):
    id: str
    symbol: str
    name: Optional[str] = None
    side: str
    order_type: str
    quantity: int
    limit_price: Optional[float] = None
    estimated_value: float
    current_price: float
    risk_status: str
    risk_details: Optional[Dict[str, Any]] = None
    warnings: List[str] = []
    status: str
    message: str


class ChatResponse(BaseModel):
    message: str
    conversation_id: str
    order_proposal: Optional[OrderProposalCard] = None
    tool_calls: List[ToolCallRecord] = []
