"""
Pydantic v2 schemas for Transaction CRUD, filtering, and analytics responses.
"""
from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator, model_validator

from app.core.config import TxType, CATEGORIES


# ── Create / Update ───────────────────────────────────────────────────────────

class TransactionCreate(BaseModel):
    amount: float = Field(..., gt=0, description="Must be a positive number.")
    type: TxType
    category: str = Field(..., examples=["food"])
    date: date
    notes: Optional[str] = Field(None, max_length=500)

    @field_validator("category")
    @classmethod
    def validate_category(cls, v: str) -> str:
        v = v.lower().strip()
        if v not in CATEGORIES:
            raise ValueError(
                f"Invalid category '{v}'. Valid options: {CATEGORIES}"
            )
        return v

    @model_validator(mode="after")
    def check_category_matches_type(self) -> "TransactionCreate":
        income_cats = {"salary", "freelance", "investment", "gift", "other_income"}
        expense_cats = {
            "food", "transport", "utilities", "rent", "health",
            "entertainment", "education", "shopping", "other_expense",
        }
        if self.type == TxType.INCOME and self.category in expense_cats:
            raise ValueError(
                f"Category '{self.category}' is an expense category. "
                "Use an income category for income transactions."
            )
        if self.type == TxType.EXPENSE and self.category in income_cats:
            raise ValueError(
                f"Category '{self.category}' is an income category. "
                "Use an expense category for expense transactions."
            )
        return self


class TransactionUpdate(BaseModel):
    amount: Optional[float] = Field(None, gt=0)
    type: Optional[TxType] = None
    category: Optional[str] = None
    date: Optional[date] = None
    notes: Optional[str] = Field(None, max_length=500)

    @field_validator("category")
    @classmethod
    def validate_category(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.lower().strip()
        if v not in CATEGORIES:
            raise ValueError(f"Invalid category '{v}'. Valid options: {CATEGORIES}")
        return v


# ── Response ──────────────────────────────────────────────────────────────────

class TransactionOut(BaseModel):
    id: int
    amount: float
    type: TxType
    category: str
    date: date
    notes: Optional[str]
    owner_id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── Filter params (used as query params in the list endpoint) ─────────────────

class TransactionFilter(BaseModel):
    type: Optional[TxType] = None
    category: Optional[str] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    min_amount: Optional[float] = Field(None, gt=0)
    max_amount: Optional[float] = Field(None, gt=0)


# ── Paginated response wrapper ────────────────────────────────────────────────

class PaginatedTransactions(BaseModel):
    total: int
    page: int
    page_size: int
    results: list[TransactionOut]


# ── Analytics / Summary schemas ───────────────────────────────────────────────

class CategoryBreakdown(BaseModel):
    category: str
    total: float
    count: int
    percentage: float  # % of its type (income or expense)


class MonthlyTotal(BaseModel):
    year: int
    month: int
    income: float
    expense: float
    net: float


class FinancialSummary(BaseModel):
    total_income: float
    total_expense: float
    balance: float
    transaction_count: int
    income_count: int
    expense_count: int
    top_expense_category: Optional[str]
    top_income_category: Optional[str]
    category_breakdown: list[CategoryBreakdown]
    monthly_totals: list[MonthlyTotal]
    recent_transactions: list[TransactionOut]
