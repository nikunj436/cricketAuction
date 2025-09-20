from pydantic import BaseModel

# Pythonic name: PascalCase, no suffix
class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

# Pythonic name: PascalCase, no suffix
class TokenPayload(BaseModel):
    sub: str | None = None