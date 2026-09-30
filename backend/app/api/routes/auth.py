import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select

from app.api.deps import CurrentUserDep, SessionDep
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_password_hash,
    verify_password,
)
from app.models.user import User
from app.schemas.auth import (
    ForgotPasswordRequest,
    RefreshTokenRequest,
    ResetPasswordRequest,
    Token,
    UserLogin,
    UserRegister,
)
from app.schemas.common import MessageResponse
from app.schemas.user import UserRead
from app.utils.enums import UserRole

router = APIRouter(prefix="/auth")


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register(
    user_in: UserRegister,
    db: SessionDep,
) -> User:
    existing = db.scalar(select(User).where(User.email == user_in.email))
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists",
        )

    user = User(
        name=user_in.name,
        email=user_in.email,
        password_hash=get_password_hash(user_in.password),
        role=user_in.role or UserRole.USER,
        is_active=True,
        is_verified=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=Token)
def login(
    db: SessionDep,
    form_data: OAuth2PasswordRequestForm = Depends(),
) -> Token:
    user = db.scalar(select(User).where(User.email == form_data.username))
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User account is inactive",
        )

    access_token = create_access_token(user.id, extra_claims={"role": user.role.value})
    refresh_token = create_refresh_token(user.id)

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        user_id=user.id,
        email=user.email,
        role=user.role,
    )


@router.post("/refresh", response_model=Token)
def refresh_token(
    refresh_in: RefreshTokenRequest,
    db: SessionDep,
) -> Token:
    payload = decode_token(refresh_in.refresh_token)
    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    user_id = uuid.UUID(payload.get("sub"))
    user = db.get(User, user_id)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    access_token = create_access_token(user.id, extra_claims={"role": user.role.value})
    new_refresh = create_refresh_token(user.id)

    return Token(
        access_token=access_token,
        refresh_token=new_refresh,
        token_type="bearer",
        user_id=user.id,
        email=user.email,
        role=user.role,
    )


@router.post("/logout", response_model=MessageResponse)
def logout(current_user: CurrentUserDep) -> MessageResponse:
    return MessageResponse(message="Successfully logged out")


@router.post("/forgot-password", response_model=MessageResponse)
def forgot_password(
    forgot_in: ForgotPasswordRequest,
    db: SessionDep,
) -> MessageResponse:
    user = db.scalar(select(User).where(User.email == forgot_in.email))
    # Return success regardless of existence to avoid email enumeration
    return MessageResponse(
        message="If this email is registered, password reset instructions have been sent"
    )


@router.post("/reset-password", response_model=MessageResponse)
def reset_password(
    reset_in: ResetPasswordRequest,
    db: SessionDep,
) -> MessageResponse:
    payload = decode_token(reset_in.token)
    user_id = uuid.UUID(payload.get("sub"))
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid token or user not found",
        )

    user.password_hash = get_password_hash(reset_in.new_password)
    db.commit()
    return MessageResponse(message="Password reset successfully")


@router.get("/me", response_model=UserRead)
def get_auth_me(current_user: CurrentUserDep) -> User:
    return current_user
