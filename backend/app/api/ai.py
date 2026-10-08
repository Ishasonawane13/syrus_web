"""AI Copilot chat API endpoints."""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.account import Account
from app.api.deps import get_demo_account
from app.schemas.ai import ChatRequest, ChatResponse
from app.ai.copilot import copilot_service

router = APIRouter(prefix="/ai", tags=["AI Copilot"])


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    account: Account = Depends(get_demo_account),
    db: AsyncSession = Depends(get_db),
):
    """
    Main AI Copilot chat endpoint.
    Processes user natural language input, invokes tool calling with safety checks,
    creates validated order proposals when requested, and returns structured data.
    """
    response = await copilot_service.chat(
        db=db,
        account=account,
        message=request.message,
        conversation_id=request.conversation_id,
    )
    return response


@router.get("/chat/history")
async def chat_history():
    """Returns sample or stored conversation history."""
    return {
        "history": [
            {
                "role": "assistant",
                "content": "Hello! I am your AI Trading Copilot. How can I help you manage your paper portfolio today?",
            }
        ]
    }
