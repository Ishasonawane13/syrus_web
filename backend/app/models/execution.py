"""Execution model — records of filled orders."""
from decimal import Decimal
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.mixins import UUIDMixin, utc_now


class Execution(UUIDMixin, Base):
    __tablename__ = "executions"

    order_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False
    )
    execution_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    execution_quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    fees: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=Decimal("0"))
    total_value: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    executed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )

    # Relationships
    order: Mapped["Order"] = relationship("Order", back_populates="executions")
    transaction: Mapped[list["Transaction"]] = relationship("Transaction", back_populates="execution")

    def __repr__(self) -> str:
        return f"<Execution order={self.order_id} price={self.execution_price} qty={self.execution_quantity}>"
