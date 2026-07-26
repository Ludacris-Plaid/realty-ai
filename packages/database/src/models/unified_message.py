import uuid
from datetime import datetime
from sqlalchemy import String, Text, DateTime, ForeignKey, Enum as SAEnum, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from base import Base
import enum


class MessagePlatform(str, enum.Enum):
    EMAIL = "email"
    SMS = "sms"
    SLACK = "slack"
    WHATSAPP = "whatsapp"
    INTERNAL = "internal"


class MessageDirection(str, enum.Enum):
    INBOUND = "inbound"
    OUTBOUND = "outbound"


class MessageStatus(str, enum.Enum):
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"
    QUEUED = "queued"


class UnifiedConversation(Base):
    __tablename__ = "unified_conversations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    platform: Mapped[MessagePlatform] = mapped_column(SAEnum(MessagePlatform), nullable=False, index=True)
    external_thread_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    subject: Mapped[str | None] = mapped_column(String(500), nullable=True)
    participant_identifiers: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    last_message_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    unread_count: Mapped[int] = mapped_column(default=0, nullable=False)
    metadata: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    messages: Mapped[list["UnifiedMessage"]] = relationship(back_populates="conversation", lazy="dynamic")


class UnifiedMessage(Base):
    __tablename__ = "unified_messages"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("unified_conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    platform: Mapped[MessagePlatform] = mapped_column(SAEnum(MessagePlatform), nullable=False, index=True)
    direction: Mapped[MessageDirection] = mapped_column(SAEnum(MessageDirection), nullable=False)
    status: Mapped[MessageStatus] = mapped_column(SAEnum(MessageStatus), default=MessageStatus.QUEUED, nullable=False)
    external_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    sender: Mapped[str | None] = mapped_column(String(255), nullable=True)
    recipient: Mapped[str | None] = mapped_column(String(255), nullable=True)
    subject: Mapped[str | None] = mapped_column(String(500), nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    content_html: Mapped[str | None] = mapped_column(Text, nullable=True)
    attachments: Mapped[list[dict]] = mapped_column(JSONB, default=list, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    conversation: Mapped["UnifiedConversation"] = relationship(back_populates="messages")

    __table_args__ = (
        Index("ix_unified_messages_user_platform", "user_id", "platform"),
        Index("ix_unified_messages_conversation_created", "conversation_id", "created_at"),
    )