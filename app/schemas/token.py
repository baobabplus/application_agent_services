from typing import Literal

from pydantic import BaseModel, Field


class TokenResponse(BaseModel):
    access_token: str = Field(
        ..., description="The access token.", example="eyJhbGciOiJIUzI1NiIsInR..."
    )
    refresh_token: str = Field(
        ..., description="The refresh token.", example="eyJhbGciOiJIUzI1NiIsInR..."
    )
    token_type: Literal["Bearer"] = Field(
        "Bearer", description="The type of token.", example="Bearer"
    )


class LogoutResponse(BaseModel):
    message: str = Field(
        ...,
        description="The message indicating the user has been logged out.",
        example="User logged out successfully.",
    )
