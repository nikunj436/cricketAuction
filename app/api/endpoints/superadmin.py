from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.api import deps
from app.models import User
from app.enums import Role
from app.dto.user_dto import User as UserSchema, UserLimitUpdate, UserRoleUpdate, UserApprovalUpdate

router = APIRouter()

@router.post("/users/{user_id}/status", response_model=UserSchema)
def update_user_approval_status(
    user_id: int,
    approval_data: UserApprovalUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_superadmin)
):
    """
    Update user approval status. (SUPERADMIN only)
    Send JSON body: {"action": "approve"} or {"action": "reject"}
    """
    if approval_data.action not in ["approve", "reject"]:
        raise HTTPException(status_code=400, detail="Action must be 'approve' or 'reject'")
    
    user_to_update = db.query(User).filter(User.id == user_id).first()
    if not user_to_update:
        raise HTTPException(status_code=404, detail="User not found")
    
    user_to_update.is_approved = True if approval_data.action == "approve" else False
    db.commit()
    db.refresh(user_to_update)
    return user_to_update

@router.get("/users/by-status", response_model=List[UserSchema])
def get_users_by_approval_status(
    status: str,  # "pending", "approved", "rejected"
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_superadmin)
):
    """
    Get users by approval status. (SUPERADMIN only)
    Status: 'pending', 'approved', 'rejected'
    """
    if status == "pending":
        users = db.query(User).filter(User.is_approved.is_(None)).all()
    elif status == "approved":
        users = db.query(User).filter(User.is_approved == True).all()
    elif status == "rejected":
        users = db.query(User).filter(User.is_approved == False).all()
    else:
        raise HTTPException(status_code=400, detail="Status must be 'pending', 'approved', or 'rejected'")
    
    return users


@router.get("/organizers", response_model=List[UserSchema])
def get_all_organizers(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_superadmin)
):
    """
    Get a list of all organizer users. (SUPERADMIN only)
    """
    organizers = db.query(User).filter(User.role == Role.ORGANIZER).all()
    return organizers

@router.post("/users/{user_id}/assign-role", response_model=UserSchema)
def assign_user_role(
    user_id: int,
    role_data: UserRoleUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_superadmin)
):
    """
    Assign role to an approved user. (SUPERADMIN only)
    Send JSON body: {"new_role": "ORGANIZER"} or {"new_role": "USER"}
    """
    user_to_update = db.query(User).filter(User.id == user_id).first()
    if not user_to_update:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Prevent superadmin from changing their own role
    if user_to_update.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot change your own role")
    
    user_to_update.role = role_data.new_role
    db.commit()
    db.refresh(user_to_update)
    return user_to_update

@router.post("/users/{user_id}/assign-credit", response_model=UserSchema)
def assign_user_credit(
    user_id: int,
    credit_data: UserLimitUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_superadmin)
):
    """
    Assign auction credit/limit to a user. (SUPERADMIN only)
    Send JSON body: {"new_limit": 5}
    """
    user_to_update = db.query(User).filter(User.id == user_id).first()
    if not user_to_update:
        raise HTTPException(status_code=404, detail="User not found")
    
    user_to_update.auction_limit = credit_data.new_limit
    db.commit()
    db.refresh(user_to_update)
    return user_to_update
