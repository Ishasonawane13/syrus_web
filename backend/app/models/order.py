"""Order model — full order lifecycle."""
from decimal import Decimal
from typing import Optional

from sqlalchemy import ForeignKey, Index, Integer, JSON, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.mixins import UUIDMixin, TimestampUpdateMixin


class OrderStatus:
    PENDING_APPROVAL = "PENDING_APPROVAL"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"
    OPEN = "OPEN"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    FILLED = "FILLED"


class OrderSide:
    BUY = "BUY"
    SELL = "SELL"


class OrderType:
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP = "STOP"


class Order(UUIDMixin, TimestampUpdateMixin, Base):
    __tablename__ = "orders"

    account_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False
    )
    instrument_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("instruments.id"), nullable=False
    )
    side: Mapped[str] = mapped_column(String(4), nullable=False)  # BUY | SELL
    order_type: Mapped[str] = mapped_column(String(10), nullable=False)  # MARKET | LIMIT | STOP
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    limit_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=True)
    stop_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=True)
    estimated_value: Mapped[Decimal] = mapped_column(
        Numeric(15, 2), nullable=False, default=Decimal("0")
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=OrderStatus.PENDING_APPROVAL, index=True
    )
    risk_status: Mapped[str] = mapped_column(String(10), nullable=False, default="PENDING")
    risk_details: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Relationships
    account: Mapped["Account"] = relationship("Account", back_populates="orders")
    instrument: Mapped["Instrument"] = relationship("Instrument", back_populates="orders")
    executions: Mapped[list["Execution"]] = relationship("Execution", back_populates="order")
    audit_logs: Mapped[list["AuditLog"]] = relationship("AuditLog", back_populates="order")

    __table_args__ = (
        Index("ix_orders_account_status", "account_id", "status"),
        Index("ix_orders_account_created", "account_id", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<Order {self.side} {self.quantity} instrument={self.instrument_id} status={self.status}>"
