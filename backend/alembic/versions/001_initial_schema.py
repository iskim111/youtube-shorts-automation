"""initial schema v1

Revision ID: 001
Revises:
Create Date: 2026-06-09

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE TYPE operation_mode AS ENUM ('manual', 'semi_auto', 'auto')")
    op.execute(
        "CREATE TYPE topic_status AS ENUM "
        "('generated', 'recommended', 'review_required', 'on_hold', 'rejected', 'approved')"
    )
    op.execute("CREATE TYPE copyright_risk AS ENUM ('low', 'medium', 'high')")
    op.execute(
        "CREATE TYPE job_status AS ENUM ("
        "'DRAFT', 'TOPIC_APPROVED', 'SCRIPT_GENERATING', 'SCRIPT_READY', 'SCRIPT_APPROVED', "
        "'TTS_QUEUED', 'TTS_PROCESSING', 'TTS_READY', 'ASSET_SEARCHING', 'ASSET_READY', "
        "'RIGHTS_CHECKING', 'RIGHTS_PASSED', 'RIGHTS_HOLD', 'MANIFEST_BUILDING', "
        "'RENDER_QUEUED', 'RENDER_PROCESSING', 'RENDER_READY', 'SUBTITLE_PROCESSING', "
        "'SUBTITLE_READY', 'THUMBNAIL_READY', 'METADATA_CHECKING', 'METADATA_APPROVED', "
        "'QA_PENDING', 'QA_APPROVED', 'QA_HOLD', 'UPLOAD_QUEUED', 'UPLOADING', 'UPLOADED', "
        "'UPLOAD_FAILED', 'PUBLISHED', 'ARCHIVED', 'CANCELLED')"
    )
    op.execute(
        "CREATE TYPE job_operation_mode AS ENUM ('manual', 'semi_auto', 'auto')"
    )
    op.execute(
        "CREATE TYPE stage_status AS ENUM ('pending', 'processing', 'success', 'failed', 'hold')"
    )

    op.create_table(
        "channels",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("youtube_channel_id", sa.String(64), unique=True, nullable=True),
        sa.Column(
            "operation_mode",
            postgresql.ENUM("manual", "semi_auto", "auto", name="operation_mode", create_type=False),
            nullable=False,
        ),
        sa.Column("daily_upload_cap", sa.Integer(), nullable=False, server_default="5"),
        sa.Column("category_allowlist", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("voice_profile_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "topic_candidates",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("code", sa.String(32), unique=True, nullable=False),
        sa.Column("channel_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("channels.id"), nullable=False),
        sa.Column("category", sa.String(64), nullable=False),
        sa.Column("keyword_cluster", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("hook_line", sa.Text(), nullable=False),
        sa.Column("score_view_potential", sa.Numeric(5, 1), server_default="0"),
        sa.Column("score_competition", sa.Numeric(5, 1), server_default="0"),
        sa.Column("score_production", sa.Numeric(5, 1), server_default="0"),
        sa.Column("score_copyright_safety", sa.Numeric(5, 1), server_default="0"),
        sa.Column("score_final", sa.Numeric(5, 1), server_default="0"),
        sa.Column("score_breakdown", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column(
            "status",
            postgresql.ENUM(
                "generated", "recommended", "review_required", "on_hold", "rejected", "approved",
                name="topic_status", create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("source_links", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("ai_label_required", sa.Boolean(), server_default="false"),
        sa.Column(
            "copyright_risk",
            postgresql.ENUM("low", "medium", "high", name="copyright_risk", create_type=False),
            nullable=False,
        ),
        sa.Column("similarity_penalty", sa.Numeric(5, 1), server_default="0"),
        sa.Column("policy_penalty", sa.Numeric(5, 1), server_default="0"),
        sa.Column("campaign_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("code", sa.String(32), unique=True, nullable=False),
        sa.Column("channel_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("channels.id"), nullable=False),
        sa.Column(
            "topic_candidate_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("topic_candidates.id"),
            unique=True,
            nullable=False,
        ),
        sa.Column(
            "status",
            postgresql.ENUM(name="job_status", create_type=False),
            nullable=False,
        ),
        sa.Column(
            "operation_mode",
            postgresql.ENUM("manual", "semi_auto", "auto", name="job_operation_mode", create_type=False),
            nullable=False,
        ),
        sa.Column("priority", sa.Integer(), server_default="0"),
        sa.Column("scheduled_publish_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("retry_count", sa.Integer(), server_default="0"),
        sa.Column("hold_reason", sa.Text(), nullable=True),
        sa.Column("assigned_operator_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "job_stages",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "job_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("jobs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("stage", sa.String(32), nullable=False),
        sa.Column(
            "status",
            postgresql.ENUM(
                "pending", "processing", "success", "failed", "hold",
                name="stage_status", create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("progress", sa.Integer(), server_default="0"),
        sa.Column("output_uri", sa.Text(), nullable=True),
        sa.Column("error_code", sa.String(64), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("job_stages")
    op.drop_table("jobs")
    op.drop_table("topic_candidates")
    op.drop_table("channels")
    op.execute("DROP TYPE stage_status")
    op.execute("DROP TYPE job_operation_mode")
    op.execute("DROP TYPE job_status")
    op.execute("DROP TYPE copyright_risk")
    op.execute("DROP TYPE topic_status")
    op.execute("DROP TYPE operation_mode")
