from datetime import date
from enum import Enum

from pydantic import BaseModel, Field, field_validator

from app.schemas.odoo_record import Many2One


class ReportStatusSchema(str, Enum):
    IN_PROGRESS = "in_progress"
    TO_VALIDATE = "to_validate"
    DONE = "done"


class ReportPeriodSchema(str, Enum):
    CURRENT = "current"
    PREVIOUS = "previous"


class IncentiveReportSimpleSchema(BaseModel):
    id: int = Field(
        ..., description="The unique identifier for the Incentive Report.", example=1
    )
    start_date: date = Field(
        ..., description="The start date of the incentive report.", example="2024-01-01"
    )
    end_date: date = Field(
        ..., description="The end date of the incentive report.", example="2024-12-31"
    )
    action: str = Field(
        ...,
        description="The route to view the incentive report.",
        example="/incentive-report/1",
    )


class IncentiveReportSchema(BaseModel):
    id: int = Field(
        ..., description="The unique identifier for the Incentive Report.", example=1
    )
    name: str = Field(
        ..., description="The name of the Incentive Report.", example="ACTIVATION"
    )
    start_date: date = Field(
        ..., description="The start date of the incentive report.", example="2024-01-01"
    )
    end_date: date = Field(
        ..., description="The end date of the incentive report.", example="2024-12-31"
    )
    generic_job_id: Many2One = Field(
        ..., description="The job associated with this incentive report."
    )
    status: ReportStatusSchema = Field(
        ..., description="Status of the incentive report.", example="done"
    )

    @field_validator("end_date")
    def validate_dates(cls, v, values):
        if "start_date" in values and v < values["start_date"]:
            raise ValueError("End date cannot be earlier than start date")
        return v
