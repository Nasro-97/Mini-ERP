from uuid import UUID
from pydantic import BaseModel, ConfigDict
from datetime import datetime

from app.models import RFQ, RFQStatus

#Frontend --> backend Creating
class RFQCreate(BaseModel):

    request_id: UUID
    supplier_id: UUID
    contact_id: UUID | None = None

    notes: str | None = None
    response_deadline: datetime


# Frontend --> backend updating
class RFQUpdate(BaseModel):

    notes: str | None = None
    response_deadline: datetime | None = None


# Backend -> Frontend
class RFQOutput(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    request_id: UUID
    supplier_id: UUID
    contact_id: UUID | None = None
    procurement_manager_id: UUID
    rfq_number: str
    status: RFQStatus
    notes: str | None = None
    response_deadline: datetime
    sent_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


