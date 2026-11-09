import uuid
from datetime import datetime, timezone, timedelta
from typing import Tuple
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.config import settings
from backend.app.core.security import get_password_hash, verify_password, create_access_token, create_refresh_token, decode_token
from backend.app.models.user import User, RefreshToken

class AuthService:
    @staticmethod
    async def register_user(db: AsyncSession, email: str, password: str, full_name: str, phone: str = None) -> User:
        stmt = select(User).where(User.email == email.lower())
        res = await db.execute(stmt)
        if res.scalar_one_or_none():
            raise ValueError("Email already registered")

        user = User(
            email=email.lower(),
            hashed_password=get_password_hash(password),
            full_name=full_name,
            phone=phone,
            is_active=True,
            is_verified=True
        )
        db.add(user)
        await db.flush()
        return user

    @staticmethod
    async def authenticate_user(db: AsyncSession, email: str, password: str) -> User:
        stmt = select(User).where(User.email == email.lower())
        res = await db.execute(stmt)
        user = res.scalar_one_or_none()
        if not user or not verify_password(password, user.hashed_password):
            raise ValueError("Invalid credentials")
        if not user.is_active:
            raise ValueError("Account is disabled")
        return user

    @staticmethod
    async def create_tokens(db: AsyncSession, user: User) -> Tuple[str, str]:
        access_token = create_access_token(subject=str(user.id))
        refresh_token_str = create_refresh_token(subject=str(user.id))
        refresh_rec = RefreshToken(
            user_id=user.id,
            token_hash=get_password_hash(refresh_token_str[-32:]),
            expires_at=datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        )
        db.add(refresh_rec)
        await db.flush()
        return access_token, refresh_token_str

    @staticmethod
    async def refresh_access_token(db: AsyncSession, refresh_token_str: str) -> Tuple[str, User]:
        payload = decode_token(refresh_token_str)
        if payload.get("type") != "refresh":
            raise ValueError("Invalid token type")
        user_id = uuid.UUID(payload["sub"])
        user = await db.get(User, user_id)
        if not user or not user.is_active:
            raise ValueError("User not found or inactive")
        return create_access_token(subject=str(user.id)), user
