"""add ab test metrics

Revision ID: 8d5b7f72dacb
Revises: 1a7209015e35
Create Date: 2025-03-26 16:32:53.473117

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8d5b7f72dacb'
down_revision = '1a7209015e35'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('content', sa.Column('generation_time', sa.Float(), nullable=True))
    # Set server_default to true() and nullable=False for needs_review
    op.add_column('content', sa.Column('needs_review', sa.Boolean(), server_default=sa.true(), nullable=False))


def downgrade():
    op.drop_column('content', 'needs_review')
    op.drop_column('content', 'generation_time')
