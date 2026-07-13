import uuid
from datetime import datetime, date

from sqlalchemy import String, Text, DateTime, ForeignKey, Float, Date, Numeric, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from ..base import Base
import enum


class PropertyStatus(str, enum.Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    PENDING = "pending"
    SOLD = "sold"
    EXPIRED = "expired"
    WITHDRAWN = "withdrawn"


class PropertyType(str, enum.Enum):
    SINGLE_FAMILY = "single_family"
    CONDO = "condo"
    TOWNHOUSE = "townhouse"
    MULTI_FAMILY = "multi_family"
    LAND = "land"
    COMMERCIAL = "commercial"


class Property(Base):
    __tablename__ = "properties"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    brokerage_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)
    client_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("clients.id"), nullable=True)

    address_street: Mapped[str] = mapped_column(String(255), nullable=False)
    address_city: Mapped[str] = mapped_column(String(100), nullable=False)
    address_state: Mapped[str] = mapped_column(String(50), nullable=False)
    address_zip: Mapped[str] = mapped_column(String(20), nullable=False)
    address_unit: Mapped[str | None] = mapped_column(String(50))

    property_type: Mapped[PropertyType] = mapped_column(SAEnum(PropertyType, name="property_type"), default=PropertyType.SINGLE_FAMILY)
    status: Mapped[PropertyStatus] = mapped_column(SAEnum(PropertyStatus, name="property_status"), default=PropertyStatus.DRAFT)

    beds: Mapped[int | None] = mapped_column()
    baths: Mapped[float | None] = mapped_column()
    sqft: Mapped[float | None] = mapped_column(Float)
    lot_size: Mapped[float | None] = mapped_column(Float)
    year_built: Mapped[int | None] = mapped_column()
    garage_spaces: Mapped[int | None] = mapped_column()

    list_price: Mapped[float | None] = mapped_column(Numeric(14,2))
    hoa_dues: Mapped[float | None] = mapped_column(Numeric(10,2))

    description: Mapped[str | None] = mapped_column(Text)
    features: Mapped[list | None] = mapped_column(JSONB, default=list)
    images: Mapped[list | None] = mapped_column(JSONB, default=list)
    mls_number: Mapped[str | None] = mapped_column(String(50))

    listed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    sold_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    sold_price: Mapped[float | None] = mapped_column(Numeric(14,2))

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    agent: Mapped["User"] = relationship(back_populates="properties", foreign_keys=[agent_id])
