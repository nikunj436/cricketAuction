from pydantic import BaseModel, EmailStr

# Schema for the forgot-password request
class EmailSchema(BaseModel):
    email: EmailStr

# Schema for the reset-password request
class ResetPasswordSchema(BaseModel):
    token: str
    new_password: str

# Schema for the reset-password request
class ResetPasswordSchema(BaseModel):
    token: str
    password: str

class TokenSchema(BaseModel):
    token: str