"""Position model — current holdings."""
from decimal import Decimal

from sqlalchemy import ForeignKey, Index, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.mixins import UUIDMixin, TimestampUpdateMixin


class Position(UUIDMixin, TimestampUpdateMixin, Base):
    __tablename__ = "positions"

    account_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False
    )
    instrument_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("instruments.id"), nullable=False
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    avg_price: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, default=Decimal("0")
    )
    realized_pnl: Mapped[Decimal] = mapped_column(
        Numeric(15, 2), nullable=False, default=Decimal("0")
    )

    # Relationships
    account: Mapped["Account"] = relationship("Account", back_populates="positions")
    instrument: Mapped["Instrument"] = relationship("Instrument", back_populates="positions")

    __table_args__ = (
        UniqueConstraint("account_id", "instrument_id", name="uq_positions_account_instrument"),
        Index("ix_positions_account", "account_id"),
    )

    def __repr__(self) -> str:
        return f"<Position {self.instrument_id} qty={self.quantity} avg={self.avg_price}>"
