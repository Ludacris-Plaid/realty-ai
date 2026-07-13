import uuid
from datetime import datetime
from sqlalchemy import String, Text, DateTime, ForeignKey, Boolean, Integer, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from base import Base
import enum


class WorkflowStatus(str, enum.Enum):
    ACTIVE = "active"; PAUSED = "paused"; COMPLETED = "completed"; FAILED = "failed"


class WorkflowTrigger(str, enum.Enum):
    MANUAL = "manual"; NEW_LEAD = "new_lead"; LEAD_UPDATED = "lead_updated"; SCHEDULED = "scheduled"; EVENT = "event"


class Workflow(Base):
    __tablename__ = "workflows"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    brokerage_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    trigger: Mapped[WorkflowTrigger] = mapped_column(SAEnum(WorkflowTrigger, name="wf_trigger"), default=WorkflowTrigger.MANUAL)
    status: Mapped[WorkflowStatus] = mapped_column(SAEnum(WorkflowStatus, name="wf_status"), default=WorkflowStatus.ACTIVE)
    config: Mapped[dict | None] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    steps: Mapped[list["WorkflowStep"]] = relationship(back_populates="workflow", cascade="all, delete-orphan", order_by="WorkflowStep.order")


class WorkflowStep(Base):
    __tablename__ = "workflow_steps"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workflow_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("workflows.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    step_type: Mapped[str] = mapped_column(String(100), nullable=False)
    order: Mapped[int] = mapped_column(Integer, default=0)
    config: Mapped[dict | None] = mapped_column(JSONB, default=dict)
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    workflow: Mapped["Workflow"] = relationship(back_populates="steps")
