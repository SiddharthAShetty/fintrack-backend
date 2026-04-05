"""
FinTrack — Python-based Finance System Backend
Built with FastAPI + SQLAlchemy + SQLite + JWT Auth

Entry point: uvicorn app.main:app --reload
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.openapi.utils import get_openapi

from app.core.database import engine, Base
from app.routers.auth import router as auth_router
from app.routers.transactions import router as tx_router, analytics_router
from app.routers.users import router as users_router

# ── Import models so SQLAlchemy registers them ────────────────────────────────
import app.models.user        # noqa: F401
import app.models.transaction  # noqa: F401


# ── Lifespan (startup / shutdown) ─────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create all tables on startup
    Base.metadata.create_all(bind=engine)
    yield
    # (teardown here if needed)


# ── App factory ───────────────────────────────────────────────────────────────

app = FastAPI(
    title="FinTrack API",
    description="""
## 💰 FinTrack — Personal Finance Tracking System

A clean, role-based REST API for managing financial records, generating analytics,
and exporting data.

### Roles
| Role     | Capabilities                                                    |
|----------|-----------------------------------------------------------------|
| viewer   | Read transactions & summaries (own records only)                |
| analyst  | Viewer + detailed filters + CSV/JSON export (own records)       |
| admin    | Full CRUD on all records + user management                      |

### Quick Start
1. **Register** via `POST /auth/register`
2. **Login** via `POST /auth/login` to get your JWT
3. Click **Authorize** above and paste: `Bearer <your_token>`
4. Explore the endpoints!

> 💡 Seed data is available — run `python -m app.seed` for demo users.
    """,
    version="1.0.0",
    contact={"name": "Siddharth A Shetty", "email": "siddharthshetty521@gmail.com"},
    license_info={"name": "MIT"},
    lifespan=lifespan,
)

# ── CORS ──────────────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Custom validation error handler (cleaner 422 messages) ───────────────────

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = []
    for error in exc.errors():
        field = " → ".join(str(loc) for loc in error["loc"] if loc != "body")
        errors.append({"field": field or "body", "message": error["msg"]})
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": "Validation failed.", "errors": errors},
    )


# ── Routers ───────────────────────────────────────────────────────────────────

app.include_router(auth_router)
app.include_router(tx_router)
app.include_router(analytics_router)
app.include_router(users_router)


# ── Health check ──────────────────────────────────────────────────────────────

@app.get("/health", tags=["System"], summary="Health check")
def health():
    """Returns API status. Useful for uptime monitoring."""
    return {"status": "ok", "service": "FinTrack API", "version": "1.0.0"}


@app.get("/", tags=["System"], include_in_schema=False)
def root():
    return {"message": "FinTrack API is running. Visit /docs for the interactive API documentation."}


# ── Custom OpenAPI schema — adds the Bearer token input box ──────────────────

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "Paste your JWT token here. Get it from POST /auth/login",
        }
    }
    for path in schema.get("paths", {}).values():
        for method in path.values():
            method["security"] = [{"BearerAuth": []}]
    app.openapi_schema = schema
    return schema

app.openapi = custom_openapi