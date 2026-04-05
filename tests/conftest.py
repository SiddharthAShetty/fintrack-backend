"""
Test configuration and shared fixtures.
Uses an in-memory SQLite database — fully isolated from the real DB.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base, get_db
from app.core.security import hash_password
from app.core.config import Role
from app.main import app
from app.models.user import User
from app.models.transaction import Transaction  # noqa: F401 — register with Base

TEST_DATABASE_URL = "sqlite:///./test_fintrack.db"

engine_test = create_engine(
    TEST_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine_test)


@pytest.fixture(scope="function", autouse=True)
def setup_db():
    """Create all tables before each test, drop after."""
    Base.metadata.create_all(bind=engine_test)
    yield
    Base.metadata.drop_all(bind=engine_test)


@pytest.fixture(scope="function")
def db():
    """Yield a test database session."""
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="function")
def client(db):
    """TestClient with the test DB injected via dependency override."""
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# ── Convenience fixtures ───────────────────────────────────────────────────────

def _create_user(db, username, email, password, role) -> User:
    user = User(
        username=username,
        email=email,
        hashed_password=hash_password(password),
        role=role,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _get_token(client, username, password) -> str:
    resp = client.post(
        "/auth/login",
        data={"username": username, "password": password},
    )
    return resp.json()["access_token"]


@pytest.fixture
def admin_user(db):
    return _create_user(db, "admin", "admin@test.com", "Admin@1234", Role.ADMIN)


@pytest.fixture
def analyst_user(db):
    return _create_user(db, "analyst", "analyst@test.com", "Analyst@1234", Role.ANALYST)


@pytest.fixture
def viewer_user(db):
    return _create_user(db, "viewer", "viewer@test.com", "Viewer@1234", Role.VIEWER)


@pytest.fixture
def admin_token(client, admin_user):
    return _get_token(client, "admin", "Admin@1234")


@pytest.fixture
def analyst_token(client, analyst_user):
    return _get_token(client, "analyst", "Analyst@1234")


@pytest.fixture
def viewer_token(client, viewer_user):
    return _get_token(client, "viewer", "Viewer@1234")


@pytest.fixture
def auth_header_admin(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture
def auth_header_analyst(analyst_token):
    return {"Authorization": f"Bearer {analyst_token}"}


@pytest.fixture
def auth_header_viewer(viewer_token):
    return {"Authorization": f"Bearer {viewer_token}"}
