from typing import Union

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    odoo_url: str = Field(..., alias="ODOO_URL")
    odoo_db: str = Field(..., alias="ODOO_DB")
    odoo_username: str = Field(..., alias="ODOO_USERNAME")
    odoo_password: str = Field(..., alias="ODOO_PASSWORD")
    odoo_uuid: Union[int, bool] = Field(..., alias="ODOO_UUID")
    odoo_account_segmentation_slow_payer: str = Field(
        ..., alias="ODOO_SLOW_PAYER_SEGMENTATION_LIST"
    )
    odoo_account_segmentation_hypercare: str = Field(
        ..., alias="ODOO_HYPERCARE_SEGMENTATION_LIST"
    )
    access_token_secret: str = Field(..., alias="ACCESS_TOKEN_SECRET")
    refresh_token_secret: str = Field(..., alias="REFRESH_TOKEN_SECRET")
    access_token_expire: int = Field(..., alias="ACCESS_TOKEN_EXPIRE")
    refresh_token_expire: int = Field(..., alias="REFRESH_TOKEN_EXPIRE")

    class Config:
        env_file = ".env"
        extra = "allow"
        populate_by_name = True


settings = Settings()
