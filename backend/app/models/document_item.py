import uuid
import enum
from sqlalchemy import Column, String, Numeric, Integer, Text, Enum, ForeignKey, DateTime, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.core.database import Base

class DocumentType(str, enum.Enum):
    REQUEST = "request"
    RFQ = "rfq"
    QUOTATION = "quotation"
    OFFER_VERSION = "offer_version"
    PURCHASE_ORDER = "purchase_order"
    SHIPMENT = "shipment"


class DocumentItem(Base):
    __tablename__ = "documents_item"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), nullable=False)
    document_type = Column(Enum(DocumentType), nullable=False)

    line_number = Column(Integer, nullable=False)
    description = Column(Text, nullable=False)
    quantity = Column(Numeric(12, 3), nullable=True)
    unit = Column(String(50),nullable=True)

    origin_country = Column(String(100), nullable=True)
    warranty = Column(String(200), nullable=True)
    unit_price = Column(Numeric(15, 4), nullable=True)
    total_price = Column(Numeric(15, 4), nullable=True)
    currency = Column(String(10), nullable=True)

    hs_code = Column(String(50), nullable=True)
    package_count = Column(Integer, nullable=True)
    gross_weight_kg = Column(Numeric(10, 3), nullable=True)
    net_weight_kg = Column(Numeric(10, 3), nullable=True)
    dimensions_cm = Column(String(100), nullable=True)

    extra_data = Column(JSONB, nullable=True, default=dict)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())





