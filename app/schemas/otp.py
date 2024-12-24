from typing import Optional

from pydantic import BaseModel, Field, field_validator

from app.utils.main import validate_and_extract_country


class OTPRequest(BaseModel):
    phone_number: str = Field(..., title="Phone Number")

    @field_validator("phone_number")
    def validate_phone_number(cls, value):
        phone_data = validate_and_extract_country(value)
        return phone_data


class OTPResponse(BaseModel):
    otp: Optional[str] = Field(
        None, description="The Time based One Time Password (TOTP) sent to the user."
    )
    message: str = Field(
        ..., description="A message describing the outcome of the operation."
    )
