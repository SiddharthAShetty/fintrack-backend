"""
User repository — thin data-access layer, no business logic here.
"""
from typing import Optional
from sqlalchemy.orm import Session

from app.models.user import User
from app.core.config import Role


class UserRepository:

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, user_id: int) -> Optional[User]:
        return self.db.query(User).filter(User.id == user_id).first()

    def get_by_username(self, username: str) -> Optional[User]:
        return self.db.query(User).filter(User.username == username).first()

    def get_by_email(self, email: str) -> Optional[User]:
        return self.db.query(User).filter(User.email == email).first()

    def get_all(self) -> list[User]:
        return self.db.query(User).order_by(User.id).all()

    def create(
        self,
        username: str,
        email: str,
        hashed_password: str,
        role: Role = Role.VIEWER,
    ) -> User:
        user = User(
            username=username,
            email=email,
            hashed_password=hashed_password,
            role=role,
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def update_role(self, user: User, role: Role) -> User:
        user.role = role
        self.db.commit()
        self.db.refresh(user)
        return user

    def set_active(self, user: User, is_active: bool) -> User:
        user.is_active = is_active
        self.db.commit()
        self.db.refresh(user)
        return user

    def delete(self, user: User) -> None:
        self.db.delete(user)
        self.db.commit()
