"""Contact model – mirrors Copper Person records with phone normalisation."""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.db import Base


class Contact(Base):
    __tablename__ = "contacts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    copper_person_id: Mapped[Optional[str]] = mapped_column(
        String(64), unique=True, index=True, nullable=True
    )
    phone_e164: Mapped[Optional[str]] = mapped_column(
        String(32), index=True, nullable=True
    )
    email: Mapped[Optional[str]] = mapped_column(
        String(255), index=True, nullable=True
    )
    full_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    events: Mapped[list["CommunicationEvent"]] = relationship(  # noqa: F821
        "CommunicationEvent", back_populates="contact", lazy="select"
    )
    review_items: Mapped[list["ReviewQueueItem"]] = relationship(  # noqa: F821
        "ReviewQueueItem", back_populates="contact", lazy="select"
    )

    def __repr__(self) -> str:
        return f"<Contact id={self.id} copper_person_id={self.copper_person_id} name={self.full_name!r}>"
