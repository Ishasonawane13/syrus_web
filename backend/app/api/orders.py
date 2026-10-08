"""Orders and Execution API endpoints."""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.database import get_db
from app.models.account import Account
from app.models.order import Order
from app.models.instrument import Instrument
from app.api.deps import get_demo_account
from app.schemas.order import (
    OrderListResponse,
    OrderResponse,
    OrderExecutionResponse,
    OrderCancelResponse,
)
from app.services.order_service import get_orders_for_account
from app.trading.engine import trading_engine
from app.services.audit_service import log_ai_action

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.get("", response_model=OrderListResponse)
async def list_orders(
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    account: Account = Depends(get_demo_account),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve orders for the account with optional status filtering."""
    orders, total = await get_orders_for_account(
        db, account.id, status_filter=status, limit=limit, offset=offset
    )
    return {"orders": orders, "total": total}


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: str,
    account: Account = Depends(get_demo_account),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve details of a single order."""
    result = await db.execute(
        select(Order, Instrument)
        .join(Instrument, Order.instrument_id == Instrument.id)
        .where(and_(Order.id == order_id, Order.account_id == account.id))
    )
    row = result.first()
    if not row:
        raise HTTPException(status_code=404, detail="Order not found")

    order, instrument = row
    return {
        "id": order.id,
        "symbol": instrument.symbol,
        "name": instrument.name,
        "side": order.side,
        "order_type": order.order_type,
        "quantity": order.quantity,
        "limit_price": float(order.limit_price) if order.limit_price else None,
        "estimated_value": float(order.estimated_value),
        "status": order.status,
        "risk_status": order.risk_status,
        "risk_details": order.risk_details,
        "created_at": order.created_at.isoformat(),
        "updated_at": order.updated_at.isoformat() if order.updated_at else None,
    }


@router.post("/{order_id}/execute", response_model=OrderExecutionResponse)
async def execute_order(
    order_id: str,
    account: Account = Depends(get_demo_account),
    db: AsyncSession = Depends(get_db),
):
    """
    Execute an approved order in the simulated exchange.
    CRITICAL SAFETY CHECK:
    Order must be in status PENDING_APPROVAL and satisfy all live balance constraints.
    """
    try:
        exec_res = await trading_engine.execute_approved_order(
            db=db,
            order_id=order_id,
            account_id=account.id,
        )
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Execution error: {str(e)}")

    # Record user approval & execution result in audit logs
    try:
        await log_ai_action(
            db=db,
            account_id=account.id,
            user_request="User confirmed and approved order execution via UI",
            order_id=order_id,
            user_approved=True,
            execution_result=exec_res.status,
            tool_result={
                "execution_price": exec_res.execution_price,
                "quantity": exec_res.execution_quantity,
                "fees": exec_res.fees,
            },
        )
    except Exception:
        pass

    return {
        "order_id": exec_res.order_id,
        "status": exec_res.status,
        "execution_price": exec_res.execution_price,
        "execution_quantity": exec_res.execution_quantity,
        "fees": exec_res.fees,
        "cash_after": exec_res.cash_after,
        "message": exec_res.message,
    }


@router.post("/{order_id}/cancel", response_model=OrderCancelResponse)
async def cancel_order(
    order_id: str,
    account: Account = Depends(get_demo_account),
    db: AsyncSession = Depends(get_db),
):
    """Cancel a pending or open order."""
    try:
        res = await trading_engine.cancel_order(
            db=db,
            order_id=order_id,
            account_id=account.id,
        )
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    # Record cancellation in audit logs
    try:
        await log_ai_action(
            db=db,
            account_id=account.id,
            user_request="User rejected / cancelled order proposal via UI",
            order_id=order_id,
            user_approved=False,
            execution_result="CANCELLED",
        )
    except Exception:
        pass

    return res
