"""Transaction model — cash flow ledger."""
from decimal import Decimal
from typing import Optional

from sqlalchemy import ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.mixins import UUIDMixin, TimestampMixin


class Transaction(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "transactions"

    account_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False
    )
    execution_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("executions.id"), nullable=True
    )
    # BUY_FILL | SELL_FILL | FEE | DEPOSIT | WITHDRAWAL
    type: Mapped[str] = mapped_column(String(20), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    balance_before: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    balance_after: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")

    # Relationships
    account: Mapped["Account"] = relationship("Account", back_populates="transactions")
    execution: Mapped[Optional["Execution"]] = relationship(
        "Execution", back_populates="transaction"
    )

    def __repr__(self) -> str:
        return f"<Transaction {self.type} amount={self.amount}>"
