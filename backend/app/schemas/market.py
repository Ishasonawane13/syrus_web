"""Market schemas."""
from typing import List
from pydantic import BaseModel, ConfigDict


class InstrumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    symbol: str
    name: str
    exchange: str
    lot_size: int
    is_active: bool


class InstrumentsListResponse(BaseModel):
    instruments: List[InstrumentResponse]


class MarketPriceResponse(BaseModel):
    symbol: str
    name: str
    price: float
    bid: float
    ask: float
    change: float
    change_pct: float
    volume: int
    timestamp: str


class OrderBookLevel(BaseModel):
    price: float
    quantity: int


class OrderBookResponse(BaseModel):
    symbol: str
    bids: List[OrderBookLevel]
    asks: List[OrderBookLevel]
    timestamp: str
