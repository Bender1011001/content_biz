"""add_clients_and_payments_tables

Revision ID: 7c579caa39aa
Revises: 8d5b7f72dacb
Create Date: 2025-04-01 19:42:29.513654

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7c579caa39aa'
down_revision = '8d5b7f72dacb'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create clients table
    op.create_table('clients',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('stripe_customer_id', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )
    
    # Create payments table
    op.create_table('payments',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('client_id', sa.String(), nullable=False),
        sa.Column('brief_id', sa.String(), nullable=False),
        sa.Column('amount', sa.Float(), nullable=True, server_default='75.00'),
        sa.Column('status', sa.String(), nullable=True, server_default='pending'),
        sa.Column('stripe_payment_id', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['client_id'], ['clients.id'], ),
        sa.ForeignKeyConstraint(['brief_id'], ['briefs.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Add client_id column to briefs table and create foreign key
    op.add_column('briefs', sa.Column('client_id', sa.String(), nullable=True))
    op.create_foreign_key('fk_briefs_client', 'briefs', 'clients', ['client_id'], ['id'])


def downgrade() -> None:
    # Drop foreign key from briefs table
    op.drop_constraint('fk_briefs_client', 'briefs', type_='foreignkey')
    op.drop_column('briefs', 'client_id')
    
    # Drop payments table
    op.drop_table('payments')
    
    # Drop clients table
    op.drop_table('clients')
