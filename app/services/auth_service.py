from fastapi import HTTPException, status
from jwt.exceptions import PyJWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.user import User
from app.repositories import user_repository
from app.schemas.auth import LoginRequest, TokenResponse
from app.schemas.user import UserCreate


async def register_user(
    db: AsyncSession,
    user_data: UserCreate,
) -> User:
    # 1. Check for duplicate email
    existing_user = await user_repository.get_user_by_email(
        db=db,
        email=user_data.email,
    )
    if existing_user is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists",
        )

    # 2. Hash password securely
    password_hash = hash_password(user_data.password)

    # 3. Create and persist user entity
    user = User(
        name=user_data.name,
        email=user_data.email.strip().lower(),
        password_hash=password_hash,
        is_active=True,
    )
    return await user_repository.create_user(db=db, user=user)


async def authenticate_user(
    db: AsyncSession,
    login_data: LoginRequest,
) -> TokenResponse:
    user = await user_repository.get_user_by_email(
        db=db,
        email=login_data.email,
    )
    if user is None or not verify_password(login_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )

    access_token = create_access_token(
        subject=user.id,
        extra_claims={"email": user.email},
    )
    refresh_token = create_refresh_token(
        subject=user.id,
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
    )


async def refresh_access_token(
    db: AsyncSession,
    refresh_token: str,
) -> TokenResponse:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired refresh token",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_token(refresh_token)
        token_type: str | None = payload.get("type")
        sub: str | None = payload.get("sub")
        if token_type != "refresh" or sub is None:
            raise credentials_exception
        user_id = int(sub)
    except (PyJWTError, ValueError):
        raise credentials_exception

    user = await user_repository.get_user_by_id(db=db, user_id=user_id)
    if user is None or not user.is_active:
        raise credentials_exception

    new_access_token = create_access_token(
        subject=user.id,
        extra_claims={"email": user.email},
    )
    new_refresh_token = create_refresh_token(
        subject=user.id,
    )

    return TokenResponse(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
    )
