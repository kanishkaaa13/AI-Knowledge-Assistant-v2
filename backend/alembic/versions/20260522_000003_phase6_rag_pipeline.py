"""phase 6 rag pipeline"""

from alembic import op
import sqlalchemy as sa


revision = "20260522_000003"
down_revision = "20260522_000002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("document_chunks", sa.Column("vector_id", sa.Text(), nullable=True))
    op.create_index(op.f("ix_document_chunks_vector_id"), "document_chunks", ["vector_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_document_chunks_vector_id"), table_name="document_chunks")
    op.drop_column("document_chunks", "vector_id")
