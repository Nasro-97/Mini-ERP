import uuid
from sqlalchemy import Column, String, Boolean, DateTime, func
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base

class Supplier(Base):
    __tablename__ = "suppliers"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    company_name = Column(String(150), nullable=False, unique=True)
    email = Column(String(150), nullable=False)
    phone_1 = Column(String(20), nullable=False)
    phone_2 = Column(String(20))
    address = Column(String(300))

    is_active = Column(Boolean, nullable=False, default=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())