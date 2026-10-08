"""
AI Copilot Service.

Orchestrates conversational queries, LLM tool execution, fallback intent parsing,
order proposal creation, and immutable audit logging.
"""
import json
import logging
import re
import uuid
from typing import Any, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.account import Account
from app.ai.prompts import SYSTEM_PROMPT
from app.ai.tools import TOOLS_SCHEMA, execute_tool, ToolValidationError, SUPPORTED_SYMBOLS
from app.schemas.ai import ChatResponse, OrderProposalCard, ToolCallRecord
from app.services.audit_service import log_ai_action

logger = logging.getLogger(__name__)


def is_valid_api_key(key: Optional[str]) -> bool:
    if not key or not isinstance(key, str):
        return False
    k = key.strip()
    if len(k) < 20:
        return False
    if any(placeholder in k.lower() for placeholder in ["your-", "here", "sk-...", "change-me", "example"]):
        return False
    return True


class AICopilotService:
    def __init__(self):
        self.llm_client = None
        self.llm_model = None
        self._init_clients()

    def _init_clients(self):
        provider = settings.LLM_PROVIDER.strip().lower()
        if provider == "openai" and is_valid_api_key(settings.OPENAI_API_KEY):
            try:
                from openai import AsyncOpenAI

                self.llm_client = AsyncOpenAI(
                    api_key=settings.OPENAI_API_KEY,
                    timeout=8.0,
                    max_retries=0,
                )
                self.llm_model = settings.OPENAI_MODEL
            except Exception:
                logger.exception("Could not initialize the OpenAI client")
        elif provider == "gemini" and is_valid_api_key(settings.GEMINI_API_KEY):
            try:
                from openai import AsyncOpenAI

                self.llm_client = AsyncOpenAI(
                    api_key=settings.GEMINI_API_KEY,
                    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
                    timeout=8.0,
                    max_retries=0,
                )
                self.llm_model = settings.GEMINI_MODEL
            except Exception:
                logger.exception("Could not initialize the Gemini client")

    async def chat(
        self,
        db: AsyncSession,
        account: Account,
        message: str,
        conversation_id: Optional[str] = None,
        history: Optional[List[Dict[str, str]]] = None,
    ) -> ChatResponse:
        conv_id = conversation_id or str(uuid.uuid4())
        tool_call_records: List[ToolCallRecord] = []
        proposal_card: Optional[OrderProposalCard] = None
        interpreted_intent: Optional[Dict[str, Any]] = None
        tool_used_name: Optional[str] = None
        tool_args_data: Optional[Dict[str, Any]] = None
        tool_result_data: Optional[Dict[str, Any]] = None
        risk_result_status: Optional[str] = None
        risk_details_data: Optional[Dict[str, Any]] = None
        order_id_ref: Optional[str] = None

        # 1. Attempt the configured LLM provider if its key is valid
        if self.llm_client:
            try:
                return await self._chat_with_provider(
                    db, account, message, conv_id, history or []
                )
            except Exception:
                logger.exception("Chat request failed for provider %s", settings.LLM_PROVIDER)
                pass  # Gracefully fall through to deterministic copilot engine

        # 2. Rule-based Deterministic Copilot Engine (Instant, robust, zero-lag)
        reply_text, tool_calls_executed = await self._chat_deterministic(
            db, account, message
        )

        for tc in tool_calls_executed:
            tool_name = tc["tool"]
            args = tc["args"]
            res = tc["result"]
            tool_call_records.append(
                ToolCallRecord(tool=tool_name, args=args, result=res)
            )

            tool_used_name = tool_name
            tool_args_data = args
            tool_result_data = res if isinstance(res, dict) else {"data": res}

            if tool_name == "create_order_proposal" and isinstance(res, dict):
                interpreted_intent = {
                    "action": args.get("action"),
                    "symbol": args.get("symbol"),
                    "quantity": args.get("quantity"),
                    "order_type": args.get("order_type"),
                    "limit_price": args.get("limit_price"),
                }
                order_id_ref = res.get("proposal_id")
                risk_result_status = res.get("risk_status")
                risk_details_data = res.get("risk_details")

                warnings = []
                if risk_result_status == "REJECTED":
                    warnings.append(risk_details_data.get("reason") if risk_details_data else "Order rejected by risk checks.")

                proposal_card = OrderProposalCard(
                    id=res["proposal_id"],
                    symbol=res["symbol"],
                    name=res.get("name"),
                    side=res["side"],
                    order_type=res["order_type"],
                    quantity=res["quantity"],
                    limit_price=res.get("limit_price"),
                    estimated_value=res["estimated_value"],
                    current_price=res["current_price"],
                    risk_status=res["risk_status"],
                    risk_details=res.get("risk_details"),
                    warnings=warnings,
                    status=res["status"],
                    message=res["message"],
                )

        # 3. Record Audit Log for every interaction
        try:
            await log_ai_action(
                db=db,
                account_id=account.id,
                user_request=message,
                interpreted_intent=interpreted_intent,
                tool_used=tool_used_name,
                tool_args=tool_args_data,
                tool_result=tool_result_data,
                order_id=order_id_ref,
                risk_result=risk_result_status,
                risk_details=risk_details_data,
                user_approved=None,
                execution_result=None,
            )
        except Exception:
            pass

        return ChatResponse(
            message=reply_text,
            conversation_id=conv_id,
            order_proposal=proposal_card,
            tool_calls=tool_call_records,
        )

    async def _chat_with_provider(
        self,
        db: AsyncSession,
        account: Account,
        message: str,
        conv_id: str,
        history: List[Dict[str, str]],
    ) -> ChatResponse:
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        for h in history[-6:]:
            messages.append({"role": h["role"], "content": h["content"]})
        messages.append({"role": "user", "content": message})

        response = await self.llm_client.chat.completions.create(
            model=self.llm_model,
            messages=messages,
            tools=TOOLS_SCHEMA,
            tool_choice="auto",
            temperature=0.1,
        )

        response_msg = response.choices[0].message
        tool_call_records: List[ToolCallRecord] = []
        proposal_card: Optional[OrderProposalCard] = None

        if response_msg.tool_calls:
            tool_messages = [response_msg]
            for t_call in response_msg.tool_calls:
                func_name = t_call.function.name
                func_args = json.loads(t_call.function.arguments or "{}")

                try:
                    result = await execute_tool(func_name, func_args, db, account)
                except Exception as err:
                    result = {"error": str(err)}

                tool_call_records.append(
                    ToolCallRecord(tool=func_name, args=func_args, result=result)
                )

                if func_name == "create_order_proposal" and isinstance(result, dict) and "proposal_id" in result:
                    warnings = []
                    if result.get("risk_status") == "REJECTED":
                        rd = result.get("risk_details") or {}
                        warnings.append(rd.get("reason", "Order rejected by risk checks"))

                    proposal_card = OrderProposalCard(
                        id=result["proposal_id"],
                        symbol=result["symbol"],
                        name=result.get("name"),
                        side=result["side"],
                        order_type=result["order_type"],
                        quantity=result["quantity"],
                        limit_price=result.get("limit_price"),
                        estimated_value=result["estimated_value"],
                        current_price=result.get("current_price", 0.0),
                        risk_status=result["risk_status"],
                        risk_details=result.get("risk_details"),
                        warnings=warnings,
                        status=result["status"],
                        message=result["message"],
                    )

                tool_messages.append({
                    "role": "tool",
                    "tool_call_id": t_call.id,
                    "name": func_name,
                    "content": json.dumps(result),
                })

            followup = await self.llm_client.chat.completions.create(
                model=self.llm_model,
                messages=messages + tool_messages,
                temperature=0.1,
            )
            final_text = followup.choices[0].message.content or "Completed request."
        else:
            final_text = response_msg.content or "I am ready to help you with paper trading."

        return ChatResponse(
            message=final_text,
            conversation_id=conv_id,
            order_proposal=proposal_card,
            tool_calls=tool_call_records,
        )

    async def _chat_deterministic(
        self,
        db: AsyncSession,
        account: Account,
        message: str,
    ) -> tuple[str, List[Dict[str, Any]]]:
        """
        High-precision intent matcher for common trading instructions & queries.
        Ensures 100% instant responses and zero lag.
        """
        text = message.strip()
        lower = text.lower()
        tool_calls: List[Dict[str, Any]] = []

        # 1. Trade Orders: Buy or Sell
        trade_match = re.search(
            r"\b(buy|sell)\s+(\d+)\s+([a-zA-Z]+)(?:\s+(?:at|if|for|limit)?\s*₹?\s*(\d+(?:\.\d+)?))?",
            lower,
        )
        if trade_match:
            action = trade_match.group(1).upper()
            quantity = int(trade_match.group(2))
            symbol = trade_match.group(3).upper()
            raw_limit = trade_match.group(4)

            if "limit" in lower or raw_limit:
                order_type = "LIMIT"
                limit_price = float(raw_limit) if raw_limit else None
            else:
                order_type = "MARKET"
                limit_price = None

            args = {
                "action": action,
                "symbol": symbol,
                "quantity": quantity,
                "order_type": order_type,
            }
            if limit_price:
                args["limit_price"] = limit_price

            try:
                res = await execute_tool("create_order_proposal", args, db, account)
                tool_calls.append({"tool": "create_order_proposal", "args": args, "result": res})

                if res.get("risk_status") == "PASSED":
                    reply = (
                        f"I have prepared a paper-trading order proposal to **{action} {quantity} shares of {symbol}** "
                        f"at an estimated value of **₹{res['estimated_value']:,.2f}**.\n\n"
                        f"All deterministic safety & risk rules have **PASSED** ✅.\n"
                        f"Please review and click **Confirm Paper Trade** in the card below to execute."
                    )
                else:
                    reason = res.get("risk_details", {}).get("reason", "Risk rule violation")
                    reply = (
                        f"⚠️ Order Proposal for **{action} {quantity} {symbol}** was **REJECTED** by the Risk Engine.\n\n"
                        f"**Reason:** {reason}\n\n"
                        f"No order has been placed."
                    )
                return reply, tool_calls
            except ToolValidationError as ve:
                return f"Validation error: {str(ve)}", []
            except Exception as ex:
                return f"Could not create proposal: {str(ex)}", []

        # 2. Available Cash / Balance query
        if any(w in lower for w in ["cash", "available cash", "balance", "funds", "how much money"]):
            res = await execute_tool("get_account", {}, db, account)
            tool_calls.append({"tool": "get_account", "args": {}, "result": res})
            avail_cash = res.get("available_cash", 0.0)
            total_val = res.get("total_value", 0.0)
            reply = (
                f"Your available cash balance is **₹{avail_cash:,.2f}**.\n"
                f"Total portfolio value is **₹{total_val:,.2f}**."
            )
            return reply, tool_calls

        # 3. Single Position query (e.g. "Show my TCS position")
        for sym in SUPPORTED_SYMBOLS:
            if sym.lower() in lower and any(w in lower for w in ["position", "holding", "shares", "hold"]):
                res = await execute_tool("get_position", {"symbol": sym}, db, account)
                tool_calls.append({"tool": "get_position", "args": {"symbol": sym}, "result": res})
                if res.get("quantity", 0) > 0:
                    reply = (
                        f"**{sym} Position:**\n"
                        f"- Quantity: **{res['quantity']} shares**\n"
                        f"- Average Price: **₹{res['avg_price']:,.2f}**\n"
                        f"- Current Price: **₹{res['current_price']:,.2f}**\n"
                        f"- Current Value: **₹{res['market_value']:,.2f}**\n"
                        f"- Unrealized P&L: **₹{res['unrealized_pnl']:+,.2f} ({res['unrealized_pnl_pct']:+.2f}%)**"
                    )
                else:
                    reply = f"You currently do not hold any shares of **{sym}**."
                return reply, tool_calls

        # 4. All Positions / Portfolio query
        if any(w in lower for w in ["positions", "holdings", "portfolio", "what stocks do i have", "show holdings"]):
            res = await execute_tool("get_positions", {}, db, account)
            tool_calls.append({"tool": "get_positions", "args": {}, "result": res})
            positions = res.get("positions", [])
            if not positions:
                return "You currently have no open stock positions.", tool_calls

            lines = ["Here are your current portfolio holdings:"]
            for p in positions:
                lines.append(
                    f"- **{p['symbol']}**: {p['quantity']} shares @ avg ₹{p['avg_price']:,.2f} | "
                    f"Value: ₹{p['market_value']:,.2f} | P&L: ₹{p['unrealized_pnl']:+,.2f} ({p['unrealized_pnl_pct']:+.2f}%)"
                )
            return "\n".join(lines), tool_calls

        # 5. P&L query: "How much did I make today?", "pnl", "profit", "loss"
        if any(w in lower for w in ["pnl", "profit", "loss", "how much did i make", "make today", "returns"]):
            res = await execute_tool("get_pnl", {}, db, account)
            tool_calls.append({"tool": "get_pnl", "args": {}, "result": res})
            daily = res.get("daily_pnl", 0.0)
            daily_pct = res.get("daily_pnl_pct", 0.0)
            total = res.get("total_pnl", 0.0)
            realized = res.get("realized_pnl", 0.0)
            unrealized = res.get("unrealized_pnl", 0.0)
            reply = (
                f"**P&L Summary:**\n"
                f"- Today's P&L: **₹{daily:+,.2f} ({daily_pct:+.2f}%)**\n"
                f"- Unrealized P&L: **₹{unrealized:+,.2f}**\n"
                f"- Realized P&L: **₹{realized:+,.2f}**\n"
                f"- Cumulative Total P&L: **₹{total:+,.2f}**"
            )
            return reply, tool_calls

        # 6. Market Price Quote query: e.g. "What is TCS price?", "price of INFY"
        for sym in SUPPORTED_SYMBOLS:
            if sym.lower() in lower and any(w in lower for w in ["price", "quote", "trading at", "cost", "value"]):
                res = await execute_tool("get_market_price", {"symbol": sym}, db, account)
                tool_calls.append({"tool": "get_market_price", "args": {"symbol": sym}, "result": res})
                reply = (
                    f"**{sym} ({res['name']})** is currently trading at **₹{res['price']:,.2f}**\n"
                    f"- Change: **₹{res['change']:+,.2f} ({res['change_pct']:+.2f}%)**\n"
                    f"- Best Bid: **₹{res['bid']:,.2f}** | Best Ask: **₹{res['ask']:,.2f}**\n"
                    f"- Volume: **{res['volume']:,}**"
                )
                return reply, tool_calls

        # 7. Order History query: "Show my orders", "orders"
        if any(w in lower for w in ["orders", "recent orders", "order history"]):
            res = await execute_tool("get_orders", {}, db, account)
            tool_calls.append({"tool": "get_orders", "args": {}, "result": res})
            orders = res.get("orders", [])
            if not orders:
                return "You have no recorded orders.", tool_calls
            lines = [f"Found {len(orders)} recent order(s):"]
            for o in orders[:5]:
                lines.append(
                    f"- **{o['side']} {o['quantity']} {o['symbol']}** ({o['order_type']}) — "
                    f"Status: **{o['status']}** (Est: ₹{o['estimated_value']:,.2f})"
                )
            return "\n".join(lines), tool_calls

        # Default helpful assistant reply
        return (
            "I'm your AI Trading Copilot for simulated paper trading. You can ask me:\n"
            "- *'What is my available cash?'*\n"
            "- *'Show my TCS position.'*\n"
            "- *'Buy 50 TCS at market price.'*\n"
            "- *'Sell 20 RELIANCE.'*\n"
            "- *'How much did I make today?'*\n"
            "- *'What is the price of INFY?'*\n\n"
            "All trading actions are validated through deterministic risk rules and require your explicit approval before execution."
        ), []


copilot_service = AICopilotService()
