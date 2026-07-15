import uuid

from sqlalchemy import Column, String, DateTime, func, Text
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class Settings(Base):
    __tablename__ = "settings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    company_email = Column(String, nullable=True)
    company_phone = Column(String, nullable=True)
    company_logo_url = Column(String, nullable=True)

    rfq_email_template = Column(Text, nullable=True)
    technical_offer_template = Column(Text, nullable=True)
    commercial_offer_template = Column(Text, nullable=True)
    po_template = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())