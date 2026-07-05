import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Character(Base):
    """AI 쇼츠 고정 주인공 (HeyGen 아바타 + ElevenLabs 보이스)."""

    __tablename__ = "characters"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    role: Mapped[str] = mapped_column(String(64), nullable=False)
    heygen_avatar_id: Mapped[str] = mapped_column(String(128), default="")
    elevenlabs_voice_id: Mapped[str] = mapped_column(String(128), default="")
    speech_style: Mapped[str] = mapped_column(Text, default="")
    language_primary: Mapped[str] = mapped_column(String(8), default="ko")
    avatar_image_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    sort_order: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
