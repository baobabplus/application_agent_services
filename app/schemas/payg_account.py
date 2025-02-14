from datetime import datetime
from typing import List

from pydantic import BaseModel, Field

from app.schemas.odoo_record import Many2One


class PaygAccountSchema(BaseModel):
    id: int = Field(
        ..., description="The unique identifier for the Account.", example=1
    )
    account_ext_id: str = Field(
        ..., description="The external ID of the Account.", example="ACC12345"
    )
    create_date: datetime = Field(
        ...,
        description="The date and time when the Account was created.",
        example="2023-12-20T09:26:07",
    )
    registration_date: datetime = Field(
        ...,
        description="The Registration date of the Account.",
        example="2023-12-20T09:26:07",
    )
    client_id: Many2One = Field(
        ..., description="A reference to the client associated with the account."
    )
    nb_days_overdue: int = Field(
        ..., description="The number of days the account is overdue.", example=8
    )
    account_status: str = Field(
        ..., description="The status of the account.", example="ENABLED"
    )


class PaygAccountRecordsetSchema(BaseModel):
    count: int = Field(
        ..., description="The total number of records returned.", example=10
    )
    models: str = Field(
        ..., description="The name of the model being queried.", example="payg.account"
    )
    records: List[PaygAccountSchema] = Field(
        ..., description="A list of account records."
    )
