"""add_status_column_to_briefs

Revision ID: ad192009f9bf
Revises: 7c579caa39aa
Create Date: 2025-04-01 19:47:23.585507

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ad192009f9bf'
down_revision = '7c579caa39aa'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add status column to briefs table with default value 'pending'
    op.add_column('briefs', sa.Column('status', sa.String(), nullable=True, server_default='pending'))
    
    # Set default value for existing rows
    op.execute("UPDATE briefs SET status = 'pending' WHERE status IS NULL")


def downgrade() -> None:
    # Remove status column from briefs table
    op.drop_column('briefs', 'status')
