"""add flashcard starred

Revision ID: 20260628_000003
Revises: 20260628_000002
Create Date: 2026-06-28 04:00:00
"""

from alembic import op
import sqlalchemy as sa

revision = "20260628_000003"
down_revision = "20260628_000002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "flashcards",
        sa.Column("is_starred", sa.Boolean(), nullable=False, server_default=sa.false()),
    )


def downgrade() -> None:
    with op.batch_alter_table("flashcards") as batch_op:
        batch_op.drop_column("is_starred")
