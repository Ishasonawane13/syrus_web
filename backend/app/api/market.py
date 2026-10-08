"""Market data API endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.market import InstrumentsListResponse, MarketPriceResponse, OrderBookResponse
from app.services.market_service import (
    get_all_instruments,
    get_instrument_price,
    get_order_book,
)

router = APIRouter(prefix="/market", tags=["Market"])


@router.get("/instruments", response_model=InstrumentsListResponse)
async def list_instruments(db: AsyncSession = Depends(get_db)):
    """List all supported tradeable instruments."""
    instruments = await get_all_instruments(db)
    return {"instruments": instruments}


@router.get("/{symbol}/price", response_model=MarketPriceResponse)
async def get_price(symbol: str):
    """Get current simulated market price for a symbol."""
    data = get_instrument_price(symbol.upper())
    if not data:
        raise HTTPException(status_code=404, detail=f"Instrument '{symbol}' not found")
    return data


@router.get("/{symbol}/orderbook", response_model=OrderBookResponse)
async def get_book(symbol: str):
    """Get simulated bid/ask order book depth for a symbol."""
    book = get_order_book(symbol.upper())
    if not book:
        raise HTTPException(status_code=404, detail=f"Instrument '{symbol}' not found")
    return book
