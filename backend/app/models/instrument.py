"""Instrument model — tradeable securities."""
from sqlalchemy import Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.mixins import UUIDMixin, TimestampMixin


class Instrument(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "instruments"

    symbol: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    exchange: Mapped[str] = mapped_column(String(10), nullable=False, default="NSE")
    lot_size: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Relationships
    market_ticks: Mapped[list["MarketTick"]] = relationship(
        "MarketTick", back_populates="instrument"
    )
    positions: Mapped[list["Position"]] = relationship("Position", back_populates="instrument")
    orders: Mapped[list["Order"]] = relationship("Order", back_populates="instrument")

    def __repr__(self) -> str:
        return f"<Instrument {self.symbol}>"
