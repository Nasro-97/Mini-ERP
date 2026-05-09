from uuid import UUID
from pydantic import BaseModel, ConfigDict
from decimal import Decimal
from datetime import datetime

from app.models import ItemUnit

# Frontend --> backend when creating item
class ItemCreate(BaseModel):

    request_id: UUID

    line_number: int
    description: str
    quantity: Decimal
    unit: ItemUnit = ItemUnit.PCS

    notes: str | None = None


# Frontend --> backend when updating item
class ItemUpdate(BaseModel):

    line_number: int | None = None
    description: str | None = None
    quantity: Decimal | None = None
    unit: ItemUnit | None = None
    notes: str | None = None

# Backend --> frontend
class ItemOutput(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    request_id: UUID
    line_number: int
    internal_code: str | None = None
    description: str
    quantity: Decimal
    unit: ItemUnit
    notes: str | None = None
    created_at: datetime
    updated_at: datetime
