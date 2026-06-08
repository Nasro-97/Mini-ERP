import enum
import uuid

from app.core.database import Base
from sqlalchemy import Column, String, DateTime, ForeignKey, func, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

class OfferStatus(str, enum.Enum):
    DRAFT = "draft"
    PENDING_COD_APPROVAL = "pending_cod_approval"
    COD_APPROVED = "cod_approved"
    COD_REJECTED = "cod_rejected"
    CHANGES_REQUESTED = "changes_requested"
    SENT_TO_CLIENT = "sent_to_client"
    CLIENT_APPROVED = "client_approved"
    CLIENT_REJECTED = "client_rejected"
    REVISION_REQUESTED = "revision_requested"

class Offer(Base):
    __tablename__ = "offers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    request_id = Column(UUID(as_uuid=True), ForeignKey("requests.id", ondelete="CASCADE"))
    quotation_id = Column(UUID(as_uuid=True),ForeignKey("quotations.id", ondelete="CASCADE"))
    created_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"))

    offer_number = Column(String(100), nullable=False, unique=True)
    current_version = Column(Integer, nullable=False, default=1)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    versions = relationship("OfferVersion", back_populates="offer", order_by="OfferVersion.version_number")