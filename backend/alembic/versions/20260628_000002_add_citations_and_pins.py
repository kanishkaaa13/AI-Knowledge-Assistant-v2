"""add citations and pins

Revision ID: 20260628_000002
Revises: 20260628_000001
Create Date: 2026-06-28 03:00:00
"""

from alembic import op
import sqlalchemy as sa

revision = "20260628_000002"
down_revision = "20260628_000001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add columns
    op.add_column(
        "conversations",
        sa.Column("is_pinned", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column(
        "messages",
        sa.Column("citations", sa.Text(), nullable=True),
    )
    op.add_column(
        "document_chunks",
        sa.Column("paragraph_index", sa.Integer(), nullable=True),
    )


def downgrade() -> None:
    # Drop columns using batch operations for SQLite safety
    with op.batch_alter_table("conversations") as batch_op:
        batch_op.drop_column("is_pinned")
    with op.batch_alter_table("messages") as batch_op:
        batch_op.drop_column("citations")
    with op.batch_alter_table("document_chunks") as batch_op:
        batch_op.drop_column("paragraph_index")
