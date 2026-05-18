from uuid import UUID
from pydantic import BaseModel, ConfigDict
from decimal import Decimal
from datetime import datetime
from app.models.offer import OfferStatus


# Offer schemas

class OfferCreate(BaseModel):
    request_id:     UUID
    quotation_id:   UUID


class OfferOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id:                 UUID
    request_id:         UUID
    quotation_id:       UUID
    created_by_user_id: UUID
    offer_number:       str
    current_version:    int
    created_at:         datetime
    updated_at:         datetime


# Offer Version Schemas

class OfferVersionCreate(BaseModel):
    currency:           str | None = None
    total_price:        Decimal | None = None
    total_price_letters: str | None = None
    payment_terms:      str | None = None
    delivery_terms:     str | None = None
    delivery_period:    str | None = None
    validity_date:      datetime | None = None
    country_of_origin:  str | None = None
    notes:              str | None = None


class OfferVersionUpdate(BaseModel):
    currency:           str | None = None
    total_price:        Decimal | None = None
    total_price_letters: str | None = None
    payment_terms:      str | None = None
    delivery_terms:     str | None = None
    delivery_period:    str | None = None
    validity_date:      datetime | None = None
    country_of_origin:  str | None = None
    notes:              str | None = None


class CodResponseSchema(BaseModel):
    notes: str | None = None


class ClientResponseSchema(BaseModel):
    client_status:  str  # approved / rejected / revision_requested
    client_notes:   str | None = None


class OfferVersionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id:                     UUID
    offer_id:               UUID
    created_by_user_id:     UUID
    version_number:         int
    status:                 OfferStatus

    currency:               str | None = None
    total_price:            Decimal | None = None
    total_price_letters:    str | None = None
    payment_terms:          str | None = None
    delivery_terms:         str | None = None
    delivery_period:        str | None = None
    validity_date:          datetime | None = None
    country_of_origin:      str | None = None
    notes:                  str | None = None

    cod_notes:              str | None = None
    cod_approved_by_id:     UUID | None = None
    cod_approved_at:        datetime | None = None

    client_notes:           str | None = None
    client_responded_at:    datetime | None = None

    created_at:             datetime
    updated_at:             datetime


class OfferWithVersionsOut(OfferOut):
    versions: list[OfferVersionOut] = []