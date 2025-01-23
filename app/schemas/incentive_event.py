from datetime import date
from typing import List, Union

from pydantic import BaseModel, Field, field_validator

from app.schemas.incentive_report import IncentiveReportSimpleSchema
from app.schemas.odoo_record import Many2One
from app.schemas.payg_account import PaygAccountSchema


class EventTypeSchema(BaseModel):
    name: str = Field(
        ..., description="The name of the Event Type.", example="ACTIVATION"
    )
    type: str = Field(
        ...,
        description="The category of the Event Type.",
        example="Sales",
    )


class EventCategorySchema(BaseModel):
    name: str = Field(
        ..., description="The name of the Event Type.", example="ACTIVATION"
    )
    color: str = Field(
        ...,
        description="The color associated with the Event Type.",
        example="#FF0000",
    )
    value: float = Field(
        ...,
        description="The numeric value associated with the Event Type.",
        example=150.75,
    )


class IncentiveEventMinimalSchema(BaseModel):
    category: str = Field(
        ...,
        description="The display name of the Event Type.",
        example="Sales",
    )
    sum_value: float = Field(
        ...,
        description="The numeric value associated with the Incentive Event, such as a monetary amount or points.",
        example=150.75,
    )


class IncentiveEventSchema(BaseModel):
    id: int = Field(
        ..., description="The unique identifier for the Account.", example=1
    )
    event_date: date = Field(
        ...,
        description="The date and time of the actual Incentive Event.",
        example="2023-12-25T14:00:00",
    )
    value: float = Field(
        ...,
        description="The numeric value associated with the Incentive Event, such as a monetary amount or points.",
        example=150.75,
    )
    currency_id: Many2One
    event_type_id: EventTypeSchema = Field(..., description="The type of Bonus.")
    account_id: Union[PaygAccountSchema | bool] = Field(
        ...,
        description="A reference to the account associated with the Incentive Event.",
    )

    @field_validator("event_date", mode="before")
    def parse_event_date(cls, value):
        """Validator to ensure the date is correctly parsed."""
        if isinstance(value, str):
            try:
                return date.fromisoformat(value)
            except ValueError:
                raise ValueError(
                    f"Invalid date format: {value}. Expected format: YYYY-MM-DD"
                )
        if isinstance(value, date):
            return value
        raise ValueError(f"Unsupported type for event_date: {type(value)}")


class IncentiveEventSummarySchema(BaseModel):
    event_categories: List[EventCategorySchema] = Field(
        ..., description="A list of Incentive Category."
    )
    total_value: float = Field(
        ...,
        description="The total value of all Incentive Events.",
        example=150.75,
    )


class IncentiveEventCustomSchema(BaseModel):
    report_ids: List[IncentiveReportSimpleSchema] = Field(
        ..., description="A list of Incentive Report records."
    )
