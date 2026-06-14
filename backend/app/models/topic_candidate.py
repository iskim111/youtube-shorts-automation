import uuid
from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, Enum, ForeignKey, Numeric, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import CopyrightRisk, TopicStatus


class TopicCandidate(Base):
    __tablename__ = "topic_candidates"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    channel_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("channels.id"), nullable=False)
    category: Mapped[str] = mapped_column(String(64), nullable=False)
    keyword_cluster: Mapped[list] = mapped_column(JSON, default=list)
    hook_line: Mapped[str] = mapped_column(Text, nullable=False)
    score_view_potential: Mapped[float] = mapped_column(Numeric(5, 1), default=0)
    score_competition: Mapped[float] = mapped_column(Numeric(5, 1), default=0)
    score_production: Mapped[float] = mapped_column(Numeric(5, 1), default=0)
    score_copyright_safety: Mapped[float] = mapped_column(Numeric(5, 1), default=0)
    score_final: Mapped[float] = mapped_column(Numeric(5, 1), default=0)
    score_breakdown: Mapped[dict] = mapped_column(JSON, default=dict)
    status: Mapped[TopicStatus] = mapped_column(
        Enum(
            TopicStatus,
            name="topic_status",
            values_callable=lambda x: [e.value for e in x],
            native_enum=False,
        ),
        default=TopicStatus.GENERATED,
    )
    source_links: Mapped[list] = mapped_column(JSON, default=list)
    ai_label_required: Mapped[bool] = mapped_column(Boolean, default=False)
    copyright_risk: Mapped[CopyrightRisk] = mapped_column(
        Enum(
            CopyrightRisk,
            name="copyright_risk",
            values_callable=lambda x: [e.value for e in x],
            native_enum=False,
        ),
        default=CopyrightRisk.LOW,
    )
    similarity_penalty: Mapped[float] = mapped_column(Numeric(5, 1), default=0)
    policy_penalty: Mapped[float] = mapped_column(Numeric(5, 1), default=0)
    campaign_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    channel: Mapped["Channel"] = relationship(back_populates="topic_candidates")
    job: Mapped["Job | None"] = relationship(back_populates="topic_candidate", uselist=False)
