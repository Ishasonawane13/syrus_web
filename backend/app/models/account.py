"""Account model — holds cash balance and P&L tracking."""
from decimal import Decimal
from sqlalchemy import ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.mixins import UUIDMixin, TimestampUpdateMixin


class Account(UUIDMixin, TimestampUpdateMixin, Base):
    __tablename__ = "accounts"

    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    cash_balance: Mapped[Decimal] = mapped_column(
        Numeric(15, 2), nullable=False, default=Decimal("0.00")
    )
    realized_pnl: Mapped[Decimal] = mapped_column(
        Numeric(15, 2), nullable=False, default=Decimal("0.00")
    )
    # Snapshot of total portfolio value at start of trading day
    daily_pnl_start: Mapped[Decimal] = mapped_column(
        Numeric(15, 2), nullable=False, default=Decimal("0.00")
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="account")
    positions: Mapped[list["Position"]] = relationship("Position", back_populates="account")
    orders: Mapped[list["Order"]] = relationship("Order", back_populates="account")
    transactions: Mapped[list["Transaction"]] = relationship("Transaction", back_populates="account")
    audit_logs: Mapped[list["AuditLog"]] = relationship("AuditLog", back_populates="account")

    def __repr__(self) -> str:
        return f"<Account user_id={self.user_id} cash={self.cash_balance}>"
