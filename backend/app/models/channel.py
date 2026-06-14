import uuid
from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, Enum, Integer, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import OperationMode


class Channel(Base):
    __tablename__ = "channels"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    youtube_channel_id: Mapped[str | None] = mapped_column(String(64), unique=True, nullable=True)
    operation_mode: Mapped[OperationMode] = mapped_column(
        Enum(
            OperationMode,
            name="operation_mode",
            values_callable=lambda x: [e.value for e in x],
            native_enum=False,
        ),
        default=OperationMode.SEMI_AUTO,
    )
    daily_upload_cap: Mapped[int] = mapped_column(Integer, default=5)
    category_allowlist: Mapped[list] = mapped_column(JSON, default=list)
    voice_profile_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    topic_candidates: Mapped[list["TopicCandidate"]] = relationship(back_populates="channel")
    jobs: Mapped[list["Job"]] = relationship(back_populates="channel")
    oauth_credential: Mapped["OAuthCredential | None"] = relationship(
        back_populates="channel", uselist=False, cascade="all, delete-orphan"
    )
