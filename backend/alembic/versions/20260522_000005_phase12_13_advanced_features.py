"""phase 12 and 13 advanced assistant features

Revision ID: 20260522_000005
Revises: 20260522_000004
Create Date: 2026-05-22 17:20:00
"""

from alembic import op
import sqlalchemy as sa


revision = "20260522_000005"
down_revision = "20260522_000004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("uploaded_documents", sa.Column("ai_summary", sa.Text(), nullable=True))
    op.add_column("uploaded_documents", sa.Column("tags", sa.Text(), nullable=True))
    op.add_column("uploaded_documents", sa.Column("is_favorite", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("uploaded_documents", sa.Column("processing_error", sa.Text(), nullable=True))
    op.create_index("ix_uploaded_documents_user_id_is_favorite", "uploaded_documents", ["user_id", "is_favorite"], unique=False)

    op.add_column("conversations", sa.Column("is_favorite", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.create_index("ix_conversations_user_id_is_favorite", "conversations", ["user_id", "is_favorite"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_conversations_user_id_is_favorite", table_name="conversations")
    op.drop_column("conversations", "is_favorite")

    op.drop_index("ix_uploaded_documents_user_id_is_favorite", table_name="uploaded_documents")
    op.drop_column("uploaded_documents", "processing_error")
    op.drop_column("uploaded_documents", "is_favorite")
    op.drop_column("uploaded_documents", "tags")
    op.drop_column("uploaded_documents", "ai_summary")
