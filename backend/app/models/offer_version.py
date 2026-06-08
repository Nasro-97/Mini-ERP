import uuid
from app.core.database import Base
from sqlalchemy import Column, String, DateTime, Text, Enum, ForeignKey, func, Numeric, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.offer import OfferStatus


class OfferVersion(Base):
    __tablename__ = "offer_versions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    offer_id = Column(UUID(as_uuid=True), ForeignKey('offers.id'), nullable=False)

    version_number = Column(Integer, nullable=False)
    status = Column(Enum(OfferStatus),nullable=False, default=OfferStatus.DRAFT)

    # price
    total_price = Column(Numeric(15, 4), nullable=True)
    total_price_letters = Column(String(500), nullable=True)

    # commercial terms
    payment_terms = Column(String(500), nullable=True)
    delivery_terms = Column(String(500), nullable=True)
    delivery_period = Column(String(200), nullable=True)
    validity_date = Column(DateTime(timezone=True), nullable=True)
    country_of_origin = Column(String(200), nullable=True)
    notes = Column(Text, nullable=True)

    # COD approval
    cod_notes = Column(Text, nullable=True)
    cod_actioned_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=True)
    cod_actioned_at = Column(DateTime(timezone=True), nullable=True)

    # client response
    client_notes = Column(Text, nullable=True)
    client_responded_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    offer = relationship("Offer", back_populates="versions")