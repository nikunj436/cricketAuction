from pydantic import BaseModel

# Pythonic name: PascalCase, no suffix
class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str

class TokenPayload(BaseModel):
    sub: str = None

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class TokenSchema(BaseModel):
    token: str