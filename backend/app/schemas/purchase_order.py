from uuid import UUID
from pydantic import BaseModel, ConfigDict
from decimal import Decimal
from datetime import datetime

from app.models import POStatus


class PurchaseOrderCreate(BaseModel):
    offer_version_id: UUID


class PurchaseOrderUpdate(BaseModel):
    payment_terms: str | None = None
    delivery_notes: str | None = None
    lead_time: str | None = None

    notes: str | None = None

    currency: str | None = None
    subtotal: Decimal | None = None
    shipping_cost: Decimal | None = None
    taxes: Decimal | None = None
    other_costs: Decimal | None = None
    total_amount: Decimal | None = None


class PurchaseOrderOutput(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    offer_version_id: UUID
    request_id: UUID
    quotation_id: UUID
    supplier_id: UUID
    created_by_user_id: UUID

    po_number: str
    status: POStatus = POStatus.DRAFT

    payment_terms: str | None = None
    delivery_terms: str | None = None
    lead_time: str | None = None

    notes: str | None = None

    currency: str | None = None
    subtotal: Decimal | None = None
    shipping_cost: Decimal | None = None
    taxes: Decimal | None = None
    other_costs: Decimal | None = None
    total_amount: Decimal | None = None

    sent_at: datetime | None = None

    created_at: datetime
    updated_at: datetime