import asyncio
import logging
import pyotp
import redis.asyncio as redis
from datetime import datetime, timezone
import requests

from growwapi import GrowwAPI, GrowwFeed
from app.config import settings
from app.services.market_service import get_active_symbols
from app.database import AsyncSessionLocal

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("GrowwFeedWorker")

async def get_db_symbols():
    async with AsyncSessionLocal() as db:
        return await get_active_symbols(db)

def get_groww_token():
    if settings.GROWW_AUTH_TOKEN:
        logger.info("Using provided GROWW_AUTH_TOKEN")
        return settings.GROWW_AUTH_TOKEN
    
    if not settings.GROWW_API_KEY or not settings.GROWW_API_SECRET or not settings.GROWW_TOTP_SECRET:
        raise ValueError("Groww credentials missing in environment.")
    
    logger.info("Generating TOTP for Groww Auth...")
    totp = pyotp.TOTP(settings.GROWW_TOTP_SECRET)
    current_totp = totp.now()
    
    url = "https://api.groww.in/v1/token/api/access"
    headers = {
        "Authorization": f"Bearer {settings.GROWW_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "key_type": "totp",
        "totp": current_totp
    }
    
    resp = requests.post(url, json=payload, headers=headers)
    resp.raise_for_status()
    return resp.json()["token"]

async def main():
    logger.info("Starting Groww Live Feed Worker")
    r = redis.from_url(settings.REDIS_URL, decode_responses=True)
    
    try:
        token = get_groww_token()
        groww = GrowwAPI(token)
        groww._load_instruments()
    except Exception as e:
        logger.error(f"Failed to auth or load instruments: {e}")
        return

    symbols = await get_db_symbols()
    logger.info(f"Subscribing to symbols: {symbols}")
    
    instrument_list = []
    
    # 1. Fetch REST snapshots to prime cache immediately
    for sym in symbols:
        try:
            quote = groww.get_quote(trading_symbol=sym, exchange=groww.EXCHANGE_NSE, segment=groww.SEGMENT_CASH)
            price = quote.get("ltp", quote.get("average_price", 0.0))
            if "ohlc" in quote and quote["ohlc"].get("close"):
                price = quote["ohlc"]["close"]
            
            # Save snapshot to Redis
            data = {
                "symbol": sym,
                "name": sym,
                "price": str(price),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            await r.hset(f"tick:{sym}", mapping=data)
            logger.info(f"Primed {sym} cache: {price}")
            
            # Find exchange token for WS subscription
            inst = groww.get_instrument_by_exchange_and_trading_symbol(groww.EXCHANGE_NSE, sym)
            instrument_list.append({
                "exchange": groww.EXCHANGE_NSE,
                "segment": groww.SEGMENT_CASH,
                "exchangeToken": str(inst.get("exchange_token"))
            })
        except Exception as e:
            logger.error(f"Failed to prime {sym}: {e}")

    # 2. WebSocket listener
    if not instrument_list:
        logger.warning("No instruments resolved for WebSocket.")
        return

    try:
        feed = GrowwFeed(groww)
        feed.subscribe_ltp(instrument_list)
        
        logger.info("WebSocket Feed Subscribed. Listening for ticks...")
        
        while True:
            ltps = feed.get_ltp()
            if ltps and groww.EXCHANGE_NSE in ltps and groww.SEGMENT_CASH in ltps:
                cash_data = ltps[groww.EXCHANGE_NSE][groww.SEGMENT_CASH]
                
                for token_str, tick in cash_data.items():
                    # Reverse map token -> symbol
                    sym_df = groww.instruments.loc[groww.instruments["exchange_token"] == token_str]
                    if not sym_df.empty:
                        sym = sym_df.iloc[0]["trading_symbol"]
                        if tick.get("ltp"):
                            data = {
                                "symbol": sym,
                                "price": str(tick["ltp"]),
                                "timestamp": datetime.now(timezone.utc).isoformat()
                            }
                            await r.hset(f"tick:{sym}", mapping=data)
            
            await asyncio.sleep(0.5)

    except KeyboardInterrupt:
        logger.info("Shutting down worker...")
    except Exception as e:
        logger.error(f"Worker crashed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
