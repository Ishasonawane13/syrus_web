"""Audit Log API endpoints."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.account import Account
from app.api.deps import get_demo_account
from app.schemas.audit import AuditLogListResponse
from app.services.audit_service import get_audit_logs

router = APIRouter(prefix="/audit", tags=["Audit"])


@router.get("/logs", response_model=AuditLogListResponse)
async def list_audit_logs(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    account: Account = Depends(get_demo_account),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve immutable audit log history of all AI actions and trading approvals."""
    logs, total = await get_audit_logs(db, account.id, limit=limit, offset=offset)
    return {"logs": logs, "total": total}
