from pydantic import BaseModel, Field


class UserSchema(BaseModel):
    sub: int = Field(description="The unique identifier of the user.", example=1234)
    name: str = Field(description="The full name of the user.", example="Jane Doe")
    phonenumber: str = Field(description="The phone number of the user")
    loyality_points: int = Field(
        description="The loyality points of the user", example=100
    )
    picture: str = Field(description="The picture of the user")

    class Config:
        from_attributes = True
