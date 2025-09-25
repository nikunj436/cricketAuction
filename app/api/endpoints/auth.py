from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.dto import UserCreate, User, Token, RefreshTokenRequest
from app.models import User as UserModel, Token as TokenModel
from app.core import security, settings
from app.db import SessionLocal
from app.enums import Role

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# def 

@router.post("/signup", response_model=User, status_code=status.HTTP_201_CREATED)
def create_user(
    *,
    db: Session = Depends(get_db),
    user_in: UserCreate
):
    """
    Create a new user.
    """
    user = db.query(UserModel).filter(UserModel.email == user_in.email).first()
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this email already exists.",
        )
    
    if user_in.mobile:
        user = db.query(UserModel).filter(UserModel.mobile == user_in.mobile).first()
        if user:
            raise HTTPException(
                status_code=400,
                detail="The user with this mobile number already exists.",
            )

    hashed_password = security.get_password_hash(user_in.password)
    
    db_user = UserModel(
        first_name=user_in.first_name,
        last_name=user_in.last_name,
        email=user_in.email,
        mobile=user_in.mobile,
        hashed_password=hashed_password,
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user

@router.post("/login", response_model=Token)
def login_for_access_token(
    db: Session = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
):
    """
    Handles user login, returns access/refresh tokens, and saves the refresh token.
    """
    user = db.query(UserModel).filter(UserModel.email == form_data.username).first()

    if not user or not security.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if user is approved (only for ORGANIZER role)
    
    if user.is_approved is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account is pending approval. Please wait for administrator approval.",
        )
    elif user.is_approved is False:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account has been rejected. Please contact administrator.",
        )

    # Generate tokens
    access_token = security.create_access_token(data={"sub": user.email})
    refresh_token = security.create_refresh_token(data={"sub": user.email})

    # --- Start of new logic ---

    # Calculate refresh token expiry date
    expires_at = datetime.now() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    # Create a token record in the database
    db_token = TokenModel(
        user_id=user.id,
        refresh_token=refresh_token,
        expires_at=expires_at
    )
    db.add(db_token)
    db.commit()
    db.refresh(db_token)

    # --- End of new logic ---

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }

@router.post("/refresh", response_model=Token)
def refresh_access_token(
    refresh_request: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    """
    Refresh access token using a valid refresh token.
    """
    # Find refresh token in database
    db_token = db.query(TokenModel).filter(
        TokenModel.refresh_token == refresh_request.refresh_token
    ).first()
    
    if not db_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    # Check if refresh token is expired
    if db_token.expires_at < datetime.now():
        # Remove expired token from database
        db.delete(db_token)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has expired"
        )
    
    # Get user from token
    user = db_token.user
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    # Generate new access token
    new_access_token = security.create_access_token(data={"sub": user.email})
    
    # Generate new refresh token (rotate refresh tokens)
    new_refresh_token = security.create_refresh_token(data={"sub": user.email})
    
    # Keep original expiration - only reset if user was inactive for 7+ days
    # This ensures users must login again after 7 days of inactivity
    new_expires_at = datetime.now() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    # Update refresh token in database
    db_token.refresh_token = new_refresh_token
    db_token.expires_at = new_expires_at
    db.commit()
    db.refresh(db_token)
    
    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer"
    }