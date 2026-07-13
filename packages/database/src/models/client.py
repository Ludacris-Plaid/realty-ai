import uuid
from datetime import datetime

from sqlalchemy import String, Text, DateTime, ForeignKey, Numeric, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from base import Base
import enum


class ClientType(str, enum.Enum):
    BUYER = "buyer"
    SELLER = "seller"
    BOTH = "both"


class ClientStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    CLOSED = "closed"
    LOST = "lost"


class Client(Base):
    __tablename__ = "clients"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    brokerage_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)

    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255))
    phone: Mapped[str | None] = mapped_column(String(50))
    client_type: Mapped[ClientType] = mapped_column(SAEnum(ClientType, name="client_type"), default=ClientType.BUYER)
    status: Mapped[ClientStatus] = mapped_column(SAEnum(ClientStatus, name="client_status"), default=ClientStatus.ACTIVE)
    budget_min: Mapped[float | None] = mapped_column(Numeric(12,2))
    budget_max: Mapped[float | None] = mapped_column(Numeric(12,2))
    location_interest: Mapped[str | None] = mapped_column(String(255))
    notes: Mapped[str | None] = mapped_column(Text)
    source: Mapped[str | None] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    agent: Mapped["User"] = relationship(back_populates="clients", foreign_keys=[agent_id])
