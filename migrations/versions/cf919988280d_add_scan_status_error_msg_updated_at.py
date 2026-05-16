"""add scan status error_msg updated_at

Revision ID: cf919988280d
Revises: 769440fb19e7
Create Date: 2026-05-16 06:00:05.814711

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'cf919988280d'
down_revision = '769440fb19e7'
branch_labels = None
depends_on = None


def upgrade():
    # 1. Create the PostgreSQL ENUM type first
    op.execute("CREATE TYPE scanstatus AS ENUM ('pending', 'processing', 'completed', 'failed')")
 
    # 2. Now add the columns (copy any other ADD COLUMN lines alembic generated here too)
    with op.batch_alter_table('mri_scans', schema=None) as batch_op:
        batch_op.add_column(sa.Column('status', sa.Enum('pending', 'processing', 'completed', 'failed', name='scanstatus'), nullable=False, server_default='pending'))
        batch_op.add_column(sa.Column('error_msg', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')))
 
    # 3. Remove server defaults (they were only needed for the backfill)
    with op.batch_alter_table('mri_scans', schema=None) as batch_op:
        batch_op.alter_column('status', server_default=None)
        batch_op.alter_column('updated_at', server_default=None)
    # ### end Alembic commands ###


def downgrade():
    with op.batch_alter_table('mri_scans', schema=None) as batch_op:
        batch_op.drop_column('updated_at')
        batch_op.drop_column('error_msg')
        batch_op.drop_column('status')
 
    # Drop the ENUM type after the column is gone
    op.execute("DROP TYPE scanstatus")