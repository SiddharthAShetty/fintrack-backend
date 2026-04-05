# 💰 FinTrack — Python-Based Finance System Backend

A clean, production-ready **FastAPI** backend for tracking personal and organizational financial records — with role-based access control, analytics, CSV/JSON export, JWT authentication, and a full test suite.

---

## ✨ What Makes This Stand Out

| Feature | Details |
|---|---|
| **Layered architecture** | Router → Service → Repository → Model — clean separation of concerns |
| **Role-based JWT auth** | Viewer / Analyst / Admin with per-endpoint enforcement |
| **Rich analytics** | Balance, category breakdown with %, monthly net totals, recent activity |
| **Type-safe validation** | Pydantic v2 with cross-field validators (e.g. category must match transaction type) |
| **CSV + JSON export** | Filterable exports available to Analyst and Admin roles |
| **Full test suite** | 40+ pytest tests covering all routes, roles, and edge cases |
| **Auto API docs** | Swagger UI at `/docs`, ReDoc at `/redoc` — zero extra work |
| **Seed script** | One command populates the DB with 4 demo users and 160 realistic transactions |
| **Clean error responses** | Custom 422 handler returns field-level error messages in plain English |

---

## 🏗️ Architecture

```
fintrack/
├── app/
│   ├── main.py                  # FastAPI app factory + lifespan + error handlers
│   ├── seed.py                  # Demo data seeder
│   ├── core/
│   │   ├── config.py            # Enums, constants, environment config
│   │   ├── database.py          # SQLAlchemy engine + session + Base
│   │   └── security.py          # JWT creation/decoding + role-enforcement deps
│   ├── models/
│   │   ├── user.py              # User ORM model
│   │   └── transaction.py       # Transaction ORM model
│   ├── schemas/
│   │   ├── user.py              # Pydantic schemas: register, response, update
│   │   └── transaction.py       # Pydantic schemas: CRUD, filters, analytics
│   ├── repositories/
│   │   ├── user_repo.py         # Raw DB access for users
│   │   └── transaction_repo.py  # Raw DB access + aggregations for transactions
│   ├── services/
│   │   ├── auth_service.py      # Registration + login logic
│   │   ├── transaction_service.py # CRUD + analytics + export logic
│   │   └── user_service.py      # Admin user management logic
│   └── routers/
│       ├── auth.py              # /auth/* endpoints
│       ├── transactions.py      # /transactions/* + /analytics/* endpoints
│       └── users.py             # /users/* endpoints (admin only)
└── tests/
    ├── conftest.py              # Fixtures: test DB, client, users, tokens
    ├── test_auth.py             # 12 auth tests
    ├── test_transactions.py     # 23 transaction + analytics tests
    └── test_users.py            # 10 user management tests
```

---

## 🚀 Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Seed the database with demo data

```bash
python -m app.seed
```

This creates 4 users and ~160 realistic transactions spread over the past year.

### 3. Start the server

```bash
uvicorn app.main:app --reload
```

The API is now live at **http://localhost:8000**

### 4. Explore the interactive docs

Open **http://localhost:8000/docs** in your browser — full Swagger UI with try-it-out for every endpoint.

---

## 🔑 Demo Credentials

| Username | Password     | Role    |
|----------|--------------|---------|
| admin    | Admin@1234   | admin   |
| analyst  | Analyst@1234 | analyst |
| alice    | Alice@1234   | viewer  |
| bob      | Bob@12345    | viewer  |

**To authenticate in Swagger UI:**
1. `POST /auth/login` → copy the `access_token`
2. Click **Authorize** (top right) → enter `Bearer <token>`

---

## 🛡️ Role Matrix

| Endpoint | Viewer | Analyst | Admin |
|---|:---:|:---:|:---:|
| `GET /transactions` | ✅ (own) | ✅ (own) | ✅ (all) |
| `GET /transactions/{id}` | ✅ (own) | ✅ (own) | ✅ (all) |
| `POST /transactions` | ❌ | ✅ | ✅ |
| `PATCH /transactions/{id}` | ❌ | ✅ (own) | ✅ (all) |
| `DELETE /transactions/{id}` | ❌ | ❌ | ✅ |
| `GET /analytics/summary` | ✅ | ✅ | ✅ |
| `GET /analytics/export/csv` | ❌ | ✅ | ✅ |
| `GET /analytics/export/json` | ❌ | ✅ | ✅ |
| `GET /users` | ❌ | ❌ | ✅ |
| `PATCH /users/{id}` | ❌ | ❌ | ✅ |
| `DELETE /users/{id}` | ❌ | ❌ | ✅ |

---

## 📡 API Reference

### Authentication

```
POST /auth/register    Register a new user
POST /auth/login       Get JWT access token (OAuth2 password form)
GET  /auth/me          Get current user profile
```

### Transactions

```
POST   /transactions             Create a transaction
GET    /transactions             List transactions (paginated + filterable)
GET    /transactions/{id}        Get single transaction
PATCH  /transactions/{id}        Partially update a transaction
DELETE /transactions/{id}        Delete a transaction (admin only)
```

**Filter query params:** `type`, `category`, `date_from`, `date_to`, `min_amount`, `max_amount`

**Pagination:** `page` (default: 1), `page_size` (default: 20, max: 100)

### Analytics

```
GET /analytics/summary       Full financial summary
GET /analytics/export/csv    Download transactions as CSV
GET /analytics/export/json   Download transactions as JSON
```

### User Management (Admin only)

```
GET    /users          List all users
GET    /users/{id}     Get a user by ID
PATCH  /users/{id}     Update role or active status
DELETE /users/{id}     Delete a user
```

### System

```
GET /health    Health check
GET /docs      Swagger UI
GET /redoc     ReDoc
```

---

## 📊 Financial Summary Response

```json
{
  "total_income": 125000.00,
  "total_expense": 43500.00,
  "balance": 81500.00,
  "transaction_count": 34,
  "income_count": 12,
  "expense_count": 22,
  "top_expense_category": "rent",
  "top_income_category": "salary",
  "category_breakdown": [
    { "category": "rent", "total": 18000.00, "count": 3, "percentage": 41.4 },
    ...
  ],
  "monthly_totals": [
    { "year": 2025, "month": 1, "income": 55000.0, "expense": 12000.0, "net": 43000.0 },
    ...
  ],
  "recent_transactions": [...]
}
```

---

## 🧪 Running Tests

```bash
pytest -v
```

Expected output: **40+ tests, all passing** across auth, transactions, analytics, and user management.

To run a specific module:
```bash
pytest tests/test_transactions.py -v
pytest tests/test_auth.py -v
```

---

## ✅ Validation Rules

- `amount` must be **greater than 0**
- `category` must be one of the predefined slugs (see below)
- Category must **match the transaction type** — e.g. `food` is an expense category and cannot be used with `type: income`
- `notes` max 500 characters
- `page_size` max 100

**Valid income categories:** `salary`, `freelance`, `investment`, `gift`, `other_income`

**Valid expense categories:** `food`, `transport`, `utilities`, `rent`, `health`, `entertainment`, `education`, `shopping`, `other_expense`

---

## ⚙️ Configuration

All config via environment variables (`.env` supported):

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./fintrack.db` | Any SQLAlchemy-compatible URL |
| `SECRET_KEY` | `fintrack-super-secret-...` | JWT signing key — **change in production** |
| `TOKEN_EXPIRE_MINUTES` | `60` | JWT token lifetime |

To use PostgreSQL:
```bash
DATABASE_URL=postgresql://user:pass@localhost/fintrack uvicorn app.main:app
```

---

## 🧱 Assumptions

1. **Single-user transactions:** Each transaction is owned by the user who creates it. Admins can view and manage all records.
2. **Soft role management:** Only admins can promote/demote users — self-promotion is not possible.
3. **No soft delete:** Deletion is permanent. Add a `deleted_at` field if soft-delete is required.
4. **Token-based auth only:** No refresh tokens in this version — tokens expire after 60 minutes.
5. **UTC timestamps:** All timestamps are stored in UTC.

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Framework | FastAPI 0.111 |
| Database | SQLite (configurable to PostgreSQL/MySQL) |
| ORM | SQLAlchemy 2.0 (Mapped / DeclarativeBase) |
| Validation | Pydantic v2 |
| Auth | JWT via python-jose + passlib bcrypt |
| Testing | pytest + httpx TestClient |
| Docs | Auto-generated Swagger UI + ReDoc |
