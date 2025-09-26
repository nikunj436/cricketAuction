from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.dto import UserCreate, User, Token, RefreshTokenRequest
from app.dto.auth_dto import EmailSchema, ResetPasswordSchema, TokenSchema  
from app.models import User as UserModel, Token as TokenModel
from app.core import security, settings
from app.db import SessionLocal
from app.enums import Role
from app.utils.email_helper import send_verification_email, send_password_reset_email

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/signup", response_model=User, status_code=status.HTTP_201_CREATED)
async def create_user(
    *,
    db: Session = Depends(get_db),
    user_in: UserCreate,
    background_tasks: BackgroundTasks
):
    """
    Create a new user and send a verification email in the background.
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
    
    # Generate a token and send the verification email
    token = security.create_access_token(data={"sub": db_user.email, "scope": "email_verification"})
    background_tasks.add_task(send_verification_email, email=db_user.email, token=token)
    
    return db_user


@router.post("/verify-email")
def verify_email(request: TokenSchema, db: Session = Depends(get_db)):
    """
    Verify a user's email address from a token sent in the request body.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Could not validate credentials",
    )
    try:
        # Read the token from the request body via the TokenSchema
        payload = security.jwt.decode(request.token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        if payload.get("scope") != "email_verification":
            raise credentials_exception
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except security.jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Verification link has expired. Please request a new one.")
    except security.jwt.JWTError:
        raise credentials_exception

    user = db.query(UserModel).filter(UserModel.email == email).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    if user.is_verified:
        return {"message": "Email is already verified."}
    
    user.is_verified = True
    db.commit()
    
    return {"message": "Email verified successfully! You can now log in."}


@router.post("/resend-verification")
async def resend_verification_email(
    request: EmailSchema,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Resend the verification email to a user who has not yet verified their account.
    """
    user = db.query(UserModel).filter(UserModel.email == request.email).first()
    if user and not user.is_verified:
        token = security.create_access_token(data={"sub": user.email, "scope": "email_verification"})
        background_tasks.add_task(send_verification_email, email=user.email, token=token)

    return {"message": "If an unverified account with this email exists, a new verification link has been sent."}


@router.post("/login", response_model=Token)
def login_for_access_token(
    db: Session = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
):
    """
    Handles user login, returns access/refresh tokens, and requires email verification.
    """
    user = db.query(UserModel).filter(UserModel.email == form_data.username).first()

    if not user or not security.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not verified. Please check your inbox or request a new verification link.",
        )
    
    if user.is_approved is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account is pending approval. Please wait for administrator approval.",
        )
    elif user.is_approved is False:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account has been rejected. Please contact the administrator.",
        )

    access_token = security.create_access_token(data={"sub": user.email})
    refresh_token = security.create_refresh_token(data={"sub": user.email})
    expires_at = datetime.now() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    db_token = TokenModel(
        user_id=user.id,
        refresh_token=refresh_token,
        expires_at=expires_at
    )
    db.add(db_token)
    db.commit()
    db.refresh(db_token)

    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}


@router.post("/forgot-password")
async def forgot_password(
    request: EmailSchema,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Sends a password reset link to the user's email if the user exists.
    """
    user = db.query(UserModel).filter(UserModel.email == request.email).first()
    if user:
        reset_token = security.create_access_token(data={"sub": user.email, "scope": "password_reset"})
        background_tasks.add_task(send_password_reset_email, email=user.email, token=reset_token)
    
    return {"message": "If an account with this email exists, a password reset link has been sent."}


@router.post("/reset-password")
def reset_password(request: ResetPasswordSchema, db: Session = Depends(get_db)):
    """
    Resets the user's password using the token from the reset link.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid token",
    )
    try:
        payload = security.jwt.decode(request.token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        if payload.get("scope") != "password_reset":
            raise credentials_exception
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except security.jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Password reset link has expired.")
    except security.jwt.JWTError:
        raise credentials_exception

    user = db.query(UserModel).filter(UserModel.email == email).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        
    user.hashed_password = security.get_password_hash(request.password)
    db.commit()

    return {"message": "Password has been reset successfully."}


@router.post("/refresh", response_model=Token)
def refresh_access_token(
    refresh_request: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    """
    Refresh access token using a valid refresh token.
    """
    db_token = db.query(TokenModel).filter(
        TokenModel.refresh_token == refresh_request.refresh_token
    ).first()
    
    if not db_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    if db_token.expires_at < datetime.now():
        db.delete(db_token)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has expired"
        )
    
    user = db_token.user
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    new_access_token = security.create_access_token(data={"sub": user.email})
    new_refresh_token = security.create_refresh_token(data={"sub": user.email})
    new_expires_at = datetime.now() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    db_token.refresh_token = new_refresh_token
    db_token.expires_at = new_expires_at
    db.commit()
    db.refresh(db_token)
    
    return {"access_token": new_access_token, "refresh_token": new_refresh_token, "token_type": "bearer"}
