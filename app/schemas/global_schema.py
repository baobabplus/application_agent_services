from typing import List, Optional

from pydantic import BaseModel, Field


class PaginationSchema(BaseModel):
    offset: int = Field(0, description="The number of records to skip.", example=0)
    limit: int = Field(10, description="The number of records to fetch.", example=10)
    current_records: int = Field(
        0, description="The current number of records.", example=100
    )
    total_records: int = Field(
        0, description="The total number of records.", example=100
    )


class FilterSchema(BaseModel):
    value: str = Field(
        ..., description="The value to filter the data.", example="event_category"
    )
    param: str = Field(
        ..., description="The parameter to filter the data.", example="sales"
    )
    label: str = Field(
        ..., description="The label to display in the filter.", example="Sales"
    )

    def __eq__(self, other):
        return self.value == other.value and self.param == other.param


class CollapsedCardSchema(BaseModel):
    icon: str = Field(
        ...,
        description="The icon representing the component (e.g., a task or category).",
        example="units-repossess-icon",
    )
    icon_color: str = Field(
        ..., description="The color associated with the icon.", example="#FF0000"
    )
    title: str = Field(
        ..., description="The title of the component.", example="Jane Doe"
    )
    value: float = Field(..., description="The value of the component.", example=1000)
    currency: str = Field(
        ..., description="The currency code for the earnings.", example="MGA"
    )
    value_color: str = Field(
        ..., description="The color associated with the value.", example="#FF0000"
    )
    subtitle: str = Field(
        ..., description="The subtitle of the component.", example="Sales"
    )


class RowSchema(BaseModel):
    label: str = Field(
        ..., description="The label for the row.", example="Incentive Type"
    )
    value: Optional[str] = Field(
        ..., description="The value for the row.", example="New Customer bonus"
    )


class ExpandedSchema(BaseModel):
    rows: List[RowSchema] = Field(
        ..., description="The list of rows for the expanded card."
    )


class CardSchema(BaseModel):
    id: str = Field(
        ...,
        description="Identifier for the card.",
        example="uuid_1",
    )
    collapsed: CollapsedCardSchema = Field(
        ..., description="The collapsed view of the card."
    )
    expanded: ExpandedSchema = Field(..., description="The expanded view of the card.")


class TaskCollapsedCardSchema(BaseModel):
    icon: str = Field(
        ...,
        description="The icon representing the Card (e.g., a task or category).",
        example="units-repossess-icon",
    )
    icon_color: str = Field(
        ..., description="The color associated with the icon.", example="#FF0000"
    )
    title: str = Field(
        ...,
        description="The title of the Card.",
        example="Jane Doe",
    )
    rows: Optional[List[RowSchema]] = Field(
        ..., description="The list of rows for the collapsed card."
    )
    alert_text: Optional[str] = Field(
        ...,
        description="The alert text for the collapsed card.",
        example="8 days late in payment",
    )
    alert_text_color: Optional[str] = Field(
        ..., description="The color associated with the alert text.", example="#FF0000"
    )


class TaskExpandedCardSchema(BaseModel):
    rows: List[RowSchema] = Field(
        ..., description="The list of rows for the expanded card."
    )


class TaskCardSchema(BaseModel):
    collapsed: TaskCollapsedCardSchema = Field(
        ..., description="The collapsed view of the card."
    )
    expanded: TaskExpandedCardSchema = Field(
        ..., description="The expanded view of the card."
    )


class TaskSchema(BaseModel):
    icon: str = Field(
        ...,
        description="The icon representing the component (e.g., a task or category).",
        example="units-repossess-icon",
    )
    total_value: float = Field(
        ..., description="The number of the slow payer.", example=30
    )
    title: str = Field(..., description="The title of the block.", example="Slow Payer")
    pagination: PaginationSchema = Field(
        ..., description="The pagination details for the slow payer."
    )
    filters: List[FilterSchema] = Field(
        ..., description="The list of filters for the slow payer."
    )
    cards: List[TaskCardSchema] = Field(
        ..., description="The list of cards for the slow payer."
    )
