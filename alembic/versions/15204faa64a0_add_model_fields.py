"""add_model_fields

Revision ID: 15204faa64a0
Revises: 
Create Date: 2025-03-25 17:11:27.705314

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '15204faa64a0'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create briefs table first
    op.create_table('briefs',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('topic', sa.String(), nullable=True),
        sa.Column('tone', sa.String(), nullable=True),
        sa.Column('target_audience', sa.String(), nullable=True),
        sa.Column('word_count', sa.Integer(), nullable=True),
        sa.Column('brief_text', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id')
    )
    # Create content table next
    op.create_table('content',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('brief_id', sa.String(), nullable=True), # Assuming FK to briefs is needed
        sa.Column('generated_text', sa.Text(), nullable=True),
        sa.Column('quality_score', sa.Float(), nullable=True),
        sa.Column('delivery_status', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id')
        # Note: FK to briefs might need op.create_foreign_key if briefs table exists
    )
    # Add columns to briefs
    op.add_column('briefs', sa.Column('industry', sa.String(), nullable=True))
    op.add_column('briefs', sa.Column('content_type', sa.String(), nullable=True))
    
    # Set default values for existing rows
    op.execute("UPDATE briefs SET industry = 'general' WHERE industry IS NULL")
    op.execute("UPDATE briefs SET content_type = 'blog' WHERE content_type IS NULL")

    # Add columns to content
    op.add_column('content', sa.Column('model_used', sa.String(), nullable=True)) # Corrected table name
    op.add_column('content', sa.Column('generation_metadata', sa.Text(), nullable=True)) # Corrected table name


def downgrade() -> None:
    # Remove columns from content first (reverse of add_column)
    op.drop_column('content', 'generation_metadata') # Corrected table name
    op.drop_column('content', 'model_used') # Corrected table name

    # Remove columns from briefs
    op.drop_column('briefs', 'content_type')
    op.drop_column('briefs', 'industry')

    # Drop content table
    op.drop_table('content')
    # Drop briefs table last
    op.drop_table('briefs')
