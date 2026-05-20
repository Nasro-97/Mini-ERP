from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, EmailStr, ConfigDict


# Frontend --> backend Creating client
class ClientCreate(BaseModel):
    company_name : str
    email : EmailStr
    phone_1 : str
    phone_2 : str | None = None
    address : str | None = None

#Frontend --> backend Updating client
class ClientUpdate(BaseModel):
    company_name: str | None= None
    email: EmailStr | None= None
    phone_1: str | None= None
    phone_2: str | None= None
    address: str | None= None
    is_active: bool | None= None

# backend --> frontend
class ClientOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    company_name: str
    email: str
    phone_1: str
    phone_2: str | None= None
    address: str | None= None
    is_active: bool

    created_at: datetime
    updated_at: datetime