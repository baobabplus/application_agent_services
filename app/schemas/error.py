from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    error: str = Field(..., description="The error code.")
    error_description: str = Field(..., description="A brief description of the error.")
