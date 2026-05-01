"""add patient consent

Revision ID: 77bd625daafb
Revises: 70766895f53e
Create Date: 2026-05-01 03:26:18.403555

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '77bd625daafb'
down_revision = '70766895f53e'
branch_labels = None
depends_on = None


from alembic import op
import sqlalchemy as sa

def upgrade():
    # 1. Add column as nullable first
    op.add_column(
        'patients',
        sa.Column('app_consent', sa.Boolean(), nullable=True)
    )

    # 2. Set existing patients to TRUE
    op.execute(
        "UPDATE patients SET app_consent = TRUE"
    )

    # 3. Enforce NOT NULL
    op.alter_column(
        'patients',
        'app_consent',
        nullable=False
    )


def downgrade():
    op.drop_column('patients', 'app_consent')


