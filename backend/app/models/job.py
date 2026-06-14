import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text, Uuid, func  # noqa: F401
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import JobStatus, OperationMode


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    channel_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("channels.id"), nullable=False)
    topic_candidate_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("topic_candidates.id"), unique=True, nullable=False
    )
    status: Mapped[JobStatus] = mapped_column(
        Enum(
            JobStatus,
            name="job_status",
            values_callable=lambda x: [e.value for e in x],
            native_enum=False,
        ),
        default=JobStatus.TOPIC_APPROVED,
    )
    operation_mode: Mapped[OperationMode] = mapped_column(
        Enum(
            OperationMode,
            name="job_operation_mode",
            values_callable=lambda x: [e.value for e in x],
            native_enum=False,
        ),
        default=OperationMode.SEMI_AUTO,
    )
    priority: Mapped[int] = mapped_column(Integer, default=0)
    scheduled_publish_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    hold_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    assigned_operator_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    channel: Mapped["Channel"] = relationship(back_populates="jobs")
    topic_candidate: Mapped["TopicCandidate"] = relationship(back_populates="job")
    stages: Mapped[list["JobStage"]] = relationship(back_populates="job", cascade="all, delete-orphan")
    script: Mapped["Script | None"] = relationship(back_populates="job", uselist=False, cascade="all, delete-orphan")
    render_output: Mapped["RenderOutput | None"] = relationship(
        back_populates="job", uselist=False, cascade="all, delete-orphan"
    )
    upload_record: Mapped["UploadRecord | None"] = relationship(
        back_populates="job", uselist=False, cascade="all, delete-orphan"
    )
    assets: Mapped[list["Asset"]] = relationship(back_populates="job", cascade="all, delete-orphan")
    performance_metrics: Mapped[list["PerformanceMetric"]] = relationship(
        back_populates="job", cascade="all, delete-orphan"
    )
    render_template: Mapped[str] = mapped_column(String(32), default="bold_center")
    ab_variant: Mapped[str | None] = mapped_column(String(32), nullable=True)
