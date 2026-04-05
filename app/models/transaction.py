"""
Transaction ORM model — the core financial record.
"""
from datetime import date, datetime, timezone
from typing import Optional
from sqlalchemy import String, Numeric, Date, DateTime, Text, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.core.config import TxType


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    amount: Mapped[float] = mapped_column(Numeric(precision=12, scale=2), nullable=False)
    type: Mapped[TxType] = mapped_column(SAEnum(TxType), nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # ── Ownership ──────────────────────────────────────────────────────────────
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    owner: Mapped["User"] = relationship("User", back_populates="transactions")  # noqa: F821

    # ── Audit ──────────────────────────────────────────────────────────────────
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    def __repr__(self) -> str:
        return (
            f"<Transaction id={self.id} type={self.type} "
            f"amount={self.amount} category={self.category!r}>"
        )
