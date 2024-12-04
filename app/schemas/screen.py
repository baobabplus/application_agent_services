from datetime import date
from typing import List, Union

from pydantic import BaseModel, Field

from app.schemas.incentive_event import IncentiveEventMinimalRecord
from app.schemas.odoo_record import Many2One


class DateRange(BaseModel):
    start: date = Field(..., description="The start date of the range.")
    end: date = Field(..., description="The end date of the range.")


class Summary(BaseModel):
    date_range: DateRange = Field(
        ..., description="The date range for the summary (e.g., '4 - 8 Nov')."
    )
    total_earnings: int = Field(
        ..., description="The total earnings for the specified period."
    )
    currency: Union[Many2One | None] = Field(
        ..., description="The currency used for the earnings (e.g., 'Ar')."
    )
    event_count: int = Field(..., description="The count of incentive events.")
    details: List[IncentiveEventMinimalRecord] = Field(
        ..., description="Detailed data for incentive events."
    )
    action: str = Field(
        ..., description="An action link or endpoint related to the summary."
    )


class Component(BaseModel):
    icon: str = Field(
        ...,
        description="The icon representing the component (e.g., a task or category).",
    )
    label: str = Field(..., description="The label or name of the component.")
    count: int = Field(..., description="The count of items related to the component.")
    action: str = Field(
        ..., description="An action link or endpoint for the component."
    )


class DashboardResponse(BaseModel):
    summary: Summary = Field(
        ...,
        description="The summary section of the dashboard, including totals and actions.",
    )
    components: List[Component] = Field(..., description="A list of components.")
