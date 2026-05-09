import enum
import uuid
from tkinter import Text

from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Column, String, DateTime, func, ForeignKey, Enum, Integer, Text

from app.core.database import Base


class ItemUnit(str, enum.Enum):
    PCS = "pcs"
    KG = "kg"
    TON = "ton"
    METER = "meter"
    LITER = "liter"
    BOX = "box"
    SET = "set"
    ROLL = "roll"
    OTHER = "other"

class Item(Base):
    __tablename__ = "items"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    request_id = Column(UUID(as_uuid=True), ForeignKey("requests.id"))

    line_number = Column(Integer, nullable=False)
    description = Column(Text, nullable=False)
    quantity = Column(Integer, nullable=False)
    unit = Column(Enum(ItemUnit), nullable=False)

    notes = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
