"""Audit log schemas."""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict


class AuditLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    timestamp: str
    user_request: str
    interpreted_intent: Optional[Dict[str, Any]] = None
    tool_used: Optional[str] = None
    tool_args: Optional[Dict[str, Any]] = None
    tool_result: Optional[Dict[str, Any]] = None
    order_id: Optional[str] = None
    risk_result: Optional[str] = None
    risk_details: Optional[Dict[str, Any]] = None
    user_approved: Optional[bool] = None
    execution_result: Optional[str] = None


class AuditLogListResponse(BaseModel):
    logs: List[AuditLogResponse]
    total: int
