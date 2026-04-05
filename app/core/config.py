"""
Core configuration for FinTrack.
All sensitive values should be set via environment variables in production.
"""
import os
from enum import Enum


# ── JWT ───────────────────────────────────────────────────────────────────────
SECRET_KEY: str = os.getenv("SECRET_KEY", "fintrack-super-secret-change-in-prod")
ALGORITHM: str = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("TOKEN_EXPIRE_MINUTES", "60"))

# ── Database ──────────────────────────────────────────────────────────────────
DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./fintrack.db")

# ── Roles ─────────────────────────────────────────────────────────────────────
class Role(str, Enum):
    VIEWER   = "viewer"    # read-only: records + summaries
    ANALYST  = "analyst"   # viewer + filters + detailed insights + export
    ADMIN    = "admin"     # full CRUD + user management

# ── Transaction types & categories ───────────────────────────────────────────
class TxType(str, Enum):
    INCOME  = "income"
    EXPENSE = "expense"

CATEGORIES: list[str] = [
    "salary", "freelance", "investment", "gift", "other_income",
    "food", "transport", "utilities", "rent", "health",
    "entertainment", "education", "shopping", "other_expense",
]
