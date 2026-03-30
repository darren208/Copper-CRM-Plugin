"""CommunicationEvent model – one row per inbound/outbound call, SMS, or voicemail."""

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.db import Base


class CommunicationEvent(Base):
    __tablename__ = "communication_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Idempotency key – used to deduplicate retried webhook deliveries
    correlation_id: Mapped[str] = mapped_column(
        String(128), unique=True, index=True, nullable=False
    )

    # Source system that produced the event
    source: Mapped[str] = mapped_column(
        String(64), nullable=False, index=True
    )  # e.g. "ringcentral"

    # Granular type: call_ended, sms_received, voicemail, missed_call
    event_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)

    # RingCentral-assigned identifier for the underlying call/message
    ringcentral_event_id: Mapped[Optional[str]] = mapped_column(
        String(128), index=True, nullable=True
    )

    # Link to the resolved contact (may be null if caller is unknown)
    contact_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("contacts.id", ondelete="SET NULL"), nullable=True, index=True
    )

    # When the communication actually happened (not when we received the webhook)
    occurred_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Raw normalized payload stored as JSON text
    payload_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Processing lifecycle: pending → processing → completed | failed
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="pending", index=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    contact: Mapped[Optional["Contact"]] = relationship(  # noqa: F821
        "Contact", back_populates="events"
    )
    ai_jobs: Mapped[list["AIJob"]] = relationship(  # noqa: F821
        "AIJob", back_populates="communication_event", lazy="select"
    )

    def __repr__(self) -> str:
        return (
            f"<CommunicationEvent id={self.id} type={self.event_type} "
            f"status={self.status} correlation_id={self.correlation_id!r}>"
        )
