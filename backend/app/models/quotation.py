import enum
import uuid

from sqlalchemy import Column, String, DateTime, Numeric, Text, Enum, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class QuotationStatus(str, enum.Enum):
    RECEIVED         = "received"
    UNDER_REVIEW     = "under_review"
    SELECTED         = "selected"
    REJECTED         = "rejected"


class Quotation(Base):
    __tablename__ = "quotations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    rfq_id = Column(UUID(as_uuid=True), ForeignKey("rfqs.id", ondelete="CASCADE"), nullable=False)
    supplier_id = Column(UUID(as_uuid=True), ForeignKey("suppliers.id", ondelete="RESTRICT"), nullable=False)

    status = Column(Enum(QuotationStatus), nullable=False, default=QuotationStatus.RECEIVED)

    # pricing
    currency = Column(String(10), nullable=False)
    subtotal = Column(Numeric(15, 4), nullable=False)
    shipping_cost = Column(Numeric(15, 4), nullable=True)
    taxes = Column(Numeric(15, 4), nullable=True)
    other_costs = Column(Numeric(15, 4), nullable=True)
    total_amount = Column(Numeric(15, 4), nullable=False)

    # terms
    payment_terms = Column(String(500), nullable=True)
    delivery_terms = Column(String(500), nullable=True)
    lead_time = Column(String(200), nullable=True)
    validity_date = Column(DateTime(timezone=True), nullable=False)

    # extra info the supplier sends that does not fit our fields
    notes = Column(Text, nullable=True)

    # review workflow
    submitted_for_review_at = Column(DateTime(timezone=True), nullable=True)
    rejection_notes = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())