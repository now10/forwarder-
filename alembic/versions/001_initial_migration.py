"""Initial migration

Revision ID: 001
Revises: 
Create Date: 2024-01-01 00:00:00.000000

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
    # Create all tables
    op.create_table('users',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=True),
        sa.Column('company_name', sa.String(length=255), nullable=True),
        sa.Column('phone', sa.String(length=50), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('is_verified', sa.Boolean(), nullable=True),
        sa.Column('verification_token', sa.String(length=255), nullable=True),
        sa.Column('verification_expires', sa.DateTime(), nullable=True),
        sa.Column('subscription_tier', sa.String(length=50), nullable=True),
        sa.Column('subscription_status', sa.String(length=50), nullable=True),
        sa.Column('subscription_id', sa.String(length=255), nullable=True),
        sa.Column('current_period_end', sa.DateTime(), nullable=True),
        sa.Column('max_sources', sa.Integer(), nullable=True),
        sa.Column('max_destinations', sa.Integer(), nullable=True),
        sa.Column('max_keywords', sa.Integer(), nullable=True),
        sa.Column('monthly_message_limit', sa.Integer(), nullable=True),
        sa.Column('messages_used_this_month', sa.Integer(), nullable=True),
        sa.Column('two_factor_enabled', sa.Boolean(), nullable=True),
        sa.Column('two_factor_secret', sa.String(length=255), nullable=True),
        sa.Column('last_login', sa.DateTime(), nullable=True),
        sa.Column('failed_login_attempts', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('timezone', sa.String(length=50), nullable=True),
        sa.Column('language', sa.String(length=10), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )
    # ... Add all other table creation statements from our schema
    
    # Create indexes
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('message_logs')
    op.drop_table('forwarding_rules')
    op.drop_table('telegram_chats')
    op.drop_table('telegram_accounts')
    op.drop_table('user_profiles')
    op.drop_table('users')