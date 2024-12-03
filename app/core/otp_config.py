from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    otp_secret: str = Field(..., alias="OTP_SECRET")
    otp_interval: int = Field(..., alias="OTP_INTERVAL")
    otp_valid_window: int = Field(..., alias="OTP_VALID_WINDOW")

    class Config:
        env_file = ".env"
        extra = "allow"
        populate_by_name = True


settings = Settings()
