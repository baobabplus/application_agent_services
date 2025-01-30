from datetime import date
from typing import List

from pydantic import BaseModel, Field

from app.schemas.incentive_event import EventCategorySchema


class DateRangeSchema(BaseModel):
    start: date = Field(..., description="The start date of the range.")
    end: date = Field(..., description="The end date of the range.")


class TasksSchema(BaseModel):
    icon: str = Field(
        ...,
        description="The icon representing the component (e.g., a task or category).",
        example="units-repossess-icon",
    )
    color: str = Field(
        ...,
        description="The color associated with the Event Type.",
        example="#F2BA11",
    )
    label: str = Field(
        ...,
        description="The label or name of the component.",
        example="Units to Repossess",
    )
    count: int = Field(
        ..., description="The count of items related to the component.", example=4
    )
    action: str = Field(
        ...,
        description="An action link or endpoint for the component.",
        example="/api/v1/employee/unit-repossess",
    )


class SummarySimpleSchema(BaseModel):
    date_range: DateRangeSchema = Field(
        ..., description="The date range for the summary (e.g., '4 - 8 Nov')."
    )
    total_earnings: float = Field(
        ..., description="The total earnings for the specified period."
    )
    currency: str = Field(..., description="The currency code for the earnings.")
    categories: List[EventCategorySchema] = Field()
    action: str = Field(
        ..., description="An action link or endpoint related to the summary."
    )


class SummarySchema(SummarySimpleSchema):
    current_report_id: int = Field(..., description="The Current report ID", example=70)
    last_report_id: int = Field(..., description="The last report ID", example=69)
