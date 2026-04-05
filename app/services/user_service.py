"""
User management service — admin-only operations.
"""
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.repositories.user_repo import UserRepository
from app.schemas.user import UserUpdate
from app.models.user import User


class UserService:

    def __init__(self, db: Session) -> None:
        self.repo = UserRepository(db)

    def _get_or_404(self, user_id: int) -> User:
        user = self.repo.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User {user_id} not found.",
            )
        return user

    def list_users(self) -> list[User]:
        return self.repo.get_all()

    def get_user(self, user_id: int) -> User:
        return self._get_or_404(user_id)

    def update_user(self, user_id: int, payload: UserUpdate) -> User:
        user = self._get_or_404(user_id)
        if payload.role is not None:
            self.repo.update_role(user, payload.role)
        if payload.is_active is not None:
            self.repo.set_active(user, payload.is_active)
        return user

    def delete_user(self, user_id: int, current_user: User) -> None:
        if user_id == current_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You cannot delete your own account.",
            )
        user = self._get_or_404(user_id)
        self.repo.delete(user)
