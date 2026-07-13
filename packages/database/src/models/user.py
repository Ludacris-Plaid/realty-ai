import uuid
from datetime import datetime

from sqlalchemy import String, Boolean, DateTime, Text, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from ..base import Base
import enum


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    AGENT = "agent"
    BROKER = "broker"
    STAFF = "staff"


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(50))
    role: Mapped[UserRole] = mapped_column(SAEnum(UserRole, name="user_role"), default=UserRole.AGENT)
    brokerage_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    agent_profile: Mapped["AgentProfile | None"] = relationship(back_populates="user", uselist=False)
    leads: Mapped[list["Lead"]] = relationship(back_populates="agent", foreign_keys="Lead.agent_id")
    clients: Mapped[list["Client"]] = relationship(back_populates="agent", foreign_keys="Client.agent_id")
    properties: Mapped[list["Property"]] = relationship(back_populates="agent")
    conversations: Mapped[list["Conversation"]] = relationship(back_populates="user")
