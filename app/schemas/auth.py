from pydantic import BaseModel, Field

from app.schemas.token import TokenSchema
from app.schemas.user import UserSchema


class AuthSchema(BaseModel):
    user: UserSchema = Field(..., description="The user information.")
    token: TokenSchema = Field(..., description="The token information.")

    class Config:
        from_attributes = True
