"""
Unified Messages API — single inbox for email, SMS, Slack, etc.

Provides:
  GET  /messages/conversations              — list all conversations
  GET  /messages/conversations/{id}         — get conversation + messages
  GET  /messages/conversations/{id}/messages — paginated messages
  POST /messages/send                       — send a new message
  POST /messages/conversations/{id}/reply   — reply to a conversation
  POST /messages/conversations/{id}/read    — mark as read
  GET  /messages/unread-count               — unread count by platform
  POST /messages/webhook                    — inbound webhook (Twilio, etc.)
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel
from sqlalchemy import select, func, desc
from sqlalchemy.orm import Session

from ...auth import TokenPayload
from .db import engine as _shared_engine
from .deps import require_user
from database.models.unified_message import (
    UnifiedConversation, UnifiedMessage, ConversationParticipant,
    MessagePlatform, MessageDirection, MessageStatus
)

router = APIRouter(prefix="/messages", tags=["messages"])


def _get_db() -> Session:
    return Session(_shared_engine)


class SendMessageRequest(BaseModel):
    conversation_id: Optional[str] = None
    platform: str = "sms"
    to: str = ""
    subject: Optional[str] = None
    content: str = ""
    content_html: Optional[str] = None


class ReplyRequest(BaseModel):
    content: str = ""
    content_html: Optional[str] = None


@router.get("/conversations")
def list_conversations(
    platform: Optional[str] = Query(None),
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0),
    current_user: TokenPayload = Depends(require_user),
):
    """List all conversations for the current user."""
    db = _get_db()
    try:
        query = select(UnifiedConversation).where(
            UnifiedConversation.user_id == UUID(current_user.sub)
        )
        if platform:
            query = query.where(UnifiedConversation.platform == platform)
        query = query.order_by(desc(UnifiedConversation.last_message_at)).offset(offset).limit(limit)
        result = db.execute(query)
        conversations = result.scalars().all()

        return [
            {
                "id": str(c.id),
                "user_id": str(c.user_id),
                "platform": c.platform.value if isinstance(c.platform, MessagePlatform) else str(c.platform),
                "external_thread_id": c.external_thread_id,
                "subject": c.subject,
                "participant_identifiers": c.meta_json.get("participants", []) if c.meta_json else [],
                "last_message_at": c.last_message_at.isoformat() if c.last_message_at else None,
                "unread_count": c.unread_count,
                "metadata": c.meta_json,
                "created_at": c.created_at.isoformat() if c.created_at else None,
                "updated_at": c.updated_at.isoformat() if c.updated_at else None,
            }
            for c in conversations
        ]
    finally:
        db.close()


@router.get("/conversations/{conversation_id}")
def get_conversation(
    conversation_id: str,
    limit: int = Query(100, le=200),
    before: Optional[str] = Query(None),
    current_user: TokenPayload = Depends(require_user),
):
    """Get a conversation with its messages."""
    db = _get_db()
    try:
        uid = UUID(current_user.sub)
        query = select(UnifiedConversation).where(
            UnifiedConversation.id == UUID(conversation_id),
            UnifiedConversation.user_id == uid,
        )
        result = db.execute(query)
        conversation = result.scalar_one_or_none()
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")

        # Get messages
        msg_query = select(UnifiedMessage).where(
            UnifiedMessage.conversation_id == UUID(conversation_id)
        ).order_by(desc(UnifiedMessage.created_at)).limit(limit)
        if before:
            try:
                before_dt = datetime.fromisoformat(before.replace("Z", "+00:00"))
                msg_query = msg_query.where(UnifiedMessage.created_at < before_dt)
            except ValueError:
                pass
        msg_result = db.execute(msg_query)
        messages = list(reversed(msg_result.scalars().all()))

        return {
            "conversation": {
                "id": str(conversation.id),
                "user_id": str(conversation.user_id),
                "platform": conversation.platform.value if isinstance(conversation.platform, MessagePlatform) else str(conversation.platform),
                "external_thread_id": conversation.external_thread_id,
                "subject": conversation.subject,
                "participant_identifiers": conversation.meta_json.get("participants", []) if conversation.meta_json else [],
                "last_message_at": conversation.last_message_at.isoformat() if conversation.last_message_at else None,
                "unread_count": conversation.unread_count,
                "metadata": conversation.meta_json,
                "created_at": conversation.created_at.isoformat() if conversation.created_at else None,
                "updated_at": conversation.updated_at.isoformat() if conversation.updated_at else None,
            },
            "messages": [
                {
                    "id": str(m.id),
                    "conversation_id": str(m.conversation_id),
                    "user_id": str(m.user_id),
                    "platform": m.platform.value if isinstance(m.platform, MessagePlatform) else str(m.platform),
                    "direction": m.direction.value if isinstance(m.direction, MessageDirection) else str(m.direction),
                    "status": m.status.value if isinstance(m.status, MessageStatus) else str(m.status),
                    "external_id": m.external_id,
                    "sender": m.sender,
                    "recipient": m.recipient,
                    "subject": m.subject,
                    "content": m.content,
                    "content_html": m.content_html,
                    "attachments": m.attachments,
                    "error_message": m.error_message,
                    "sent_at": m.sent_at.isoformat() if m.sent_at else None,
                    "delivered_at": m.delivered_at.isoformat() if m.delivered_at else None,
                    "read_at": m.read_at.isoformat() if m.read_at else None,
                    "created_at": m.created_at.isoformat() if m.created_at else None,
                    "updated_at": m.updated_at.isoformat() if m.updated_at else None,
                }
                for m in messages
            ],
        }
    finally:
        db.close()


@router.get("/conversations/{conversation_id}/messages")
def get_messages(
    conversation_id: str,
    limit: int = Query(50, le=100),
    before: Optional[str] = Query(None),
    current_user: TokenPayload = Depends(require_user),
):
    """Get messages for a conversation (paginated)."""
    db = _get_db()
    try:
        uid = UUID(current_user.sub)
        conv_query = select(UnifiedConversation).where(
            UnifiedConversation.id == UUID(conversation_id),
            UnifiedConversation.user_id == uid,
        )
        conv_result = db.execute(conv_query)
        if not conv_result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Conversation not found")

        msg_query = select(UnifiedMessage).where(
            UnifiedMessage.conversation_id == UUID(conversation_id)
        ).order_by(desc(UnifiedMessage.created_at)).limit(limit)
        if before:
            try:
                before_dt = datetime.fromisoformat(before.replace("Z", "+00:00"))
                msg_query = msg_query.where(UnifiedMessage.created_at < before_dt)
            except ValueError:
                pass
        msg_result = db.execute(msg_query)
        messages = list(reversed(msg_result.scalars().all()))

        return [
            {
                "id": str(m.id),
                "conversation_id": str(m.conversation_id),
                "user_id": str(m.user_id),
                "platform": m.platform.value if isinstance(m.platform, MessagePlatform) else str(m.platform),
                "direction": m.direction.value if isinstance(m.direction, MessageDirection) else str(m.direction),
                "status": m.status.value if isinstance(m.status, MessageStatus) else str(m.status),
                "external_id": m.external_id,
                "sender": m.sender,
                "recipient": m.recipient,
                "subject": m.subject,
                "content": m.content,
                "content_html": m.content_html,
                "attachments": m.attachments,
                "error_message": m.error_message,
                "sent_at": m.sent_at.isoformat() if m.sent_at else None,
                "delivered_at": m.delivered_at.isoformat() if m.delivered_at else None,
                "read_at": m.read_at.isoformat() if m.read_at else None,
                "created_at": m.created_at.isoformat() if m.created_at else None,
                "updated_at": m.updated_at.isoformat() if m.updated_at else None,
            }
            for m in messages
        ]
    finally:
        db.close()


@router.post("/send")
def send_message(
    body: SendMessageRequest,
    current_user: TokenPayload = Depends(require_user),
):
    """Send a new message (creates conversation if needed)."""
    db = _get_db()
    try:
        uid = UUID(current_user.sub)
        platform = body.platform or "sms"
        to = body.to
        content = body.content
        subject = body.subject
        content_html = body.content_html
        conversation_id = body.conversation_id

        if not to:
            raise HTTPException(status_code=400, detail="Recipient 'to' is required")

        # Find or create conversation
        conversation = None
        if conversation_id:
            conv_query = select(UnifiedConversation).where(
                UnifiedConversation.id == UUID(conversation_id),
                UnifiedConversation.user_id == uid,
            )
            conv_result = db.execute(conv_query)
            conversation = conv_result.scalar_one_or_none()

        if not conversation:
            conversation = UnifiedConversation(
                user_id=uid,
                platform=platform,
                subject=subject,
                meta_json={"participants": [to]},
            )
            db.add(conversation)
            db.flush()

            # Add recipient as participant
            participant = ConversationParticipant(
                conversation_id=conversation.id,
                participant_type="phone" if platform == "sms" else "email",
                participant_value=to,
                is_self=False,
            )
            db.add(participant)

            # Add self as participant
            self_participant = ConversationParticipant(
                conversation_id=conversation.id,
                participant_type="phone" if platform == "sms" else "email",
                participant_value=current_user.email,
                participant_name=current_user.name,
                is_self=True,
            )
            db.add(self_participant)

        # Create outbound message
        message = UnifiedMessage(
            conversation_id=conversation.id,
            user_id=uid,
            platform=platform,
            direction=MessageDirection.OUTBOUND,
            status=MessageStatus.SENT,
            sender=current_user.email,
            recipient=to,
            subject=subject,
            content=content,
            content_html=content_html,
            sent_at=datetime.utcnow(),
        )
        db.add(message)

        # Update conversation
        conversation.last_message_at = datetime.utcnow()
        conversation.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(message)

        return {
            "id": str(message.id),
            "conversation_id": str(message.conversation_id),
            "user_id": str(message.user_id),
            "platform": message.platform.value if isinstance(message.platform, MessagePlatform) else str(message.platform),
            "direction": message.direction.value if isinstance(message.direction, MessageDirection) else str(message.direction),
            "status": message.status.value if isinstance(message.status, MessageStatus) else str(message.status),
            "external_id": message.external_id,
            "sender": message.sender,
            "recipient": message.recipient,
            "subject": message.subject,
            "content": message.content,
            "content_html": message.content_html,
            "attachments": message.attachments,
            "error_message": message.error_message,
            "sent_at": message.sent_at.isoformat() if message.sent_at else None,
            "delivered_at": message.delivered_at.isoformat() if message.delivered_at else None,
            "read_at": message.read_at.isoformat() if message.read_at else None,
            "created_at": message.created_at.isoformat() if message.created_at else None,
            "updated_at": message.updated_at.isoformat() if message.updated_at else None,
        }
    finally:
        db.close()


@router.post("/conversations/{conversation_id}/reply")
def reply_to_conversation(
    conversation_id: str,
    body: ReplyRequest,
    current_user: TokenPayload = Depends(require_user),
):
    """Reply to an existing conversation."""
    db = _get_db()
    try:
        uid = UUID(current_user.sub)
        content = body.content
        content_html = body.content_html

        if not content:
            raise HTTPException(status_code=400, detail="Content is required")

        # Verify conversation belongs to user
        conv_query = select(UnifiedConversation).where(
            UnifiedConversation.id == UUID(conversation_id),
            UnifiedConversation.user_id == uid,
        )
        conv_result = db.execute(conv_query)
        conversation = conv_result.scalar_one_or_none()
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")

        # Find a recipient from participants
        part_query = select(ConversationParticipant).where(
            ConversationParticipant.conversation_id == UUID(conversation_id),
            ConversationParticipant.is_self == False,
        )
        part_result = db.execute(part_query)
        recipient_participant = part_result.scalars().first()
        if not recipient_participant:
            raise HTTPException(status_code=400, detail="No recipient found for conversation")

        # Create reply message
        message = UnifiedMessage(
            conversation_id=UUID(conversation_id),
            user_id=uid,
            platform=conversation.platform,
            direction=MessageDirection.OUTBOUND,
            status=MessageStatus.SENT,
            sender=current_user.email,
            recipient=recipient_participant.participant_value,
            subject=conversation.subject,
            content=content,
            content_html=content_html,
            sent_at=datetime.utcnow(),
        )
        db.add(message)

        conversation.last_message_at = datetime.utcnow()
        conversation.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(message)

        return {
            "id": str(message.id),
            "conversation_id": str(message.conversation_id),
            "user_id": str(message.user_id),
            "platform": message.platform.value if isinstance(message.platform, MessagePlatform) else str(message.platform),
            "direction": message.direction.value if isinstance(message.direction, MessageDirection) else str(message.direction),
            "status": message.status.value if isinstance(message.status, MessageStatus) else str(message.status),
            "external_id": message.external_id,
            "sender": message.sender,
            "recipient": message.recipient,
            "subject": message.subject,
            "content": message.content,
            "content_html": message.content_html,
            "attachments": message.attachments,
            "error_message": message.error_message,
            "sent_at": message.sent_at.isoformat() if message.sent_at else None,
            "delivered_at": message.delivered_at.isoformat() if message.delivered_at else None,
            "read_at": message.read_at.isoformat() if message.read_at else None,
            "created_at": message.created_at.isoformat() if message.created_at else None,
            "updated_at": message.updated_at.isoformat() if message.updated_at else None,
        }
    finally:
        db.close()


@router.post("/conversations/{conversation_id}/read")
def mark_as_read(
    conversation_id: str,
    current_user: TokenPayload = Depends(require_user),
):
    """Mark all messages in a conversation as read."""
    db = _get_db()
    try:
        uid = UUID(current_user.sub)
        conv_query = select(UnifiedConversation).where(
            UnifiedConversation.id == UUID(conversation_id),
            UnifiedConversation.user_id == uid,
        )
        conv_result = db.execute(conv_query)
        conversation = conv_result.scalar_one_or_none()
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")

        # Mark unread inbound messages as read
        msg_query = select(UnifiedMessage).where(
            UnifiedMessage.conversation_id == UUID(conversation_id),
            UnifiedMessage.direction == MessageDirection.INBOUND,
            UnifiedMessage.status != MessageStatus.READ,
        )
        msg_result = db.execute(msg_query)
        messages = msg_result.scalars().all()

        for msg in messages:
            msg.status = MessageStatus.READ
            msg.read_at = datetime.utcnow()

        conversation.unread_count = 0
        db.commit()

        return {"status": "ok", "marked_read": len(messages)}
    finally:
        db.close()


@router.get("/unread-count")
def get_unread_count(
    current_user: TokenPayload = Depends(require_user),
):
    """Get total unread count across all platforms."""
    db = _get_db()
    try:
        uid = UUID(current_user.sub)
        conv_query = select(UnifiedConversation).where(
            UnifiedConversation.user_id == uid,
        )
        conv_result = db.execute(conv_query)
        conversations = conv_result.scalars().all()

        total = sum(c.unread_count for c in conversations)
        by_platform = {}
        for c in conversations:
            platform = c.platform.value if isinstance(c.platform, MessagePlatform) else str(c.platform)
            by_platform[platform] = by_platform.get(platform, 0) + c.unread_count

        return {"total": total, "by_platform": by_platform}
    finally:
        db.close()


@router.post("/webhook")
def receive_webhook(request: Request):
    """Receive inbound messages from Twilio, Gmail, etc."""
    # This is a public endpoint (no auth) for webhooks
    # In production, validate webhook signatures
    body = request.json()
    content = body.get("content", "")
    sender = body.get("sender", "")
    subject = body.get("subject")
    platform = body.get("platform", "sms")

    # For now, return a simple acknowledgment
    # Real implementation would map incoming messages to users
    return {"status": "received", "platform": platform, "sender": sender}