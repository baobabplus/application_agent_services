from pydantic import BaseModel, Field


class EmployeeSchema(BaseModel):
    id: int = Field(description="The unique identifier of the employee.", example=4)
    name: str = Field(description="The full name of the employee.", example="Jane Doe")
    mobile_phone: str = Field(
        ...,
        description="The mobile phone number of the employee.",
        example="+1234567890",
    )

    class Config:
        from_attributes = True
