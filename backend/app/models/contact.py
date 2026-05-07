import enum
import uuid

from sqlalchemy import Column, String, DateTime, Enum, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.core.database import Base


class CompanyType(str, enum.Enum):
    CLIENT = "client"
    SUPPLIER = "supplier"

class Contact(Base):
    __tablename__ = "contacts"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_type = Column(Enum(CompanyType), nullable=False)

    # Stores the ID of either a client or supplier depending on company_type
    company_id = Column(UUID(as_uuid=True), nullable=False)

    fullname = Column(String(150), nullable=False)
    position = Column(String(100))
    email = Column(String(150))
    phone_1 = Column(String(150))
    phone_2 = Column(String(150))

    is_active = Column(Boolean, nullable=False, default=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())