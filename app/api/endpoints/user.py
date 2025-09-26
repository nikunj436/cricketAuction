from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.dto.user_dto import User as UserSchema, updateUser
from app.models import User
from app.api import deps


router = APIRouter()


@router.get("/me", response_model=UserSchema, tags=["User"])
def get_current_user(current_user: User = Depends(deps.get_current_user)):

    return current_user


@router.post("/update", response_model=UserSchema, tags=["User"])
def update_current_user(
    request: updateUser,
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db)
 ):

    if request.first_name:
        current_user.first_name = request.first_name

    if request.last_name:
        current_user.last_name = request.last_name

    db.commit()
    db.refresh(current_user)

    return current_user

