from datetime import timedelta
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
from app.models.user import User
from app.schemas.auth import (
    PasswordReset,
    PasswordResetRequest,
    Token,
    UserLogin,
    UserRegister,
    UserResponse,
    UserUpdate,
)

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
        return {"message": f"Password reset email sent to {request.email}"}

    # In a real implementation, you would:
    # 1. Generate reset token
    # 2. Send email with reset link
    # 3. Store reset token with expiration

    return {"message": f"Password reset email sent to {request.email}"}


@router.post("/reset-password")
def reset_password(reset_data: PasswordReset, db: Session = Depends(get_db)):
    """Password reset confirmation"""
    # In a real implementation, you would:
    # 1. Verify reset token
    # 2. Check token expiration
    # 3. Update user password
    # 4. Invalidate reset token

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
