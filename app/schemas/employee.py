from pydantic import BaseModel, Field

from app.schemas.odoo_record import Many2One


class EmployeeSchema(BaseModel):
    id: int = Field(description="The unique identifier of the employee.", example=4)
    name: str = Field(description="The full name of the employee.", example="Jane Doe")
    mobile_phone: str = Field(
        ...,
        description="The mobile phone number of the employee.",
        example="+1234567890",
    )
    can_use_application_agent: bool = Field(
        ...,
        description="Indicates whether the employee can use the application agent.",
        example=True,
    )
    generic_job_id: Many2One = Field(..., description="Generic job")
    company_id: Many2One

    class Config:
        from_attributes = True
