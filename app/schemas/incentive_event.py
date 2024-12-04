from datetime import date
from typing import List, Union

from pydantic import BaseModel, Field, field_validator

from app.schemas.odoo_record import Many2One
from app.schemas.payg_account import PaygAccountRecord


class EventType(BaseModel):
    id: int = Field(
        ..., description="The unique identifier for the Event Type.", example=1
    )
    name: str = Field(
        ..., description="The name of the Event Type.", example="ACTIVATION"
    )
    category: str = Field(
        ...,
        description="The display name of the Event Type.",
        example="Sales",
    )


class IncentiveEventMinimalRecord(BaseModel):
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


class IncentiveEventRecord(BaseModel):
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
    event_type_id: EventType = Field(..., description="The type of Bonus.")
    account_id: Union[PaygAccountRecord | bool] = Field(
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


class IncentiveEventResponse(BaseModel):
    count: int = Field(
        ..., description="The total number of records returned.", example=10
    )
    models: str = Field(
        ...,
        description="The name of the model being queried.",
        example="incentive.event",
    )
    total_value: float = Field(
        ...,
        description="The total value of all records returned.",
        example=1500.75,
    )
    records: List[IncentiveEventRecord] = Field(
        ..., description="A list of account records."
    )
