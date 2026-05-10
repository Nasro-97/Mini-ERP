from uuid import UUID
from pydantic import BaseModel, ConfigDict
from datetime import datetime

from app.models import RequestStatus, RequestPriority
from app.schemas.item import ItemOutput

#Frontend --> backend Creating
class RequestCreate(BaseModel):
    request_number: str
    title: str
    description: str | None = None
    client_reference: str

    client_id: UUID
    assigned_to_user_id: UUID | None = None
    sales_manager_id: UUID | None = None

    priority: RequestPriority = RequestPriority.LOW

    request_date: datetime
    required_date: datetime | None = None
    deadline: datetime

    sales_manager_notes: str | None = None
    sales_manager_decision_at: datetime | None = None

    notes: str | None = None


# Frontend --> backend updating request
class RequestUpdate(BaseModel):

    title: str | None = None
    description: str | None = None
    client_reference: str | None = None

    client_id: UUID | None = None
    assigned_to_user_id: UUID | None = None
    sales_manager_id: UUID | None = None

    priority: RequestPriority | None = None

    request_date: datetime | None = None
    required_date: datetime | None = None
    deadline: datetime | None = None

    sales_manager_notes: str | None = None

    notes: str | None = None


# Backend --> frontend
class RequestOutput(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    request_number: str
    title: str
    description: str | None = None
    client_reference: str | None = None

    client_id: UUID
    created_by_user_id: UUID
    assigned_to_user_id: UUID | None = None
    sales_manager_id: UUID | None = None

    status: RequestStatus
    priority: RequestPriority

    request_date: datetime
    required_date: datetime | None = None
    deadline: datetime

    sales_manager_notes: str | None = None
    sales_manager_decision_at: datetime | None = None

    notes: str | None = None


# Backend --> frontend request with items attached
class RequestWithItems(RequestOutput):

    items: list[ItemOutput] = []
