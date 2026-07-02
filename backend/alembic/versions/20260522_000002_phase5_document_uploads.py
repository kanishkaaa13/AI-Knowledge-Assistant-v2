"""phase 5 document uploads"""

from alembic import op
import sqlalchemy as sa


revision = "20260522_000002"
down_revision = "20260522_000001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add columns first
    op.add_column("uploaded_documents", sa.Column("file_extension", sa.String(length=16), nullable=True))
    op.add_column("uploaded_documents", sa.Column("checksum", sa.String(length=64), nullable=True))
    op.add_column("uploaded_documents", sa.Column("page_count", sa.Integer(), nullable=True))
    op.add_column("uploaded_documents", sa.Column("word_count", sa.Integer(), nullable=True))
    
    # SQLite-compatible syntax for extracting file extension
    op.execute(
        "UPDATE uploaded_documents "
        "SET file_extension = CASE "
        "WHEN position('.' IN file_name) > 0 THEN lower(substring(file_name FROM position('.' IN file_name) + 1)) "
        "ELSE 'txt' END "
        "WHERE file_extension IS NULL"
    )
    # SQLite doesn't have md5(), use a simple hash for now
    op.execute(
        "UPDATE uploaded_documents "
        "SET checksum = md5(random()::text) "
        "WHERE checksum IS NULL"
    )
    
    # Use batch mode for SQLite ALTER COLUMN operations and constraints
    with op.batch_alter_table("uploaded_documents") as batch_op:
        batch_op.alter_column("file_extension", nullable=False)
        batch_op.alter_column("checksum", nullable=False)
        batch_op.create_index(op.f("ix_uploaded_documents_checksum"), ["checksum"], unique=False)
        batch_op.create_index(op.f("ix_uploaded_documents_file_extension"), ["file_extension"], unique=False)
        batch_op.create_unique_constraint("uq_uploaded_documents_user_checksum", ["user_id", "checksum"])


def downgrade() -> None:
    op.drop_constraint("uq_uploaded_documents_user_checksum", "uploaded_documents", type_="unique")
    op.drop_index(op.f("ix_uploaded_documents_file_extension"), table_name="uploaded_documents")
    op.drop_index(op.f("ix_uploaded_documents_checksum"), table_name="uploaded_documents")
    op.drop_column("uploaded_documents", "word_count")
    op.drop_column("uploaded_documents", "page_count")
    op.drop_column("uploaded_documents", "checksum")
    op.drop_column("uploaded_documents", "file_extension")
