"""chatbot

Revision ID: 769440fb19e7
Revises: 117a8faedcf4
Create Date: 2026-05-14 23:44:42.364247
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "769440fb19e7"
down_revision = "117a8faedcf4"
branch_labels = None
depends_on = None


def upgrade():
    # Create chat_sessions table
    op.create_table(
        "chat_sessions",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.user_id"],
            ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id")
    )

    # Create chat_messages table
    op.create_table(
        "chat_messages",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("session_id", sa.UUID(), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["session_id"],
            ["chat_sessions.id"],
            ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id")
    )


def downgrade():
    # Drop chat tables only
    op.drop_table("chat_messages")
    op.drop_table("chat_sessions")