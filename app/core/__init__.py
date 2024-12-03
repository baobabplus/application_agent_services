from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    service_env: str = Field("LOCAL", alias="ENV")

    class Config:
        env_file = ".env"
        extra = "allow"
        populate_by_name = True


settings = Settings()
