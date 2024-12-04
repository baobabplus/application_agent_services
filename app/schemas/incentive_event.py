from datetime import date
from typing import List

from pydantic import BaseModel, Field, field_validator

from app.schemas.odoo_record import Many2One


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
    event_type_id: Many2One = Field(
        ...,
        description="The type of Bonus.",
        examples=[{"id": 1, "name": "Activation"}],
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
    records: List[IncentiveEventRecord] = Field(
        ..., description="A list of account records."
    )
