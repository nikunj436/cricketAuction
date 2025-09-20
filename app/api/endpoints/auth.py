from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

# Updated import to be Pythonic
from app.schemas.user import UserCreate, User 
from app.models.user import User as UserModel
from app.core import security
from app.db.session import SessionLocal

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Updated response_model and input parameter type hint
@router.post("/signup", response_model=User, status_code=status.HTTP_201_CREATED)
def create_user(
    *,
    db: Session = Depends(get_db),
    user_in: UserCreate # <-- Updated here
):
    """
    Create a new user.
    """
    # The rest of your function logic remains the same...
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