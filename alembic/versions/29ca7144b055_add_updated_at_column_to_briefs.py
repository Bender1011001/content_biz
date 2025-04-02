"""add_updated_at_column_to_briefs

Revision ID: 29ca7144b055
Revises: ad192009f9bf
Create Date: 2025-04-01 19:49:39.906014

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '29ca7144b055'
down_revision = 'ad192009f9bf'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add updated_at column to briefs table with default value of current timestamp
    op.add_column('briefs', sa.Column('updated_at', sa.DateTime(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')))
    
    # Set default value for existing rows
    op.execute("UPDATE briefs SET updated_at = created_at WHERE updated_at IS NULL")


def downgrade() -> None:
    # Remove updated_at column from briefs table
    op.drop_column('briefs', 'updated_at')
