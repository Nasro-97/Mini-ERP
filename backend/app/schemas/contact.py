from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, EmailStr, ConfigDict

from app.models import CompanyType


# Frontend --> backend when creating contact
class ContactCreate(BaseModel):
    company_type: CompanyType
    company_id: UUID

    fullname: str
    position: str
    email: EmailStr
    phone_1: str
    phone_2: str | None = None

# Frontend --> backend when updating contact
class ContactUpdate(BaseModel):

    fullname: str | None = None
    position: str | None = None
    email: EmailStr | None = None
    phone_1: str | None = None
    phone_2: str | None = None

    is_active: bool | None = None

# Backend -> frontend
class ContactOut(BaseModel):
    #allows Pydantic to read data from SQLAlchemy
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    company_type: CompanyType
    company_id: UUID

    fullname: str
    position: str
    email: EmailStr
    phone_1: str
    phone_2: str | None= None

    is_active: bool

    created_at: datetime
    updated_at: datetime
