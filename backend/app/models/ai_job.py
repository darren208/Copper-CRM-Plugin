"""
AI pipeline models:
  AIJob           – tracks one invocation of an AI model
  AIOutput        – stores the structured result produced by the job
  ReviewQueueItem – human review gate keyed to an AI output
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.db import Base


class AIJob(Base):
    __tablename__ = "ai_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    communication_event_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("communication_events.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # call_summary | sms_classifier | sms_reply | cross_sell | doc_extract |
    # dashboard_summary | gmail_draft
    job_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)

    # openai | gemini
    vendor: Mapped[str] = mapped_column(String(32), nullable=False)

    # Model name/version used
    model: Mapped[str] = mapped_column(String(128), nullable=False)

    # Version slug of the prompt template file (e.g. "v1")
    prompt_template_version: Mapped[str] = mapped_column(
        String(32), nullable=False, default="v1"
    )

    # SHA-256 of the redacted input – enables exact-match caching
    input_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)

    # Model-reported or post-processed confidence (0–1)
    confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # pending | running | completed | failed
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="pending", index=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    communication_event: Mapped[Optional["CommunicationEvent"]] = relationship(  # noqa: F821
        "CommunicationEvent", back_populates="ai_jobs"
    )
    outputs: Mapped[list["AIOutput"]] = relationship(
        "AIOutput", back_populates="ai_job", lazy="select"
    )

    def __repr__(self) -> str:
        return (
            f"<AIJob id={self.id} type={self.job_type} vendor={self.vendor} "
            f"status={self.status} confidence={self.confidence}>"
        )


class AIOutput(Base):
    __tablename__ = "ai_outputs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    ai_job_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("ai_jobs.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # call_summary | sms_classification | followup_draft | cross_sell_recommendations | …
    output_type: Mapped[str] = mapped_column(String(64), nullable=False)

    # Structured output stored as JSON text
    output_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Human review state
    approved: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    approved_by: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    approved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    ai_job: Mapped["AIJob"] = relationship("AIJob", back_populates="outputs")
    review_queue_items: Mapped[list["ReviewQueueItem"]] = relationship(
        "ReviewQueueItem", back_populates="ai_output", lazy="select"
    )

    def __repr__(self) -> str:
        return (
            f"<AIOutput id={self.id} type={self.output_type} "
            f"approved={self.approved} job_id={self.ai_job_id}>"
        )


class ReviewQueueItem(Base):
    __tablename__ = "review_queue_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    ai_output_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("ai_outputs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    contact_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("contacts.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # follow_up | compliance | billing | general
    category: Mapped[str] = mapped_column(String(64), nullable=False, index=True)

    # low | medium | high | critical
    urgency: Mapped[str] = mapped_column(
        String(32), nullable=False, default="medium", index=True
    )

    # pending | approved | rejected
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="pending", index=True
    )

    # Email or agent ID of the secretary/owner assigned to review
    assigned_to: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    resolved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    resolution_note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    ai_output: Mapped["AIOutput"] = relationship(
        "AIOutput", back_populates="review_queue_items"
    )
    contact: Mapped[Optional["Contact"]] = relationship(  # noqa: F821
        "Contact", back_populates="review_items"
    )

    def __repr__(self) -> str:
        return (
            f"<ReviewQueueItem id={self.id} category={self.category} "
            f"urgency={self.urgency} status={self.status}>"
        )
