"""phase 7 chromadb service"""

from alembic import op
import sqlalchemy as sa


revision = "20260522_000004"
down_revision = "20260522_000003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("document_chunks", sa.Column("page_number", sa.Integer(), nullable=True))
    op.create_index(op.f("ix_document_chunks_page_number"), "document_chunks", ["page_number"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_document_chunks_page_number"), table_name="document_chunks")
    op.drop_column("document_chunks", "page_number")
