"""
Deterministic market price simulator.

Generates realistic-looking price ticks using a seeded random walk.
Prices are reproducible for a given day + seed combination.
"""
import math
import random
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from app.config import settings


# Base prices and metadata for each instrument (realistic NSE prices)
INSTRUMENT_CONFIG: dict[str, dict] = {
    "RELIANCE": {
        "name": "Reliance Industries Limited",
        "base_price": 2800.0,
        "daily_volatility": 0.015,  # 1.5% daily vol
        "avg_volume": 5_000_000,
        "spread_pct": 0.0003,
        "exchange": "NSE",
        "lot_size": 1,
    },
    "TCS": {
        "name": "Tata Consultancy Services",
        "base_price": 3500.0,
        "daily_volatility": 0.012,
        "avg_volume": 2_500_000,
        "spread_pct": 0.0003,
        "exchange": "NSE",
        "lot_size": 1,
    },
    "INFY": {
        "name": "Infosys Limited",
        "base_price": 1500.0,
        "daily_volatility": 0.014,
        "avg_volume": 8_000_000,
        "spread_pct": 0.0003,
        "exchange": "NSE",
        "lot_size": 1,
    },
    "HDFCBANK": {
        "name": "HDFC Bank Limited",
        "base_price": 1650.0,
        "daily_volatility": 0.013,
        "avg_volume": 10_000_000,
        "spread_pct": 0.0002,
        "exchange": "NSE",
        "lot_size": 1,
    },
    "ICICIBANK": {
        "name": "ICICI Bank Limited",
        "base_price": 1100.0,
        "daily_volatility": 0.016,
        "avg_volume": 12_000_000,
        "spread_pct": 0.0003,
        "exchange": "NSE",
        "lot_size": 1,
    },
    "SBIN": {
        "name": "State Bank of India",
        "base_price": 620.0,
        "daily_volatility": 0.018,
        "avg_volume": 20_000_000,
        "spread_pct": 0.0004,
        "exchange": "NSE",
        "lot_size": 1,
    },
    "ITC": {
        "name": "ITC Limited",
        "base_price": 450.0,
        "daily_volatility": 0.010,
        "avg_volume": 15_000_000,
        "spread_pct": 0.0004,
        "exchange": "NSE",
        "lot_size": 1,
    },
    "TATAMOTORS": {
        "name": "Tata Motors Limited",
        "base_price": 950.0,
        "daily_volatility": 0.020,
        "avg_volume": 6_000_000,
        "spread_pct": 0.0005,
        "exchange": "NSE",
        "lot_size": 1,
    },
}


@dataclass
class Tick:
    symbol: str
    name: str
    price: float
    bid: float
    ask: float
    volume: int
    change: float
    change_pct: float
    timestamp: datetime


@dataclass
class OrderBookLevel:
    price: float
    quantity: int


@dataclass
class OrderBook:
    symbol: str
    bids: list[OrderBookLevel]
    asks: list[OrderBookLevel]
    timestamp: datetime


class MarketSimulator:
    """
    Deterministic market simulator.

    Price algorithm:
    1. Start from base price
    2. Apply a seeded random walk using (date + seed) as the seed
    3. Each tick is a small step in the random walk
    4. Price is bounded within ±5% of base price for stability
    """

    def __init__(self, seed: int = settings.MARKET_SEED):
        self.seed = seed

    def _get_price_for_symbol(self, symbol: str, timestamp: Optional[datetime] = None) -> float:
        """Generate a deterministic price for a symbol at a given time."""
        if symbol not in INSTRUMENT_CONFIG:
            raise ValueError(f"Unknown symbol: {symbol}")

        config = INSTRUMENT_CONFIG[symbol]
        base = config["base_price"]
        vol = config["daily_volatility"]

        if timestamp is None:
            timestamp = datetime.now(timezone.utc)

        # Create a seed from symbol + date + global seed
        date_seed = timestamp.strftime("%Y%m%d")
        tick_seed = int(timestamp.strftime("%H%M")) // settings.MARKET_TICK_INTERVAL
        combined_seed = hash(f"{symbol}{date_seed}{tick_seed}{self.seed}") % (2**31)

        rng = random.Random(combined_seed)

        # Random walk: sum of multiple small steps
        n_steps = 50
        step_vol = vol / math.sqrt(n_steps)
        cumulative_return = sum(rng.gauss(0, step_vol) for _ in range(n_steps))

        # Bound to ±8% of base
        cumulative_return = max(-0.08, min(0.08, cumulative_return))
        price = base * (1 + cumulative_return)

        return round(price, 2)

    def get_tick(self, symbol: str, name: str = "", timestamp: Optional[datetime] = None) -> Tick:
        """Get the current simulated price tick for a symbol."""
        if timestamp is None:
            timestamp = datetime.now(timezone.utc)

        config = INSTRUMENT_CONFIG.get(symbol, {})
        if not config:
            raise ValueError(f"Unknown symbol: {symbol}")

        price = self._get_price_for_symbol(symbol, timestamp)
        spread_pct = config.get("spread_pct", 0.0003)
        spread = price * spread_pct

        bid = round(price - spread / 2, 2)
        ask = round(price + spread / 2, 2)

        # Yesterday's close (for change calculation)
        from datetime import timedelta
        yesterday = timestamp - timedelta(days=1)
        prev_close = self._get_price_for_symbol(symbol, yesterday)

        change = round(price - prev_close, 2)
        change_pct = round((change / prev_close) * 100, 4) if prev_close else 0

        # Volume: based on time of day (higher near open/close)
        hour = timestamp.hour
        volume_factor = 0.5 + 0.5 * math.sin(math.pi * (hour - 9) / 7) if 9 <= hour <= 16 else 0.1
        avg_vol = config.get("avg_volume", 5_000_000)
        rng = random.Random(hash(f"{symbol}{timestamp.date()}{self.seed}vol"))
        volume = int(avg_vol * volume_factor * rng.uniform(0.8, 1.2))

        return Tick(
            symbol=symbol,
            name=name or config.get("name", symbol),
            price=price,
            bid=bid,
            ask=ask,
            volume=max(0, volume),
            change=change,
            change_pct=change_pct,
            timestamp=timestamp,
        )

    def get_order_book(self, symbol: str, levels: int = 5) -> OrderBook:
        """Generate a simulated order book with bid/ask levels."""
        timestamp = datetime.now(timezone.utc)
        tick = self.get_tick(symbol, timestamp=timestamp)

        rng = random.Random(hash(f"{symbol}{timestamp.strftime('%H%M')}{self.seed}book"))
        tick_size = 0.05  # ₹0.05 tick size

        bids = []
        asks = []

        for i in range(levels):
            bid_price = round(tick.bid - i * tick_size, 2)
            bid_qty = rng.randint(100, 2000) * 10
            bids.append(OrderBookLevel(price=bid_price, quantity=bid_qty))

            ask_price = round(tick.ask + i * tick_size, 2)
            ask_qty = rng.randint(100, 2000) * 10
            asks.append(OrderBookLevel(price=ask_price, quantity=ask_qty))

        return OrderBook(symbol=symbol, bids=bids, asks=asks, timestamp=timestamp)

    def get_price(self, symbol: str) -> float:
        """Quick method to get just the current price."""
        return self._get_price_for_symbol(symbol)

    def apply_slippage(self, price: float, quantity: int, side: str) -> float:
        """
        Apply market impact / slippage for large orders.
        Small orders: 0.01% slippage
        Large orders (>1000 shares): up to 0.1% additional
        """
        base_slippage = 0.0001
        size_factor = min(quantity / 10000, 1.0) * 0.001
        total_slippage = base_slippage + size_factor

        if side == "BUY":
            return round(price * (1 + total_slippage), 2)
        else:
            return round(price * (1 - total_slippage), 2)


# Singleton instance
simulator = MarketSimulator()
