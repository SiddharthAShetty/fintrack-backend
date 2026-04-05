"""
Auth router — /auth/register and /auth/login
"""
from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.schemas.user import UserCreate, UserOut, Token
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserOut, status_code=201, summary="Register a new user")
def register(payload: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user. Default role is **viewer**.
    Admins can pass a different role in the payload.
    """
    user = AuthService(db).register(payload)
    return user


@router.post("/login", response_model=Token, summary="Obtain JWT access token")
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    Standard OAuth2 password flow. Returns a JWT bearer token.
    Use this token in the `Authorization: Bearer <token>` header for all protected endpoints.
    """
    return AuthService(db).login(form.username, form.password)


@router.get("/me", response_model=UserOut, summary="Get current user info")
def me(current_user=Depends(get_current_user)):
    """Returns the profile of the currently authenticated user."""
    return current_user
