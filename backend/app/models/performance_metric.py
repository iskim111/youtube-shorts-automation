import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class PerformanceMetric(Base):
    __tablename__ = "performance_metrics"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    job_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False
    )
    youtube_video_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    views_1h: Mapped[int] = mapped_column(Integer, default=0)
    views_24h: Mapped[int] = mapped_column(Integer, default=0)
    views_7d: Mapped[int] = mapped_column(Integer, default=0)
    avg_view_duration_sec: Mapped[float] = mapped_column(Numeric(8, 2), default=0)
    retention_rate: Mapped[float] = mapped_column(Numeric(5, 4), default=0)
    ab_variant: Mapped[str | None] = mapped_column(String(32), nullable=True)
    collected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    job: Mapped["Job"] = relationship(back_populates="performance_metrics")
