import uuid

from sqlalchemy import Column, String, DateTime, Integer, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class DocumentCounter(Base):
    __tablename__ = "document_counters"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    document_type = Column(String(50), nullable=False)  # "po", "request", "rfq"
    company_code = Column(String(50), nullable=False)
    year = Column(Integer, nullable=False)

    next_number = Column(Integer, nullable=False, default=1)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("document_type", "company_code", "year", name="uq_document_counter"),
    )