import uuid
import enum
from app.core.database import Base
from sqlalchemy import Column, String, DateTime, Text, Enum, ForeignKey, func, Numeric
from sqlalchemy.dialects.postgresql import UUID

class POStatus(str, enum.Enum):
    DRAFT       = "draft"
    SENT        = "sent"
    ACCEPTED    = "accepted"


class PurchaseOrder(Base):
    __tablename__ = "purchase_orders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    offer_version_id = Column(UUID(as_uuid=True), ForeignKey("offer_versions.id"), nullable=False)
    request_id = Column(UUID(as_uuid=True), ForeignKey("requests.id", ondelete="CASCADE"), nullable=False)
    quotation_id = Column(UUID(as_uuid=True), ForeignKey("quotations.id"), nullable=False)
    supplier_id = Column(UUID(as_uuid=True), ForeignKey("suppliers.id"), nullable=False)
    created_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    po_number = Column(String(50), nullable=False, unique=True)
    status = Column(Enum(POStatus), nullable=False, default=POStatus.DRAFT)

    payment_terms = Column(Text, nullable=True)
    delivery_terms = Column(Text, nullable=True)
    lead_time = Column(Text, nullable=True)

    notes = Column(Text, nullable=True)

    currency = Column(String(10), nullable=True)
    subtotal = Column(Numeric(15, 4), nullable=True)
    shipping_cost = Column(Numeric(15, 4), nullable=True)
    taxes = Column(Numeric(15, 4), nullable=True)
    other_costs = Column(Numeric(15, 4), nullable=True)
    total_amount = Column(Numeric(15, 4), nullable=True)

    sent_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

