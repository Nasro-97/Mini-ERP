import enum
import uuid

from sqlalchemy import Column, String, DateTime, func, ForeignKey, Enum, Text
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base

class RFQStatus(str ,enum.Enum):
    DRAFT = "draft"
    SENT = "sent"
    QUOTE_RECEIVED = "quote_received"
    DECLINED = "declined"


class RFQ(Base):
    __tablename__ = "rfqs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    request_id = Column(UUID(as_uuid=True), ForeignKey("requests.id", ondelete="CASCADE"), nullable=False)
    supplier_id = Column(UUID(as_uuid=True), ForeignKey("suppliers.id", ondelete="CASCADE"),nullable=False)
    contact_id = Column(UUID(as_uuid=True), ForeignKey("contacts.id", ondelete="SET NULL"),nullable=True)

    procurement_manager_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"),nullable=False)

    rfq_number = Column(String(20), nullable=False, unique=True)
    status = Column(Enum(RFQStatus), nullable=False, default=RFQStatus.DRAFT)
    notes = Column(Text, nullable=True)

    response_deadline = Column(DateTime(timezone=True), nullable=False)
    sent_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())