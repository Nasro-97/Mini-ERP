from uuid import UUID
from pydantic import BaseModel, ConfigDict
from decimal import Decimal
from datetime import datetime

from app.models.quotation import QuotationStatus


class QuotationCreate(BaseModel):
    rfq_id: UUID
    client_reference: str
    currency: str
    subtotal: Decimal
    shipping_cost: Decimal | None = None
    taxes: Decimal | None = None
    other_costs: Decimal | None = None
    total_amount: Decimal
    payment_terms: str | None = None
    delivery_terms: str | None = None
    lead_time: str | None = None
    validity_date: datetime
    notes: str | None = None


class QuotationUpdate(BaseModel):
    currency: str | None = None
    subtotal: Decimal | None = None
    shipping_cost: Decimal | None = None
    taxes: Decimal | None = None
    other_costs: Decimal | None = None
    total_amount: Decimal | None = None
    payment_terms: str | None = None
    delivery_terms: str | None = None
    lead_time: str | None = None
    validity_date: datetime | None = None
    notes: str | None = None


class QuotationOutput(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    rfq_id: UUID
    supplier_id: UUID
    quotation_number: str
    client_reference: str
    status: QuotationStatus
    currency: str
    subtotal: Decimal
    shipping_cost: Decimal | None = None
    taxes: Decimal | None = None
    other_costs: Decimal | None = None
    total_amount: Decimal
    payment_terms: str | None = None
    delivery_terms: str | None = None
    lead_time: str | None = None
    validity_date: datetime
    notes: str | None = None
    submitted_for_review_at: datetime | None = None
    rejection_notes: str | None = None
    created_at: datetime
    updated_at: datetime