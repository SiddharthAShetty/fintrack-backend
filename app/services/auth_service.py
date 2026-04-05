"""
Auth service — registration and login business logic.
"""
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import ACCESS_TOKEN_EXPIRE_MINUTES
from app.core.security import hash_password, verify_password, create_access_token
from app.repositories.user_repo import UserRepository
from app.schemas.user import UserCreate, Token
from app.models.user import User


class AuthService:

    def __init__(self, db: Session) -> None:
        self.repo = UserRepository(db)

    def register(self, payload: UserCreate) -> User:
        if self.repo.get_by_username(payload.username):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Username '{payload.username}' is already taken.",
            )
        if self.repo.get_by_email(payload.email):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Email '{payload.email}' is already registered.",
            )
        return self.repo.create(
            username=payload.username,
            email=payload.email,
            hashed_password=hash_password(payload.password),
            role=payload.role,
        )

    def login(self, username: str, password: str) -> Token:
        user = self.repo.get_by_username(username)
        if not user or not verify_password(password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This account has been deactivated.",
            )
        token = create_access_token({"sub": str(user.id), "role": user.role})
        return Token(access_token=token, token_type="bearer", expires_in_minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
