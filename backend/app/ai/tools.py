"""
Tool definitions and executor for AI Trading Copilot.
Includes JSON Schema specifications and server-side argument validation.
"""
from typing import Any, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.account import Account
from app.trading.simulator import INSTRUMENT_CONFIG
from app.services.market_service import get_instrument_price, get_order_book
from app.services.portfolio_service import (
    get_account_summary,
    get_all_positions,
    get_pnl_summary,
    get_position_for_symbol,
)
from app.services.order_service import create_order_proposal, get_orders_for_account


SUPPORTED_SYMBOLS = list(INSTRUMENT_CONFIG.keys())


class ToolValidationError(Exception):
    """Raised when LLM tool call arguments fail server-side validation."""
    pass


# OpenAPI / OpenAI Function Calling schemas
TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "get_account",
            "description": "Fetch overall account balance, available cash, and portfolio values.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_positions",
            "description": "Fetch all current stock holdings and positions with their P&L.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_position",
            "description": "Fetch specific position holdings for an instrument symbol (e.g. TCS).",
            "parameters": {
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "NSE ticker symbol (e.g., TCS, INFY, RELIANCE)",
                    }
                },
                "required": ["symbol"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_market_price",
            "description": "Fetch the current simulated market price and quote for a symbol.",
            "parameters": {
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "NSE ticker symbol (e.g., TCS, INFY, RELIANCE)",
                    }
                },
                "required": ["symbol"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_order_book",
            "description": "Fetch current simulated bid and ask order book levels for a symbol.",
            "parameters": {
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "NSE ticker symbol (e.g., TCS, INFY)",
                    }
                },
                "required": ["symbol"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_orders",
            "description": "Retrieve order history, optionally filtered by status (PENDING_APPROVAL, FILLED, CANCELLED, REJECTED).",
            "parameters": {
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "description": "Optional status filter (e.g., FILLED, PENDING_APPROVAL)",
                    }
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_pnl",
            "description": "Get realized, unrealized, and today's total P&L metrics.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_order_proposal",
            "description": "Create an order proposal evaluated by the deterministic risk engine. Requires user approval before execution.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["BUY", "SELL"],
                        "description": "Order action side: BUY or SELL",
                    },
                    "symbol": {
                        "type": "string",
                        "description": "NSE ticker symbol (e.g., TCS, INFY, RELIANCE)",
                    },
                    "quantity": {
                        "type": "integer",
                        "description": "Positive integer number of shares to trade",
                    },
                    "order_type": {
                        "type": "string",
                        "enum": ["MARKET", "LIMIT"],
                        "description": "Order type: MARKET or LIMIT (default MARKET)",
                    },
                    "limit_price": {
                        "type": "number",
                        "description": "Limit price in INR if order_type is LIMIT",
                    },
                },
                "required": ["action", "symbol", "quantity"],
            },
        },
    },
]


def validate_order_proposal_args(args: Dict[str, Any]) -> None:
    """Rigorous server-side validation for proposed order parameters."""
    action = str(args.get("action", "")).upper()
    if action not in ("BUY", "SELL"):
        raise ToolValidationError(f"Invalid action '{action}'. Must be BUY or SELL.")

    symbol = str(args.get("symbol", "")).upper()
    if not symbol:
        raise ToolValidationError("Symbol is required.")

    qty = args.get("quantity")
    if not isinstance(qty, int) or qty <= 0:
        raise ToolValidationError(f"Quantity must be a positive integer, received: {qty}")

    order_type = str(args.get("order_type", "MARKET")).upper()
    if order_type not in ("MARKET", "LIMIT"):
        raise ToolValidationError(f"Invalid order type '{order_type}'. Must be MARKET or LIMIT.")

    limit_price = args.get("limit_price")
    if order_type == "LIMIT":
        if limit_price is None or float(limit_price) <= 0:
            raise ToolValidationError("Limit price must be specified and positive for LIMIT orders.")


async def execute_tool(
    name: str,
    args: Dict[str, Any],
    db: AsyncSession,
    account: Account,
) -> Any:
    """Execute a tool call safely against the application backend."""
    if name == "get_account":
        return await get_account_summary(db, account)

    elif name == "get_positions":
        return await get_all_positions(db, account)

    elif name == "get_position":
        symbol = str(args.get("symbol", "")).upper()
        res = await get_position_for_symbol(db, account, symbol)
        if not res:
            return {"symbol": symbol, "quantity": 0, "message": f"No active position found for {symbol}"}
        return res

    elif name == "get_market_price":
        symbol = str(args.get("symbol", "")).upper()
        price_info = get_instrument_price(symbol)
        if not price_info:
            return {"error": f"Instrument {symbol} not found"}
        return price_info

    elif name == "get_order_book":
        symbol = str(args.get("symbol", "")).upper()
        book = get_order_book(symbol)
        if not book:
            return {"error": f"Orderbook not found for {symbol}"}
        return book

    elif name == "get_orders":
        status_filter = args.get("status")
        orders, _ = await get_orders_for_account(db, account.id, status_filter=status_filter)
        return {"orders": orders}

    elif name == "get_pnl":
        return await get_pnl_summary(db, account)

    elif name == "create_order_proposal":
        validate_order_proposal_args(args)
        symbol = str(args["symbol"]).upper()
        action = str(args["action"]).upper()
        quantity = int(args["quantity"])
        order_type = str(args.get("order_type", "MARKET")).upper()
        limit_price = float(args["limit_price"]) if args.get("limit_price") is not None else None

        order, risk_result = await create_order_proposal(
            db=db,
            account=account,
            symbol=symbol,
            side=action,
            quantity=quantity,
            order_type=order_type,
            limit_price=limit_price,
        )

        curr_price = get_instrument_price(symbol)
        price_val = curr_price["price"] if curr_price else 0.0

        return {
            "proposal_id": order.id,
            "symbol": symbol,
            "side": order.side,
            "order_type": order.order_type,
            "quantity": order.quantity,
            "limit_price": float(order.limit_price) if order.limit_price else None,
            "estimated_value": float(order.estimated_value),
            "current_price": price_val,
            "risk_status": risk_result.status,
            "risk_details": risk_result.to_dict(),
            "status": order.status,
            "message": (
                "Order proposal created and passed safety checks. Please review and confirm to execute."
                if risk_result.status == "PASSED"
                else f"Order proposal was rejected by the risk engine: {risk_result.reason}"
            ),
        }

    else:
        raise ValueError(f"Unknown tool '{name}'")
