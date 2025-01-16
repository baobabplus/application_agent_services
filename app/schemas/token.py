from typing import Literal

from pydantic import BaseModel, Field


class TokenResponse(BaseModel):
    token_type: Literal["Bearer"] = Field(
        "Bearer", description="The type of token.", example="Bearer"
    )
    expires_in: int = Field(
        ..., description="The time in seconds until the token expires.", example=3600
    )
    access_token: str = Field(
        ..., description="The access token.", example="eyJhbGciOiJIUzI1NiIsInR..."
    )
    refresh_token: str = Field(
        ..., description="The refresh token.", example="eyJhbGciOiJIUzI1NiIsInR..."
    )


class LogoutResponse(BaseModel):
    message: str = Field(
        ...,
        description="The message indicating the user has been logged out.",
        example="User logged out successfully.",
    )
