"""Audit log service — track AI actions and decisions."""
from typing import Any, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.models.audit_log import AuditLog


async def log_ai_action(
    db: AsyncSession,
    account_id: str,
    user_request: str,
    interpreted_intent: Optional[Dict[str, Any]] = None,
    tool_used: Optional[str] = None,
    tool_args: Optional[Dict[str, Any]] = None,
    tool_result: Optional[Dict[str, Any]] = None,
    order_id: Optional[str] = None,
    risk_result: Optional[str] = None,
    risk_details: Optional[Dict[str, Any]] = None,
    user_approved: Optional[bool] = None,
    execution_result: Optional[str] = None,
) -> AuditLog:
    """Record an action taken by or through the AI Copilot."""
    entry = AuditLog(
        account_id=account_id,
        user_request=user_request,
        interpreted_intent=interpreted_intent,
        tool_used=tool_used,
        tool_args=tool_args,
        tool_result=tool_result,
        order_id=order_id,
        risk_result=risk_result,
        risk_details=risk_details,
        user_approved=user_approved,
        execution_result=execution_result,
    )
    db.add(entry)
    await db.commit()
    await db.refresh(entry)
    return entry


async def get_audit_logs(
    db: AsyncSession,
    account_id: str,
    limit: int = 50,
    offset: int = 0,
) -> tuple[List[dict], int]:
    """Retrieve audit logs with pagination."""
    query = (
        select(AuditLog)
        .where(AuditLog.account_id == account_id)
        .order_by(desc(AuditLog.created_at))
        .offset(offset)
        .limit(limit)
    )
    result = await db.execute(query)
    entries = result.scalars().all()

    logs = []
    for entry in entries:
        logs.append({
            "id": entry.id,
            "timestamp": entry.created_at.isoformat(),
            "user_request": entry.user_request,
            "interpreted_intent": entry.interpreted_intent,
            "tool_used": entry.tool_used,
            "tool_args": entry.tool_args,
            "tool_result": entry.tool_result,
            "order_id": entry.order_id,
            "risk_result": entry.risk_result,
            "risk_details": entry.risk_details,
            "user_approved": entry.user_approved,
            "execution_result": entry.execution_result,
        })

    return logs, len(logs)
