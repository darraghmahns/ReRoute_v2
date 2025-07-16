from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
from app.schemas.auth import UserRegister, UserLogin, UserResponse, Token, PasswordResetRequest, PasswordReset
from app.core.security import get_password_hash, verify_password, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES, get_current_active_user
from app.core.database import get_db
from app.models.user import User
from typing import Optional

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=UserResponse)
def register(user_data: UserRegister, db: Session = Depends(get_db)):
    """User registration"""
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        email=user_data.email,
        hashed_password=hashed_password,
        full_name=user_data.full_name
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return new_user

@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """User login"""
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
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/logout")
def logout():
    """User logout"""
    # In a real implementation, you might blacklist the token
    # For now, just return success
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
def me(current_user: User = Depends(get_current_active_user)):
    """Current user info"""
    return current_user

@router.get("/me/with-profile")
def me_with_profile(current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    """Current user info with profile"""
    from app.models.user import Profile
    
    # Get user profile
    profile = db.query(Profile).filter(Profile.id == current_user.id).first()
    
    return {
        "user": current_user,
        "profile": profile
    } 