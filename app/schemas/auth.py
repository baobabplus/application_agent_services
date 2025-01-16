from pydantic import BaseModel, Field

from app.schemas.token import TokenResponse
from app.schemas.user import UserSchema


class AuthResponse(BaseModel):
    user: UserSchema = Field(..., description="The user information.")
    token: TokenResponse = Field(..., description="The token information.")

    class Config:
        from_attributes = True
