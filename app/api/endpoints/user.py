from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.dto.user_dto import User as UserSchema
from app.models import User
from app.api import deps


router = APIRouter()


@router.get("/me", response_model=UserSchema, tags=["User"])
def get_current_user(current_user: User = Depends(deps.get_current_user)):

    return current_user