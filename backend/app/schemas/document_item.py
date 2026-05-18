from uuid import UUID
from pydantic import BaseModel, ConfigDict
from decimal import Decimal
from datetime import datetime
from typing import Any
from app.models.document_item import DocumentType


class DocumentItemCreate(BaseModel):
    item_id: UUID
    document_type: DocumentType
    document_id: UUID
    line_number: int
    description: str
    quantity: int | None = None
    price: Decimal | None = None

    warranty: str | None = None
    unit_price: Decimal | None = None
    total_price: Decimal | None = None
    currency: str | None = None

    hs_code: str | None = None
    package_count: int | None = None
    gross_weight_kg: Decimal | None = None
    net_weight_kg: Decimal| None = None
    dimensions_cm: str| None = None

    extra_data: dict[str, Any] | None = None


class DocumentItemUpdate(BaseModel):
    line_number:    int | None = None
    description:    str | None = None
    quantity:       Decimal | None = None
    unit:           str | None = None
    brand:          str | None = None
    model:          str | None = None
    origin_country: str | None = None
    warranty:       str | None = None
    unit_price:     Decimal | None = None
    total_price:    Decimal | None = None
    currency:       str | None = None
    delivery_terms: str | None = None
    lead_time:      str | None = None
    hs_code:        str | None = None
    package_count:  int | None = None
    gross_weight_kg: Decimal | None = None
    net_weight_kg:  Decimal | None = None
    dimensions_cm:  str | None = None
    extra_data:     dict[str, Any] | None = None


class DocumentItemLineOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id:             UUID
    item_id:        UUID
    document_type:  DocumentType
    document_id:    UUID
    line_number:    int
    description:    str | None = None
    quantity:       Decimal | None = None
    unit:           str | None = None
    brand:          str | None = None
    model:          str | None = None
    origin_country: str | None = None
    warranty:       str | None = None
    unit_price:     Decimal | None = None
    total_price:    Decimal | None = None
    currency:       str | None = None
    delivery_terms: str | None = None
    lead_time:      str | None = None
    hs_code:        str | None = None
    package_count:  int | None = None
    gross_weight_kg: Decimal | None = None
    net_weight_kg:  Decimal | None = None
    dimensions_cm:  str | None = None
    extra_data:     dict[str, Any] | None = None
    created_at:     datetime
    updated_at:     datetime