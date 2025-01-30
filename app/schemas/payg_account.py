from datetime import datetime
from typing import List

from pydantic import BaseModel, Field

from app.schemas.global_schema import FilterSchema, PaginationSchema, RowSchema
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
    client_id: Many2One = Field(
        ..., description="A reference to the client associated with the account."
    )
    nb_days_overdue: int = Field(
        ..., description="The number of days the account is overdue.", example=8
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


class SlowPayerCollapsedCardSchema(BaseModel):
    icon: str = Field(
        ...,
        description="The icon representing the component (e.g., a task or category).",
        example="units-repossess-icon",
    )
    icon_color: str = Field(
        ..., description="The color associated with the icon.", example="#FF0000"
    )
    rows: List[RowSchema] = Field(
        ..., description="The list of rows for the collapsed card."
    )
    alert_text: str = Field(
        ...,
        description="The alert text for the collapsed card.",
        example="8 days late in payment",
    )
    alert_text_color: str = Field(
        ..., description="The color associated with the alert text.", example="#FF0000"
    )


class SlowPayerExpandedCardSchema(BaseModel):
    rows: List[RowSchema] = Field(
        ..., description="The list of rows for the expanded card."
    )


class SlowPayerCardSchema(BaseModel):
    collapsed: SlowPayerCollapsedCardSchema = Field(
        ..., description="The collapsed view of the card."
    )
    expanded: SlowPayerExpandedCardSchema = Field(
        ..., description="The expanded view of the card."
    )


class SlowPayerSchema(BaseModel):
    icon: str = Field(
        ...,
        description="The icon representing the component (e.g., a task or category).",
        example="units-repossess-icon",
    )
    total_value: float = Field(
        ..., description="The number of the slow payer.", example=30
    )
    title: str = Field(..., description="The title of the block.", example="Slow Payer")
    pagination: PaginationSchema = Field(
        ..., description="The pagination details for the slow payer."
    )
    filters: List[FilterSchema] = Field(
        ..., description="The list of filters for the slow payer."
    )
    cards: List[SlowPayerCardSchema] = Field(
        ..., description="The list of cards for the slow payer."
    )
