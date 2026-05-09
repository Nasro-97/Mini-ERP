import enum
import uuid

from sqlalchemy import Column, String, DateTime, func, ForeignKey, Enum, Text
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class RequestStatus(str, enum.Enum):

    DRAFT = "draft"
    PENDING_SALES_MANAGER_APPROVAL = "pending_sales_manager_approval"
    APPROVED_FOR_SOURCING = "approved_for_sourcing"
    REJECTED = "rejected"
    RFQ_IN_PROGRESS = "rfq_in_progress"
    QUOTATION_REVIEW = "quotation_review"
    OFFER_IN_PROGRESS = "offer_in_progress"
    CLIENT_APPROVAL_PENDING = "client_approval_pending"
    APPROVED_BY_CLIENT = "approved_by_client"
    PO_IN_PROGRESS = "po_in_progress"
    SHIPMENT_IN_PROGRESS = "shipment_in_progress"
    DELIVERED = "delivered"
    CLOSED = "closed"

class RequestPriority(str, enum.Enum):

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"

class Request(Base):
    __tablename__ = "requests"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    request_number= Column(String(100), nullable=False, unique=True)
    title = Column(String(100), nullable=False)
    description = Column(Text)
    client_reference = Column(String(100), nullable=False)

    client_id = Column(UUID(as_uuid=True), ForeignKey("clients.id", ondelete="CASCADE"))
    created_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    assigned_to_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    sales_manager_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=True)

    status = Column(Enum(RequestStatus), nullable=False, default=RequestStatus.DRAFT)
    priority = Column(Enum(RequestPriority), nullable=False, default=RequestPriority.LOW)

    request_date = Column(DateTime(timezone=True), nullable=False)
    required_date = Column(DateTime(timezone=True))
    deadline = Column(DateTime(timezone=True), nullable=False)

    sales_manager_notes = Column(Text)
    sales_manager_decision_at = Column(DateTime(timezone=True))

    notes = Column(Text)


    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

