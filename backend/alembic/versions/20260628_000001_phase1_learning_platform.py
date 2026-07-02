"""phase 1 learning platform tables

Revision ID: 20260628_000001
Revises: 20260522_000005
Create Date: 2026-06-28 02:50:00
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260628_000001"
down_revision = "20260522_000005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create notes table
    op.create_table(
        "notes",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("content", sa.Text(), nullable=False, server_default=""),
        sa.Column("is_pinned", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("tags", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_notes_title", "notes", ["title"], unique=False)
    op.create_index("ix_notes_user_id_updated_at", "notes", ["user_id", "updated_at"], unique=False)
    op.create_index("ix_notes_user_id_is_pinned", "notes", ["user_id", "is_pinned"], unique=False)

    # Create flashcards table
    op.create_table(
        "flashcards",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("front", sa.Text(), nullable=False),
        sa.Column("back", sa.Text(), nullable=False),
        sa.Column("difficulty", sa.String(length=20), nullable=False, server_default="medium"),
        sa.Column("tags", sa.Text(), nullable=True),
        sa.Column("source_context", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["document_id"], ["uploaded_documents.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_flashcards_user_id_updated_at", "flashcards", ["user_id", "updated_at"], unique=False)
    op.create_index("ix_flashcards_user_id_document_id", "flashcards", ["user_id", "document_id"], unique=False)


def downgrade() -> None:
    # Drop flashcards table and indexes
    op.drop_index("ix_flashcards_user_id_document_id", table_name="flashcards")
    op.drop_index("ix_flashcards_user_id_updated_at", table_name="flashcards")
    op.drop_table("flashcards")

    # Drop notes table and indexes
    op.drop_index("ix_notes_user_id_is_pinned", table_name="notes")
    op.drop_index("ix_notes_user_id_updated_at", table_name="notes")
    op.drop_index("ix_notes_title", table_name="notes")
    op.drop_table("notes")
