"""
Users router — admin-only user management.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.config import Role
from app.core.database import get_db
from app.core.security import get_current_user, require_role
from app.models.user import User
from app.schemas.user import UserOut, UserUpdate
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["Users (Admin)"])


@router.get("", response_model=list[UserOut], summary="List all users")
def list_users(
    db: Session = Depends(get_db),
    _: User = Depends(require_role(Role.ADMIN)),
):
    """**Admin only.** List every registered user."""
    return UserService(db).list_users()


@router.get("/{user_id}", response_model=UserOut, summary="Get a user by ID")
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_role(Role.ADMIN)),
):
    """**Admin only.** Retrieve a user by their ID."""
    return UserService(db).get_user(user_id)


@router.patch("/{user_id}", response_model=UserOut, summary="Update user role or status")
def update_user(
    user_id: int,
    payload: UserUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_role(Role.ADMIN)),
):
    """**Admin only.** Update a user's role (viewer/analyst/admin) or active status."""
    return UserService(db).update_user(user_id, payload)


@router.delete("/{user_id}", status_code=204, summary="Delete a user")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(Role.ADMIN)),
):
    """**Admin only.** Permanently delete a user and all their transactions."""
    UserService(db).delete_user(user_id, current_user)
