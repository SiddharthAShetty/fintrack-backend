"""
Transactions router — financial record CRUD, analytics, and export.

Role matrix:
  VIEWER   → GET /transactions, GET /transactions/{id}, GET /analytics/summary
  ANALYST  → all of VIEWER + export endpoints
  ADMIN    → all of ANALYST + POST, PATCH, DELETE (on any record)
"""
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse, JSONResponse
from sqlalchemy.orm import Session

from app.core.config import TxType, Role
from app.core.database import get_db
from app.core.security import get_current_user, require_role
from app.models.user import User
from app.schemas.transaction import (
    TransactionCreate,
    TransactionFilter,
    TransactionOut,
    TransactionUpdate,
    PaginatedTransactions,
    FinancialSummary,
)
from app.services.transaction_service import TransactionService

router = APIRouter(prefix="/transactions", tags=["Transactions"])
analytics_router = APIRouter(prefix="/analytics", tags=["Analytics"])


# ── Helpers ───────────────────────────────────────────────────────────────────

def _build_filter(
    type: Optional[TxType] = Query(None, description="Filter by income or expense"),
    category: Optional[str] = Query(None, description="Filter by category slug"),
    date_from: Optional[date] = Query(None, description="Filter from date (YYYY-MM-DD)"),
    date_to: Optional[date] = Query(None, description="Filter to date (YYYY-MM-DD)"),
    min_amount: Optional[float] = Query(None, gt=0, description="Minimum amount"),
    max_amount: Optional[float] = Query(None, gt=0, description="Maximum amount"),
) -> TransactionFilter:
    return TransactionFilter(
        type=type,
        category=category,
        date_from=date_from,
        date_to=date_to,
        min_amount=min_amount,
        max_amount=max_amount,
    )


# ── CRUD ──────────────────────────────────────────────────────────────────────

@router.post("", response_model=TransactionOut, status_code=201, summary="Create a transaction")
def create_transaction(
    payload: TransactionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(Role.ADMIN, Role.ANALYST)),
):
    """
    **Admin / Analyst only.** Create a new income or expense record.
    The record is automatically linked to the authenticated user.
    """
    svc = TransactionService(db)
    return svc.create(payload, current_user)


@router.get("", response_model=PaginatedTransactions, summary="List transactions")
def list_transactions(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    filters: TransactionFilter = Depends(_build_filter),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List transactions with optional filters and pagination.
    - **Admins** see all records across all users.
    - **Viewers / Analysts** see only their own records.
    """
    return TransactionService(db).list_all(current_user, filters, page, page_size)


@router.get("/{tx_id}", response_model=TransactionOut, summary="Get a single transaction")
def get_transaction(
    tx_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve a single transaction by ID. Non-admins can only access their own records."""
    return TransactionService(db).get_one(tx_id, current_user)


@router.patch("/{tx_id}", response_model=TransactionOut, summary="Update a transaction")
def update_transaction(
    tx_id: int,
    payload: TransactionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(Role.ADMIN, Role.ANALYST)),
):
    """
    Partially update a transaction. Only send the fields you want to change.
    - **Admins** can update any transaction.
    - **Analysts** can only update their own.
    """
    return TransactionService(db).update(tx_id, payload, current_user)


@router.delete("/{tx_id}", status_code=204, summary="Delete a transaction")
def delete_transaction(
    tx_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(Role.ADMIN)),
):
    """**Admin only.** Permanently delete a transaction."""
    TransactionService(db).delete(tx_id, current_user)


# ── Analytics ─────────────────────────────────────────────────────────────────

@analytics_router.get(
    "/summary",
    response_model=FinancialSummary,
    summary="Full financial summary",
)
def get_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Returns a comprehensive financial summary including:
    - Total income, expenses, and balance
    - Category-wise breakdown with percentages
    - Month-by-month totals
    - 5 most recent transactions
    """
    return TransactionService(db).get_summary(current_user)


# ── Export ────────────────────────────────────────────────────────────────────

@analytics_router.get("/export/csv", summary="Export transactions as CSV")
def export_csv(
    filters: TransactionFilter = Depends(_build_filter),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(Role.ADMIN, Role.ANALYST)),
):
    """**Analyst / Admin only.** Download all (filtered) transactions as a CSV file."""
    svc = TransactionService(db)
    csv_data = svc.export_csv(current_user, filters)
    return StreamingResponse(
        iter([csv_data]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=transactions.csv"},
    )


@analytics_router.get("/export/json", summary="Export transactions as JSON")
def export_json(
    filters: TransactionFilter = Depends(_build_filter),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(Role.ADMIN, Role.ANALYST)),
):
    """**Analyst / Admin only.** Download all (filtered) transactions as JSON."""
    svc = TransactionService(db)
    data = svc.export_json(current_user, filters)
    return JSONResponse(content=data, headers={"Content-Disposition": "attachment; filename=transactions.json"})
