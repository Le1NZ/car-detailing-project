"""Create users table

Revision ID: 001
Revises:
Create Date: 2025-11-15 12:00:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Create users table with all required fields.
    """
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=False),
        sa.Column('phone_number', sa.String(length=20), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
        sa.UniqueConstraint('phone_number')
    )

    # Create indexes for better query performance
    op.create_index('ix_users_email', 'users', ['email'])
    op.create_index('ix_users_phone_number', 'users', ['phone_number'])


def downgrade() -> None:
    """
    Drop users table and its indexes.
    """
    op.drop_index('ix_users_phone_number', table_name='users')
    op.drop_index('ix_users_email', table_name='users')
    op.drop_table('users')
