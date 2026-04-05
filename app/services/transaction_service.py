"""
Transaction service — all business logic for financial records and analytics.
"""
import csv
import io
import json
from collections import defaultdict
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import TxType, Role
from app.models.transaction import Transaction
from app.models.user import User
from app.repositories.transaction_repo import TransactionRepository
from app.schemas.transaction import (
    TransactionCreate,
    TransactionFilter,
    TransactionUpdate,
    PaginatedTransactions,
    TransactionOut,
    FinancialSummary,
    CategoryBreakdown,
    MonthlyTotal,
)


class TransactionService:

    def __init__(self, db: Session) -> None:
        self.repo = TransactionRepository(db)

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _resolve_owner_id(self, current_user: User) -> Optional[int]:
        """Admins see all records; others see only their own."""
        return None if current_user.role == Role.ADMIN else current_user.id

    def _get_or_404(self, tx_id: int, owner_id: Optional[int]) -> Transaction:
        tx = self.repo.get_by_id(tx_id, owner_id)
        if not tx:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Transaction {tx_id} not found.",
            )
        return tx

    # ── CRUD ──────────────────────────────────────────────────────────────────

    def create(self, payload: TransactionCreate, current_user: User) -> Transaction:
        return self.repo.create(
            owner_id=current_user.id,
            amount=payload.amount,
            type=payload.type,
            category=payload.category,
            date=payload.date,
            notes=payload.notes,
        )

    def get_one(self, tx_id: int, current_user: User) -> Transaction:
        return self._get_or_404(tx_id, self._resolve_owner_id(current_user))

    def list_all(
        self,
        current_user: User,
        filters: TransactionFilter,
        page: int,
        page_size: int,
    ) -> PaginatedTransactions:
        owner_id = self._resolve_owner_id(current_user)
        results, total = self.repo.list_transactions(owner_id, filters, page, page_size)
        return PaginatedTransactions(
            total=total,
            page=page,
            page_size=page_size,
            results=[TransactionOut.model_validate(r) for r in results],
        )

    def update(self, tx_id: int, payload: TransactionUpdate, current_user: User) -> Transaction:
        # Only admins can edit any record; others edit only their own
        owner_id = None if current_user.role == Role.ADMIN else current_user.id
        tx = self._get_or_404(tx_id, owner_id)
        updates = payload.model_dump(exclude_unset=True)
        if not updates:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="No fields provided for update.",
            )
        return self.repo.update(tx, updates)

    def delete(self, tx_id: int, current_user: User) -> None:
        tx = self._get_or_404(tx_id, None)  # admin-only endpoint, checked in router
        self.repo.delete(tx)

    # ── Analytics ─────────────────────────────────────────────────────────────

    def get_summary(self, current_user: User) -> FinancialSummary:
        owner_id = self._resolve_owner_id(current_user)

        totals = self.repo.total_by_type(owner_id)
        counts = self.repo.count_by_type(owner_id)

        total_income = totals.get(TxType.INCOME, 0.0)
        total_expense = totals.get(TxType.EXPENSE, 0.0)
        income_count = counts.get(TxType.INCOME, 0)
        expense_count = counts.get(TxType.EXPENSE, 0)

        # Category breakdowns
        income_breakdown_raw = self.repo.breakdown_by_category(TxType.INCOME, owner_id)
        expense_breakdown_raw = self.repo.breakdown_by_category(TxType.EXPENSE, owner_id)

        def to_breakdown(rows, type_total) -> list[CategoryBreakdown]:
            return [
                CategoryBreakdown(
                    category=cat,
                    total=round(tot, 2),
                    count=cnt,
                    percentage=round((tot / type_total * 100) if type_total else 0, 1),
                )
                for cat, tot, cnt in rows
            ]

        category_breakdown = (
            to_breakdown(income_breakdown_raw, total_income)
            + to_breakdown(expense_breakdown_raw, total_expense)
        )

        # Monthly totals
        monthly_raw = self.repo.monthly_totals(owner_id)
        monthly_map: dict[tuple[int, int], dict] = defaultdict(lambda: {"income": 0.0, "expense": 0.0})
        for year, month, tx_type, total in monthly_raw:
            if tx_type == TxType.INCOME:
                monthly_map[(year, month)]["income"] += total
            else:
                monthly_map[(year, month)]["expense"] += total

        monthly_totals = [
            MonthlyTotal(
                year=year,
                month=month,
                income=round(v["income"], 2),
                expense=round(v["expense"], 2),
                net=round(v["income"] - v["expense"], 2),
            )
            for (year, month), v in sorted(monthly_map.items())
        ]

        recent = self.repo.recent(owner_id, limit=5)

        return FinancialSummary(
            total_income=round(total_income, 2),
            total_expense=round(total_expense, 2),
            balance=round(total_income - total_expense, 2),
            transaction_count=income_count + expense_count,
            income_count=income_count,
            expense_count=expense_count,
            top_expense_category=expense_breakdown_raw[0][0] if expense_breakdown_raw else None,
            top_income_category=income_breakdown_raw[0][0] if income_breakdown_raw else None,
            category_breakdown=category_breakdown,
            monthly_totals=monthly_totals,
            recent_transactions=[TransactionOut.model_validate(r) for r in recent],
        )

    # ── Export ────────────────────────────────────────────────────────────────

    def export_csv(self, current_user: User, filters: TransactionFilter) -> str:
        owner_id = self._resolve_owner_id(current_user)
        records = self.repo.get_all_for_export(owner_id, filters)
        output = io.StringIO()
        writer = csv.DictWriter(
            output,
            fieldnames=["id", "date", "type", "category", "amount", "notes", "owner_id", "created_at"],
        )
        writer.writeheader()
        for r in records:
            writer.writerow({
                "id": r.id,
                "date": r.date.isoformat(),
                "type": r.type.value,
                "category": r.category,
                "amount": float(r.amount),
                "notes": r.notes or "",
                "owner_id": r.owner_id,
                "created_at": r.created_at.isoformat(),
            })
        return output.getvalue()

    def export_json(self, current_user: User, filters: TransactionFilter) -> list[dict]:
        owner_id = self._resolve_owner_id(current_user)
        records = self.repo.get_all_for_export(owner_id, filters)
        return [TransactionOut.model_validate(r).model_dump(mode="json") for r in records]
