from pydantic import BaseModel, Field


class CountrySchema(BaseModel):
    name: str = Field(..., description="The name of the country")
    flag_url: str = Field(..., description="Flag icon URL")
    dial_code: str = Field(..., description="Internation Dial Code")

    class Config:
        from_attributes = True
