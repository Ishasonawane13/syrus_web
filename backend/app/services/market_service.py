"""Market data service."""
from typing import Optional, List
import redis.asyncio as redis
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.instrument import Instrument
from app.trading.simulator import simulator, INSTRUMENT_CONFIG
from app.config import settings

# Global redis client initialization
redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)

async def get_all_instruments(db: AsyncSession) -> List[Instrument]:
    """Returns all active instruments."""
    result = await db.execute(
        select(Instrument).where(Instrument.is_active == True).order_by(Instrument.symbol)
    )
    return list(result.scalars().all())


async def get_instrument_by_symbol(db: AsyncSession, symbol: str) -> Optional[Instrument]:
    """Returns instrument by symbol."""
    result = await db.execute(
        select(Instrument).where(
            Instrument.symbol == symbol.upper(),
            Instrument.is_active == True,
        )
    )
    return result.scalar_one_or_none()


async def get_active_symbols(db: AsyncSession) -> List[str]:
    """Returns list of all active symbol strings."""
    instruments = await get_all_instruments(db)
    return [i.symbol for i in instruments]


async def get_instrument_price(symbol: str, name: str = "") -> Optional[dict]:
    """Returns current price tick as a dict."""
    sym_upper = symbol.upper()
    if sym_upper not in INSTRUMENT_CONFIG:
        return None
        
    if settings.MARKET_DATA_PROVIDER == "groww":
        data = await redis_client.hgetall(f"tick:{sym_upper}")
        if data and "price" in data:
            return {
                "symbol": sym_upper,
                "name": name,
                "price": float(data["price"]),
                "bid": float(data.get("bid", data["price"])),
                "ask": float(data.get("ask", data["price"])),
                "change": float(data.get("change", 0.0)),
                "change_pct": float(data.get("change_pct", 0.0)),
                "volume": int(data.get("volume", 0)),
                "timestamp": data.get("timestamp", datetime.now(timezone.utc).isoformat()),
            }

    # Fallback to simulator
    tick = simulator.get_tick(sym_upper, name)
    return {
        "symbol": tick.symbol,
        "name": tick.name,
        "price": tick.price,
        "bid": tick.bid,
        "ask": tick.ask,
        "change": tick.change,
        "change_pct": tick.change_pct,
        "volume": tick.volume,
        "timestamp": tick.timestamp.isoformat(),
    }


async def get_order_book(symbol: str) -> Optional[dict]:
    """Returns order book as a dict."""
    sym_upper = symbol.upper()
    if sym_upper not in INSTRUMENT_CONFIG:
        return None
        
    # Order book in Redis not fully implemented, fallback to simulator
    book = simulator.get_order_book(sym_upper)
    return {
        "symbol": book.symbol,
        "bids": [{"price": l.price, "quantity": l.quantity} for l in book.bids],
        "asks": [{"price": l.price, "quantity": l.quantity} for l in book.asks],
        "timestamp": book.timestamp.isoformat(),
    }


# Backwards compatibility aliases
get_market_tick_data = get_instrument_price
get_order_book_data = get_order_book
