"""
Transaction repository — all database access for financial records.
Filtering, pagination, and raw aggregation live here.
"""
from datetime import date
from typing import Optional
from collections import defaultdict

from sqlalchemy import func, extract
from sqlalchemy.orm import Session

from app.models.transaction import Transaction
from app.core.config import TxType
from app.schemas.transaction import TransactionFilter


class TransactionRepository:

    def __init__(self, db: Session) -> None:
        self.db = db

    # ── Internal query builder ────────────────────────────────────────────────

    def _base_query(self, owner_id: Optional[int] = None, f: Optional[TransactionFilter] = None):
        q = self.db.query(Transaction)
        if owner_id is not None:
            q = q.filter(Transaction.owner_id == owner_id)
        if f:
            if f.type:
                q = q.filter(Transaction.type == f.type)
            if f.category:
                q = q.filter(Transaction.category == f.category.lower())
            if f.date_from:
                q = q.filter(Transaction.date >= f.date_from)
            if f.date_to:
                q = q.filter(Transaction.date <= f.date_to)
            if f.min_amount:
                q = q.filter(Transaction.amount >= f.min_amount)
            if f.max_amount:
                q = q.filter(Transaction.amount <= f.max_amount)
        return q

    # ── CRUD ──────────────────────────────────────────────────────────────────

    def get_by_id(self, tx_id: int, owner_id: Optional[int] = None) -> Optional[Transaction]:
        q = self.db.query(Transaction).filter(Transaction.id == tx_id)
        if owner_id is not None:
            q = q.filter(Transaction.owner_id == owner_id)
        return q.first()

    def list_transactions(
        self,
        owner_id: Optional[int] = None,
        filters: Optional[TransactionFilter] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Transaction], int]:
        q = self._base_query(owner_id, filters)
        total = q.count()
        results = (
            q.order_by(Transaction.date.desc(), Transaction.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        return results, total

    def create(self, owner_id: int, **kwargs) -> Transaction:
        tx = Transaction(owner_id=owner_id, **kwargs)
        self.db.add(tx)
        self.db.commit()
        self.db.refresh(tx)
        return tx

    def update(self, tx: Transaction, updates: dict) -> Transaction:
        for field, value in updates.items():
            if value is not None:
                setattr(tx, field, value)
        self.db.commit()
        self.db.refresh(tx)
        return tx

    def delete(self, tx: Transaction) -> None:
        self.db.delete(tx)
        self.db.commit()

    # ── Aggregations (used by analytics service) ──────────────────────────────

    def total_by_type(self, owner_id: Optional[int] = None) -> dict[TxType, float]:
        q = self.db.query(Transaction.type, func.sum(Transaction.amount))
        if owner_id:
            q = q.filter(Transaction.owner_id == owner_id)
        rows = q.group_by(Transaction.type).all()
        return {row[0]: float(row[1]) for row in rows}

    def count_by_type(self, owner_id: Optional[int] = None) -> dict[TxType, int]:
        q = self.db.query(Transaction.type, func.count(Transaction.id))
        if owner_id:
            q = q.filter(Transaction.owner_id == owner_id)
        rows = q.group_by(Transaction.type).all()
        return {row[0]: row[1] for row in rows}

    def breakdown_by_category(
        self, tx_type: TxType, owner_id: Optional[int] = None
    ) -> list[tuple[str, float, int]]:
        """Returns (category, total_amount, count) sorted by total desc."""
        q = self.db.query(
            Transaction.category,
            func.sum(Transaction.amount),
            func.count(Transaction.id),
        ).filter(Transaction.type == tx_type)
        if owner_id:
            q = q.filter(Transaction.owner_id == owner_id)
        rows = q.group_by(Transaction.category).order_by(func.sum(Transaction.amount).desc()).all()
        return [(r[0], float(r[1]), r[2]) for r in rows]

    def monthly_totals(
        self, owner_id: Optional[int] = None
    ) -> list[tuple[int, int, TxType, float]]:
        """Returns (year, month, type, total) for all months."""
        q = self.db.query(
            extract("year", Transaction.date).label("year"),
            extract("month", Transaction.date).label("month"),
            Transaction.type,
            func.sum(Transaction.amount),
        )
        if owner_id:
            q = q.filter(Transaction.owner_id == owner_id)
        rows = (
            q.group_by("year", "month", Transaction.type)
            .order_by("year", "month")
            .all()
        )
        return [(int(r[0]), int(r[1]), r[2], float(r[3])) for r in rows]

    def recent(self, owner_id: Optional[int] = None, limit: int = 5) -> list[Transaction]:
        q = self.db.query(Transaction)
        if owner_id:
            q = q.filter(Transaction.owner_id == owner_id)
        return q.order_by(Transaction.date.desc(), Transaction.id.desc()).limit(limit).all()

    def get_all_for_export(
        self,
        owner_id: Optional[int] = None,
        filters: Optional[TransactionFilter] = None,
    ) -> list[Transaction]:
        return self._base_query(owner_id, filters).order_by(Transaction.date.desc()).all()
