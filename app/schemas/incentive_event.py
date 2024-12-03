from datetime import datetime
from typing import List

from pydantic import BaseModel, Field


class IncentiveEventRecord(BaseModel):
    id: int = Field(
        ..., description="The unique identifier for the Account.", example=1
    )
    event_date: datetime = Field(
        ...,
        description="The date and time of the actual Incentive Event.",
        example="2023-12-25T14:00:00",
    )
    value: float = Field(
        ...,
        description="The numeric value associated with the Incentive Event, such as a monetary amount or points.",
        example=150.75,
    )


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
