from uuid import UUID
from pydantic import BaseModel, EmailStr, ConfigDict
from datetime import datetime

from app.schemas.role import RoleOut


# Frontend --> backend when creating user
class UserCreate(BaseModel):
    username: str
    fullname: str
    email: EmailStr
    password: str
    role_ids: list[UUID] = []

# Frontend --> backend when updating user
class UserUpdate(BaseModel):
    username: str | None = None
    fullname: str | None = None
    email: EmailStr | None = None
    password: str | None = None
    role_ids: list[UUID] | None = None
    is_active: bool | None = None

# Backend --> frontend
class UserOut(BaseModel):
    # allows Pydantic to read data from SQLAlchemy objects
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    username: str
    fullname: str
    email: EmailStr
    roles: list[RoleOut] = []
    is_active: bool

    created_at: datetime
    updated_at: datetime

