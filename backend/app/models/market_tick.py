"""Market tick model — price history."""
from decimal import Decimal
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.mixins import UUIDMixin, utc_now


class MarketTick(UUIDMixin, Base):
    __tablename__ = "market_ticks"

    instrument_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("instruments.id", ondelete="CASCADE"), nullable=False
    )
    price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    bid: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    ask: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    volume: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    change: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=Decimal("0"))
    change_pct: Mapped[Decimal] = mapped_column(Numeric(8, 4), nullable=False, default=Decimal("0"))
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )

    # Relationships
    instrument: Mapped["Instrument"] = relationship("Instrument", back_populates="market_ticks")

    __table_args__ = (
        Index("ix_market_ticks_instrument_timestamp", "instrument_id", "timestamp"),
    )

    def __repr__(self) -> str:
        return f"<MarketTick {self.instrument_id} price={self.price}>"
