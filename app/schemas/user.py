from pydantic import BaseModel, EmailStr
from typing import Optional
from app.enums.role import Role

# Properties to receive via API on user creation
# Pythonic name: PascalCase, no suffix
class UserCreate(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    password: str
    mobile: Optional[str] = None

# Properties to return to client
# Pythonic name: PascalCase, no suffix
class User(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: EmailStr
    mobile: Optional[str] = None
    role: Role

    class Config:
        from_attributes = True