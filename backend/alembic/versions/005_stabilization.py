"""stabilization: users, audit_logs, performance_metrics, job ab_variant

Revision ID: 005
Revises: 004
Create Date: 2026-06-09

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE TYPE user_role AS ENUM ('admin', 'editor', 'operator', 'auditor')")
    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("email", sa.String(255), unique=True, nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column(
            "role",
            sa.Enum("admin", "editor", "operator", "auditor", name="user_role", create_type=False),
            nullable=False,
        ),
        sa.Column("is_active", sa.Boolean(), server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("actor_id", sa.Uuid(), nullable=True),
        sa.Column("actor_email", sa.String(255), nullable=True),
        sa.Column("action", sa.String(64), nullable=False),
        sa.Column("entity_type", sa.String(32), nullable=False),
        sa.Column("entity_id", sa.String(64), nullable=False),
        sa.Column("payload", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_table(
        "performance_metrics",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("job_id", sa.Uuid(), sa.ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("youtube_video_id", sa.String(32), nullable=True),
        sa.Column("views_1h", sa.Integer(), server_default="0"),
        sa.Column("views_24h", sa.Integer(), server_default="0"),
        sa.Column("views_7d", sa.Integer(), server_default="0"),
        sa.Column("avg_view_duration_sec", sa.Numeric(8, 2), server_default="0"),
        sa.Column("retention_rate", sa.Numeric(5, 4), server_default="0"),
        sa.Column("ab_variant", sa.String(32), nullable=True),
        sa.Column("collected_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.add_column("jobs", sa.Column("ab_variant", sa.String(32), nullable=True))


def downgrade() -> None:
    op.drop_column("jobs", "ab_variant")
    op.drop_table("performance_metrics")
    op.drop_table("audit_logs")
    op.drop_table("users")
    op.execute("DROP TYPE user_role")
