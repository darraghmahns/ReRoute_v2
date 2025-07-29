import secrets
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    create_access_token,
    create_user_session,
    get_current_active_user,
    get_current_active_user_by_session,
    get_password_hash,
    invalidate_session,
    verify_password,
)
from app.models.user import User, PasswordResetToken
from app.schemas.auth import (
    ChangePassword,
    PasswordReset,
    PasswordResetRequest,
    Token,
    UserLogin,
    UserRegister,
    UserResponse,
    UserUpdate,
)
from app.services.email import send_password_reset_email, send_welcome_email

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse)
def register(user_data: UserRegister, db: Session = Depends(get_db)):
    """User registration"""
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered"
        )

    # Create new user
    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        email=user_data.email,
        hashed_password=hashed_password,
        full_name=user_data.full_name,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Create corresponding profile
    from app.models.user import Profile

    new_profile = Profile(id=new_user.id, profile_completed=False)
    db.add(new_profile)
    db.commit()

    # Send welcome email
    send_welcome_email(new_user.email, new_user.full_name)

    return new_user


@router.post("/login", response_model=Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    request: Request = None,
    db: Session = Depends(get_db),
):
    """User login with session-based authentication"""
    # Authenticate user
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if user is active
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")

    # Get client info for session tracking
    user_agent = request.headers.get("User-Agent") if request else None
    ip_address = request.client.host if request and request.client else None

    # Create user session
    session = create_user_session(
        db=db, user_id=str(user.id), user_agent=user_agent, ip_address=ip_address
    )

    return {
        "access_token": session.session_token,
        "token_type": "bearer",
        "expires_in": int((session.expires_at - session.created_at).total_seconds()),
    }


@router.post("/logout")
def logout(request: Request, db: Session = Depends(get_db)):
    """User logout with session invalidation"""
    # Try to get session token from Authorization header
    authorization = request.headers.get("Authorization")
    if authorization and authorization.startswith("Bearer "):
        session_token = authorization[7:]  # Remove "Bearer " prefix
        invalidate_session(db, session_token)

    return {"message": "Successfully logged out"}


@router.post("/forgot-password")
def forgot_password(request: PasswordResetRequest, db: Session = Depends(get_db)):
    """Password reset request"""
    # Check if user exists
    user = db.query(User).filter(User.email == request.email).first()
    if not user:
        # Don't reveal if email exists or not for security
        return {
            "message": f"If an account with {request.email} exists, a password reset email has been sent."
        }

    # Generate secure reset token
    reset_token = secrets.token_urlsafe(32)
    expires_at = datetime.utcnow() + timedelta(hours=1)  # 1 hour expiration

    # Invalidate any existing reset tokens for this user
    db.query(PasswordResetToken).filter(
        PasswordResetToken.user_id == user.id, PasswordResetToken.used == False
    ).update({"used": True})

    # Create new reset token
    reset_token_obj = PasswordResetToken(
        user_id=user.id, token=reset_token, expires_at=expires_at
    )
    db.add(reset_token_obj)
    db.commit()

    # Send password reset email
    email_sent = send_password_reset_email(user.email, reset_token)

    if not email_sent:
        # Log the error but don't reveal it to the user for security
        from app.core.config import settings

        if settings.SENDGRID_API_KEY == "changeme":
            # For development/testing - return the token
            return {
                "message": f"If an account with {request.email} exists, a password reset email has been sent.",
                "reset_token": reset_token,  # Remove this in production
                "dev_note": "SendGrid not configured - token returned for testing",
            }

    return {
        "message": f"If an account with {request.email} exists, a password reset email has been sent."
    }


@router.post("/reset-password")
def reset_password(reset_data: PasswordReset, db: Session = Depends(get_db)):
    """Password reset confirmation"""
    # Find the reset token
    reset_token = (
        db.query(PasswordResetToken)
        .filter(
            PasswordResetToken.token == reset_data.token,
            PasswordResetToken.used == False,
            PasswordResetToken.expires_at > datetime.utcnow(),
        )
        .first()
    )

    if not reset_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token",
        )

    # Get the user
    user = db.query(User).filter(User.id == reset_token.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    # Update user password
    user.hashed_password = get_password_hash(reset_data.new_password)

    # Mark token as used
    reset_token.used = True

    # Invalidate all user sessions for security
    from app.models.user import UserSession

    db.query(UserSession).filter(
        UserSession.user_id == user.id, UserSession.is_active == True
    ).update({"is_active": False})

    db.commit()

    return {"message": "Password successfully reset"}


@router.get("/verify")
def verify(token: str, db: Session = Depends(get_db)):
    """Email verification"""
    # In a real implementation, you would:
    # 1. Verify token
    # 2. Mark user as verified

    return {"message": "Email verified successfully"}


@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_active_user_by_session)):
    """Current user info"""
    return current_user


@router.put("/me", response_model=UserResponse)
def update_user(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_active_user_by_session),
    db: Session = Depends(get_db),
):
    """Update current user information"""
    # Update user fields
    for field, value in user_update.dict(exclude_unset=True).items():
        setattr(current_user, field, value)

    db.commit()
    db.refresh(current_user)
    return current_user


@router.get("/me/with-profile")
def me_with_profile(
    current_user: User = Depends(get_current_active_user_by_session),
    db: Session = Depends(get_db),
):
    """Current user info with profile"""
    from app.models.user import Profile

    # Get user profile
    profile = db.query(Profile).filter(Profile.id == current_user.id).first()

    return {"user": current_user, "profile": profile}


@router.post("/change-password")
def change_password(
    password_data: ChangePassword,
    current_user: User = Depends(get_current_active_user_by_session),
    db: Session = Depends(get_db),
):
    """Change password for authenticated user"""
    # Verify current password
    if not verify_password(
        password_data.current_password, current_user.hashed_password
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )

    # Update password
    current_user.hashed_password = get_password_hash(password_data.new_password)
    db.commit()

    return {"message": "Password successfully changed"}
