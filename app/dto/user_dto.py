from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional
import re
from app.enums import Role

# This new schema is for the admin endpoint to set an auction limit
class UserLimitUpdate(BaseModel):
    new_limit: int

# This schema is for the superadmin endpoint to update user roles
class UserRoleUpdate(BaseModel):
    new_role: Role

# This schema is for the superadmin endpoint to update user approval status
class UserApprovalUpdate(BaseModel):
    action: str  # "approve" or "reject"

# This schema for creating a user with mobile validation
class UserCreate(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    password: str
    mobile: str

    @field_validator('mobile')
    def validate_mobile(cls, v):
        
        # Remove any spaces or special characters
        mobile_clean = re.sub(r'[^\d]', '', v)
        
        # Check if exactly 10 digits
        if len(mobile_clean) != 10:
            raise ValueError('Mobile number must be exactly 10 digits')
        
        # Check if starts with 6, 7, 8, or 9
        if not mobile_clean[0] in ['6', '7', '8', '9']:
            raise ValueError('Mobile number must start with 6, 7, 8, or 9')
        
        return mobile_clean

# This is the main response schema, updated with the new fields
class User(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: EmailStr
    mobile: str
    role: Role
    is_approved: Optional[bool]           
    auction_limit: int          
    auctions_created: int       

    class Config:
        from_attributes = True