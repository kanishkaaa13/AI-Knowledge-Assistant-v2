"""phase 3 initial architecture"""

from alembic import op
import sqlalchemy as sa


revision = "20260522_000001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_users")),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)
    op.create_index(op.f("ix_users_name"), "users", ["name"], unique=False)

    op.create_table(
        "conversations",
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("fk_conversations_user_id_users"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_conversations")),
    )
    op.create_index(op.f("ix_conversations_title"), "conversations", ["title"], unique=False)
    op.create_index(op.f("ix_conversations_user_id"), "conversations", ["user_id"], unique=False)
    op.create_index("ix_conversations_user_id_updated_at", "conversations", ["user_id", "updated_at"], unique=False)

    op.create_table(
        "messages",
        sa.Column("conversation_id", sa.String(length=36), nullable=False),
        sa.Column("role", sa.String(length=50), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("sequence_number", sa.Integer(), nullable=False),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(
            ["conversation_id"], ["conversations.id"], name=op.f("fk_messages_conversation_id_conversations"), ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_messages")),
        sa.UniqueConstraint("conversation_id", "sequence_number", name="uq_messages_conversation_sequence"),
    )
    op.create_index(op.f("ix_messages_conversation_id"), "messages", ["conversation_id"], unique=False)
    op.create_index("ix_messages_conversation_id_created_at", "messages", ["conversation_id", "created_at"], unique=False)
    op.create_index(op.f("ix_messages_role"), "messages", ["role"], unique=False)

    op.create_table(
        "uploaded_documents",
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("file_name", sa.String(length=255), nullable=False),
        sa.Column("file_path", sa.String(length=500), nullable=True),
        sa.Column("mime_type", sa.String(length=120), nullable=True),
        sa.Column("file_size", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("extracted_text", sa.Text(), nullable=True),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name=op.f("fk_uploaded_documents_user_id_users"), ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_uploaded_documents")),
    )
    op.create_index(op.f("ix_uploaded_documents_status"), "uploaded_documents", ["status"], unique=False)
    op.create_index(op.f("ix_uploaded_documents_title"), "uploaded_documents", ["title"], unique=False)
    op.create_index(op.f("ix_uploaded_documents_user_id"), "uploaded_documents", ["user_id"], unique=False)
    op.create_index("ix_uploaded_documents_user_id_status", "uploaded_documents", ["user_id", "status"], unique=False)
    op.create_index(
        "ix_uploaded_documents_user_id_updated_at", "uploaded_documents", ["user_id", "updated_at"], unique=False
    )

    op.create_table(
        "document_chunks",
        sa.Column("document_id", sa.String(length=36), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("token_count", sa.Integer(), nullable=True),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(
            ["document_id"], ["uploaded_documents.id"], name=op.f("fk_document_chunks_document_id_uploaded_documents"), ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_document_chunks")),
        sa.UniqueConstraint("document_id", "chunk_index", name="uq_document_chunks_document_chunk_index"),
    )
    op.create_index(op.f("ix_document_chunks_document_id"), "document_chunks", ["document_id"], unique=False)
    op.create_index(
        "ix_document_chunks_document_id_chunk_index", "document_chunks", ["document_id", "chunk_index"], unique=False
    )

    op.create_table(
        "settings",
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("theme", sa.String(length=20), nullable=False),
        sa.Column("preferred_model", sa.String(length=100), nullable=False),
        sa.Column("memory_enabled", sa.Boolean(), nullable=False),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("fk_settings_user_id_users"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_settings")),
    )
    op.create_index(op.f("ix_settings_user_id"), "settings", ["user_id"], unique=True)


def downgrade() -> None:
    op.drop_index(op.f("ix_settings_user_id"), table_name="settings")
    op.drop_table("settings")
    op.drop_index("ix_document_chunks_document_id_chunk_index", table_name="document_chunks")
    op.drop_index(op.f("ix_document_chunks_document_id"), table_name="document_chunks")
    op.drop_table("document_chunks")
    op.drop_index("ix_uploaded_documents_user_id_updated_at", table_name="uploaded_documents")
    op.drop_index("ix_uploaded_documents_user_id_status", table_name="uploaded_documents")
    op.drop_index(op.f("ix_uploaded_documents_user_id"), table_name="uploaded_documents")
    op.drop_index(op.f("ix_uploaded_documents_title"), table_name="uploaded_documents")
    op.drop_index(op.f("ix_uploaded_documents_status"), table_name="uploaded_documents")
    op.drop_table("uploaded_documents")
    op.drop_index(op.f("ix_messages_role"), table_name="messages")
    op.drop_index("ix_messages_conversation_id_created_at", table_name="messages")
    op.drop_index(op.f("ix_messages_conversation_id"), table_name="messages")
    op.drop_table("messages")
    op.drop_index("ix_conversations_user_id_updated_at", table_name="conversations")
    op.drop_index(op.f("ix_conversations_user_id"), table_name="conversations")
    op.drop_index(op.f("ix_conversations_title"), table_name="conversations")
    op.drop_table("conversations")
    op.drop_index(op.f("ix_users_name"), table_name="users")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")
