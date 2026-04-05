"""
Seed script — populates the database with realistic demo data.
Run:  python -m app.seed
"""
import random
from datetime import date, timedelta

from app.core.database import SessionLocal, engine, Base
from app.core.security import hash_password
from app.core.config import Role, TxType
from app.models.user import User
from app.models.transaction import Transaction

# ── Import models so Base knows about them ────────────────────────────────────
import app.models.user        # noqa: F401
import app.models.transaction  # noqa: F401


INCOME_CATEGORIES = ["salary", "freelance", "investment", "gift"]
EXPENSE_CATEGORIES = [
    "food", "transport", "utilities", "rent", "health",
    "entertainment", "education", "shopping",
]

NOTES = {
    "salary": ["Monthly salary credit", "Salary for the month"],
    "freelance": ["Client project payment", "Consulting invoice"],
    "investment": ["Dividend payout", "SIP return"],
    "gift": ["Birthday gift", "Festival bonus"],
    "food": ["Swiggy order", "Groceries", "Restaurant dinner"],
    "transport": ["Uber ride", "Monthly bus pass", "Ola cab"],
    "utilities": ["Electricity bill", "Internet bill", "Water bill"],
    "rent": ["Monthly rent payment"],
    "health": ["Pharmacy", "Doctor consultation", "Gym membership"],
    "entertainment": ["Netflix", "Movie tickets", "Spotify"],
    "education": ["Udemy course", "Book purchase"],
    "shopping": ["Amazon order", "Flipkart order", "Clothes"],
}


def random_date(start: date, end: date) -> date:
    delta = (end - start).days
    return start + timedelta(days=random.randint(0, delta))


def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    # ── Skip if already seeded ────────────────────────────────────────────────
    if db.query(User).count() > 0:
        print("⚡  Database already seeded — skipping.")
        db.close()
        return

    print("🌱  Seeding database...")

    # ── Users ─────────────────────────────────────────────────────────────────
    users = [
        User(username="admin",   email="admin@fintrack.io",   hashed_password=hash_password("Admin@1234"),   role=Role.ADMIN),
        User(username="analyst", email="analyst@fintrack.io", hashed_password=hash_password("Analyst@1234"), role=Role.ANALYST),
        User(username="alice",   email="alice@fintrack.io",   hashed_password=hash_password("Alice@1234"),   role=Role.VIEWER),
        User(username="bob",     email="bob@fintrack.io",     hashed_password=hash_password("Bob@12345"),    role=Role.VIEWER),
    ]
    db.add_all(users)
    db.commit()
    for u in users:
        db.refresh(u)

    # ── Transactions ──────────────────────────────────────────────────────────
    end_date   = date.today()
    start_date = date(end_date.year - 1, end_date.month, 1)

    transactions = []
    for user in users:
        # Give each user ~40 transactions spread over the last 12 months
        for _ in range(40):
            is_income = random.random() < 0.35  # ~35% income
            if is_income:
                cat    = random.choice(INCOME_CATEGORIES)
                tx_type = TxType.INCOME
                amount  = round(random.uniform(5000, 80000), 2)
            else:
                cat    = random.choice(EXPENSE_CATEGORIES)
                tx_type = TxType.EXPENSE
                amount  = round(random.uniform(100, 15000), 2)

            note = random.choice(NOTES.get(cat, ["Transaction"]))
            transactions.append(
                Transaction(
                    owner_id=user.id,
                    amount=amount,
                    type=tx_type,
                    category=cat,
                    date=random_date(start_date, end_date),
                    notes=note,
                )
            )

    db.add_all(transactions)
    db.commit()
    db.close()

    total_tx = len(transactions)
    print(f"✅  Seeded {len(users)} users and {total_tx} transactions.")
    print()
    print("  Demo credentials:")
    print("  ┌──────────┬──────────────┬──────────┐")
    print("  │ Username │ Password     │ Role     │")
    print("  ├──────────┼──────────────┼──────────┤")
    print("  │ admin    │ Admin@1234   │ admin    │")
    print("  │ analyst  │ Analyst@1234 │ analyst  │")
    print("  │ alice    │ Alice@1234   │ viewer   │")
    print("  │ bob      │ Bob@12345    │ viewer   │")
    print("  └──────────┴──────────────┴──────────┘")


if __name__ == "__main__":
    seed()
