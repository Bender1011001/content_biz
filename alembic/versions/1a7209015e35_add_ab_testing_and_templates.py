"""add_ab_testing_and_templates

Revision ID: 1a7209015e35
Revises: 15204faa64a0
Create Date: 2025-03-25 17:13:54.662579

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1a7209015e35'
down_revision = '15204faa64a0'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create ab_tests table
    op.create_table('ab_tests',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.String(), nullable=True, server_default='active'),
        sa.Column('start_date', sa.DateTime(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('end_date', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create ab_test_variants table
    op.create_table('ab_test_variants',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('test_id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('model', sa.String(), nullable=False),
        sa.Column('prompt_template', sa.Text(), nullable=True),
        sa.Column('parameters', sa.Text(), nullable=True),
        sa.Column('weight', sa.Float(), nullable=True, server_default='1.0'),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['test_id'], ['ab_tests.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create content_templates table
    op.create_table('content_templates',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('system_prompt', sa.Text(), nullable=False),
        sa.Column('user_prompt_template', sa.Text(), nullable=False),
        sa.Column('content_type', sa.String(), nullable=False),
        sa.Column('industry', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    
    # For SQLite, we need to use batch operations to add foreign key constraints
    # Create a new table with the FK, move data, drop old table, rename new table
    with op.batch_alter_table('content') as batch_op:  # Corrected table name
        batch_op.add_column(sa.Column('variant_id', sa.String(), nullable=True))
        batch_op.create_foreign_key('fk_content_variant', 'ab_test_variants', ['variant_id'], ['id']) # Corrected FK name


def downgrade() -> None:
    # Use batch operations for SQLite to remove the foreign key
    with op.batch_alter_table('content') as batch_op: # Corrected table name
        batch_op.drop_constraint('fk_content_variant', type_='foreignkey') # Corrected FK name
        batch_op.drop_column('variant_id')
    
    # Drop tables in reverse order of creation
    op.drop_table('content_templates')
    op.drop_table('ab_test_variants')
    op.drop_table('ab_tests')
