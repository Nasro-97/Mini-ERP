from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, ConfigDict


# This is what the frontend sends to the backend when creating a new role
class RoleCreate(BaseModel):
    name: str
    description: str | None = None

# This is what the frontend sends to the backend when updating a role
class RoleUpdate(BaseModel):
    name: str | None= None
    description: str | None = None

# This is what the backend returns to the frontend
class RoleOut(BaseModel):
    # allows Pydantic to read data from SQLAlchemy objects
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    description: str | None = None

    created_at: datetime
    updated_at: datetime