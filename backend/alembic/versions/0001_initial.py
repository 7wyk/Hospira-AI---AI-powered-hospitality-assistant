from alembic import op
import sqlalchemy as sa

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.create_table("profiles", sa.Column("id", sa.String(128), primary_key=True), sa.Column("full_name", sa.String(200)), sa.Column("created_at", sa.DateTime(timezone=True)), sa.Column("updated_at", sa.DateTime(timezone=True)))
    op.create_table("conversations", sa.Column("id", sa.String(36), primary_key=True), sa.Column("user_id", sa.String(128), nullable=False), sa.Column("title", sa.String(200), nullable=False), sa.Column("summary", sa.Text()), sa.Column("active_room_id", sa.String(80)), sa.Column("active_intent", sa.String(80)), sa.Column("context_json", sa.JSON()), sa.Column("created_at", sa.DateTime(timezone=True)), sa.Column("updated_at", sa.DateTime(timezone=True)), sa.Column("last_message_at", sa.DateTime(timezone=True)))
    op.create_index("ix_conversations_user_updated", "conversations", ["user_id", "updated_at"])
    op.create_table("messages", sa.Column("id", sa.String(36), primary_key=True), sa.Column("conversation_id", sa.String(36), sa.ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False), sa.Column("user_id", sa.String(128), nullable=False), sa.Column("role", sa.String(20), nullable=False), sa.Column("content", sa.Text(), nullable=False), sa.Column("metadata_json", sa.JSON()), sa.Column("created_at", sa.DateTime(timezone=True)))
    op.create_index("ix_messages_conversation_id", "messages", ["conversation_id"])
    op.create_table("memories", sa.Column("id", sa.String(36), primary_key=True), sa.Column("user_id", sa.String(128), nullable=False), sa.Column("memory_type", sa.String(80), nullable=False), sa.Column("key", sa.String(120), nullable=False), sa.Column("value_json", sa.JSON(), nullable=False), sa.Column("source_conversation_id", sa.String(36)), sa.Column("confidence", sa.Float()), sa.Column("last_referenced_at", sa.DateTime(timezone=True)), sa.Column("created_at", sa.DateTime(timezone=True)), sa.Column("updated_at", sa.DateTime(timezone=True)), sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()))
    op.create_index("ix_memories_user_active", "memories", ["user_id", "is_active"])

def downgrade():
    op.drop_index("ix_memories_user_active", table_name="memories"); op.drop_table("memories")
    op.drop_index("ix_messages_conversation_id", table_name="messages"); op.drop_table("messages")
    op.drop_index("ix_conversations_user_updated", table_name="conversations"); op.drop_table("conversations")
    op.drop_table("profiles")
