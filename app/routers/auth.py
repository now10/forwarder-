from datetime import timedelta
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app import crud, models, schemas
from app.api.deps import get_db, get_current_user
from app.core.security import security
from app.core.config import settings
from app.utils.email import send_verification_email, send_password_reset_email

router = APIRouter()
logger = structlog.get_logger()


@router.post("/register", response_model=schemas.UserResponse)
async def register(
    *,
    db: AsyncSession = Depends(get_db),
    user_in: schemas.UserCreate,
    background_tasks: BackgroundTasks
) -> Any:
    """
    Register new user.
    """
    try:
        user = await crud.crud_user.create(db, obj_in=user_in)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    # Send verification email in background
    background_tasks.add_task(
        send_verification_email,
        email_to=user.email,
        username=user.full_name or user.email,
        token=user.verification_token
    )
    
    return user


@router.post("/login", response_model=schemas.Token)
async def login(
    db: AsyncSession = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    """
    OAuth2 compatible token login, get an access token for future requests.
    """
    user = await crud.crud_user.get_by_email(db, email=form_data.username)
    
    if not user or not security.verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    # Update last login
    user.last_login = datetime.utcnow()
    db.add(user)
    await db.commit()
    
    # Create tokens
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    access_token = security.create_access_token(
        subject=str(user.id), expires_delta=access_token_expires
    )
    refresh_token = security.create_refresh_token(
        subject=str(user.id), expires_delta=refresh_token_expires
    )
    
    logger.info("User logged in", user_id=str(user.id), email=user.email)
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


@router.post("/refresh", response_model=schemas.Token)
async def refresh_token(
    refresh_token: str,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Refresh access token using refresh token.
    """
    user_id = security.verify_token(refresh_token)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    user = await crud.crud_user.get(db, user_id)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    
    # Create new tokens
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    new_access_token = security.create_access_token(
        subject=str(user.id), expires_delta=access_token_expires
    )
    new_refresh_token = security.create_refresh_token(
        subject=str(user.id), expires_delta=refresh_token_expires
    )
    
    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer"
    }


@router.post("/verify-email")
async def verify_email(
    token_in: schemas.VerificationRequest,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Verify email with token.
    """
    user = await crud.crud_user.verify_email(db, token=token_in.token)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token"
        )
    
    logger.info("Email verified", user_id=str(user.id))
    
    return {"message": "Email verified successfully"}


@router.post("/resend-verification")
async def resend_verification(
    email_in: schemas.ResetPasswordRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Resend verification email.
    """
    user = await crud.crud_user.get_by_email(db, email=email_in.email)
    
    if not user:
        # Don't reveal if user exists or not
        return {"message": "If your email exists, you will receive a verification link"}
    
    if user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already verified"
        )
    
    # Create new verification token
    user.verification_token = security.create_verification_token(user.email)
    user.verification_expires = datetime.utcnow() + timedelta(hours=24)
    
    db.add(user)
    await db.commit()
    
    # Send verification email
    background_tasks.add_task(
        send_verification_email,
        email_to=user.email,
        username=user.full_name or user.email,
        token=user.verification_token
    )
    
    return {"message": "Verification email sent"}


@router.post("/forgot-password")
async def forgot_password(
    email_in: schemas.ResetPasswordRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Request password reset.
    """
    user = await crud.crud_user.get_by_email(db, email=email_in.email)
    
    if user and user.is_active:
        reset_token = security.create_password_reset_token(email=user.email)
        
        background_tasks.add_task(
            send_password_reset_email,
            email_to=user.email,
            username=user.full_name or user.email,
            token=reset_token
        )
    
    # Always return same message for security
    return {"message": "If your email exists, you will receive a password reset link"}


@router.post("/reset-password")
async def reset_password(
    password_in: schemas.NewPasswordRequest,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Reset password with token.
    """
    email = security.verify_password_reset_token(password_in.token)
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )
    
    user = await crud.crud_user.get_by_email(db, email=email)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Update password
    await crud.crud_user.update_password(db, user.id, password_in.new_password)
    
    logger.info("Password reset", user_id=str(user.id))
    
    return {"message": "Password updated successfully"}


@router.post("/logout")
async def logout(
    current_user: models.User = Depends(get_current_user)
) -> Any:
    """
    Logout user (client should discard tokens).
    """
    # In a stateless JWT system, logout is handled client-side
    # But we can blacklist tokens if needed (would require Redis)
    return {"message": "Successfully logged out"}


@router.get("/me", response_model=schemas.UserResponse)
async def read_users_me(
    current_user: models.User = Depends(get_current_user)
) -> Any:
    """
    Get current user.
    """
    return current_user


@router.put("/me", response_model=schemas.UserResponse)
async def update_user_me(
    *,
    db: AsyncSession = Depends(get_db),
    user_in: schemas.UserUpdate,
    current_user: models.User = Depends(get_current_user)
) -> Any:
    """
    Update own user.
    """
    user = await crud.crud_user.update(db, db_obj=current_user, obj_in=user_in)
    return user


@router.put("/change-password")
async def change_password(
    *,
    db: AsyncSession = Depends(get_db),
    old_password: str,
    new_password: str,
    current_user: models.User = Depends(get_current_user)
) -> Any:
    """
    Change password.
    """
    if not security.verify_password(old_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect old password"
        )
    
    user = await crud.crud_user.update_password(db, current_user.id, new_password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to update password"
        )
    
    return {"message": "Password updated successfully"}