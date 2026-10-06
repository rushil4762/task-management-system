import logging

from fastapi import HTTPException, status
from jwt.exceptions import PyJWTError
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.user import User, UserRole
from app.repositories import user_repository
from app.schemas.auth import LoginRequest, TokenResponse
from app.schemas.user import UserCreate

logger = logging.getLogger(__name__)


async def register_user(
    db: AsyncSession,
    user_data: UserCreate,
) -> User:
    normalized_email = user_data.email.strip().lower()

    # 1. Check for duplicate email
    existing_user = await user_repository.get_user_by_email(
        db=db,
        email=normalized_email,
    )
    if existing_user is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists",
        )

    # 2. Hash password securely
    password_hash = hash_password(user_data.password)

    # 3. Create and persist user entity with guaranteed EMPLOYEE role (prevent privilege escalation)
    user = User(
        name=user_data.name.strip(),
        email=normalized_email,
        password_hash=password_hash,
        role=UserRole.EMPLOYEE,
        is_active=True,
    )
    try:
        created_user = await user_repository.create_user(db=db, user=user)
        logger.info("Successfully registered user ID %s", created_user.id)
        return created_user
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists",
        )


async def authenticate_user(
    db: AsyncSession,
    login_data: LoginRequest,
) -> TokenResponse:
    normalized_email = login_data.email.strip().lower()

    user = await user_repository.get_user_by_email(
        db=db,
        email=normalized_email,
    )
    if user is None or not verify_password(login_data.password, user.password_hash):
        logger.warning("Failed login attempt for email: %s", normalized_email)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        logger.warning("Login attempt for inactive user ID: %s", user.id)
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

    logger.info("User ID %s authenticated successfully", user.id)
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
