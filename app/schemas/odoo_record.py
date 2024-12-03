from pydantic import BaseModel, Field, model_validator


class Many2One(BaseModel):
    id: int = Field(..., description="The ID of the related record.")
    display_name: str = Field(..., description="The name of the related record.")

    @model_validator(mode="before")
    @classmethod
    def validate_many2one(cls, values):
        if not isinstance(values, list) or len(values) != 2:
            raise ValueError(
                "Many2one must be a list with exactly two elements [int, str]."
            )
        if not isinstance(values[0], int) or not isinstance(values[1], str):
            raise ValueError("Many2one must contain an integer ID and a string name.")
        return {"id": values[0], "display_name": values[1]}
