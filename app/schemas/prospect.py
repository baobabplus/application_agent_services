from datetime import datetime
from typing import List, Union

from pydantic import BaseModel, Field


class ProspectRecord(BaseModel):
    id: int = Field(
        ..., description="The unique identifier for the Prospect.", example=1
    )
    prospect_ext_id: str = Field(
        ..., description="The external ID of the Prospect.", example="PROS12345"
    )
    create_date: datetime = Field(
        ...,
        description="The date and time when the prospect was created.",
        example="2023-12-20T09:26:07",
    )
    state: Union[str, bool] = Field(
        ...,
        description=(
            "The state of the prospect. Can be a string indicating the status "
            "or a boolean representing a simplified state."
        ),
        example="active",  # Or `true` depending on context
    )


class ProspectResponse(BaseModel):
    count: int = Field(
        ..., description="The total number of prospect records returned.", example=100
    )
    models: str = Field(
        ..., description="The name of the model being queried.", example="prospect"
    )
    records: List[ProspectRecord] = Field(
        ..., description="A list of prospect records."
    )
