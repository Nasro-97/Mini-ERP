from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr


class SettingsBase(BaseModel):
    company_email: EmailStr | None = None
    company_phone: str | None = None
    company_logo_url: str | None = None

    rfq_email_template: str | None = None
    technical_offer_template: str | None = None
    commercial_offer_template: str | None = None
    po_template: str | None = None


class SettingsUpdate(BaseModel):
    company_email: EmailStr | None = None
    company_phone: str | None = None
    company_logo_url: str | None = None

    rfq_email_template: str | None = None
    technical_offer_template: str | None = None
    commercial_offer_template: str | None = None
    po_template: str | None = None


class SettingsOutput(SettingsBase):
    id: UUID
    created_at: datetime | None = None
    updated_at: datetime | None = None

    class Config:
        from_attributes = True