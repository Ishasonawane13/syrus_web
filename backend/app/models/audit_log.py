"""Audit log model — complete trail of AI actions."""
from typing import Optional

from sqlalchemy import Boolean, ForeignKey, Index, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.mixins import UUIDMixin, TimestampMixin


class AuditLog(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "audit_logs"

    account_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False
    )
    order_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("orders.id"), nullable=True
    )
    # Original user message
    user_request: Mapped[str] = mapped_column(Text, nullable=False)
    # Structured intent parsed by LLM
    interpreted_intent: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    # Tool function called
    tool_used: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    # Args passed to tool
    tool_args: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    # Tool execution result
    tool_result: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    # PASSED | REJECTED | N/A
    risk_result: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    # Rule-by-rule details
    risk_details: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    # Did user approve the order?
    user_approved: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    # FILLED | CANCELLED | N/A
    execution_result: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    # Relationships
    account: Mapped["Account"] = relationship("Account", back_populates="audit_logs")
    order: Mapped[Optional["Order"]] = relationship("Order", back_populates="audit_logs")

    __table_args__ = (Index("ix_audit_logs_account_created", "account_id", "created_at"),)

    def __repr__(self) -> str:
        return f"<AuditLog account={self.account_id} tool={self.tool_used}>"
