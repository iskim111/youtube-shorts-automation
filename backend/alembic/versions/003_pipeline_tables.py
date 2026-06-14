"""pipeline tables: scripts, render_outputs, upload_records

Revision ID: 003
Revises: 002
Create Date: 2026-06-09

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "scripts",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("job_id", sa.Uuid(), sa.ForeignKey("jobs.id", ondelete="CASCADE"), unique=True),
        sa.Column("content", sa.JSON(), nullable=False),
        sa.Column("duration_estimate_sec", sa.Integer(), server_default="30"),
        sa.Column("version", sa.Integer(), server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_table(
        "render_outputs",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("job_id", sa.Uuid(), sa.ForeignKey("jobs.id", ondelete="CASCADE"), unique=True),
        sa.Column("video_uri", sa.Text(), nullable=False),
        sa.Column("thumbnail_uri", sa.Text(), nullable=True),
        sa.Column("duration_sec", sa.Numeric(6, 2), server_default="30"),
        sa.Column("resolution", sa.String(16), server_default="1080x1920"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_table(
        "upload_records",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("job_id", sa.Uuid(), sa.ForeignKey("jobs.id", ondelete="CASCADE"), unique=True),
        sa.Column("youtube_video_id", sa.String(32), nullable=True),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), server_default=""),
        sa.Column("tags", sa.JSON(), server_default="[]"),
        sa.Column("ai_label_applied", sa.Boolean(), server_default="false"),
        sa.Column("privacy_status", sa.String(16), server_default="private"),
        sa.Column("upload_status", sa.String(16), server_default="queued"),
        sa.Column("idempotency_key", sa.String(64), unique=True, nullable=False),
        sa.Column("claim_detected", sa.Boolean(), server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("upload_records")
    op.drop_table("render_outputs")
    op.drop_table("scripts")
