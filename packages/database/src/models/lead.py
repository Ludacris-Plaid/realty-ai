import uuid
from datetime import datetime

from sqlalchemy import String, Text, DateTime, ForeignKey, Float, Numeric, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from ..base import Base
import enum


class LeadStatus(str, enum.Enum):
    NEW = "new"
    QUALIFYING = "qualifying"
    QUALIFIED = "qualified"
    CONTACTED = "contacted"
    APPOINTMENT_SET = "appointment_set"
    CLOSED_WON = "closed_won"
    CLOSED_LOST = "closed_lost"
    DORMANT = "dormant"


class LeadSource(str, enum.Enum):
    ZILLOW = "zillow"
    REALTOR_COM = "realtor_com"
    REDFIN = "redfin"
    WEBSITE = "website"
    REFERRAL = "referral"
    SOCIAL_MEDIA = "social_media"
    OPEN_HOUSE = "open_house"
    CALL_IN = "call_in"
    EMAIL = "email"
    OTHER = "other"


class Lead(Base):
    __tablename__ = "leads"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    brokerage_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)

    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255))
    phone: Mapped[str | None] = mapped_column(String(50))
    source: Mapped[LeadSource] = mapped_column(SAEnum(LeadSource, name="lead_source"), default=LeadSource.OTHER)
    status: Mapped[LeadStatus] = mapped_column(SAEnum(LeadStatus, name="lead_status"), default=LeadStatus.NEW)

    budget: Mapped[float | None] = mapped_column(Numeric(12,2))
    location_interest: Mapped[str | None] = mapped_column(String(255))
    property_type_interest: Mapped[str | None] = mapped_column(String(100))
    timeline: Mapped[str | None] = mapped_column(String(100))
    pre_approved: Mapped[bool | None] = mapped_column(default=None)

    ai_score: Mapped[float | None] = mapped_column(Float, default=0.0)
    ai_score_reason: Mapped[str | None] = mapped_column(Text)
    ai_score_updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    last_contacted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    notes: Mapped[str | None] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    agent: Mapped["User"] = relationship(back_populates="leads", foreign_keys=[agent_id])
