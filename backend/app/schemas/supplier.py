from uuid import UUID
from pydantic import BaseModel, EmailStr, ConfigDict


# Frontend --> backend Creating supplier
class SupplierCreate(BaseModel):
    company_name : str
    email : EmailStr
    phone_1 : str
    phone_2 : str
    address : str | None = None

#Frontend --> backend Updating supplier
class SupplierUpdate(BaseModel):
    company_name: str | None= None
    email: EmailStr | None= None
    phone_1: str | None= None
    phone_2: str | None= None
    address: str | None= None
    is_active: bool | None= None

# backend --> frontend
class SupplierOut(BaseModel):
    # allows Pydantic to read data from SQLAlchemy objects
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    company_name: str
    email: str
    phone_1: str
    phone_2: str
    address: str
    is_active: bool