"""Initial schema creation

Revision ID: f6a3fb7b293b
Revises: 
Create Date: 2026-06-05 17:40:56.719188

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f6a3fb7b293b'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create initial schema from scratch on a fresh database."""

    # --- Create users table ---
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(length=100), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=True),
        sa.Column('role', sa.String(length=50), server_default=sa.text("'user'"), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('updated_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('username'),
        sa.UniqueConstraint('email'),
    )
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)

    # --- Create categories table ---
    op.create_table(
        'categories',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=150), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('slug', sa.String(length=150), nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('updated_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
        sa.UniqueConstraint('slug'),
    )
    op.create_index(op.f('ix_categories_id'), 'categories', ['id'], unique=False)

    # --- Create items table ---
    op.create_table(
        'items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('sku', sa.String(length=100), nullable=False),
        sa.Column('category_id', sa.Integer(), nullable=False),
        sa.Column('unit_price', sa.Numeric(precision=18, scale=2), nullable=False),
        sa.Column('quantity_in_stock', sa.Integer(), server_default=sa.text('0'), nullable=False),
        sa.Column('reorder_level', sa.Integer(), server_default=sa.text('10'), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('updated_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.ForeignKeyConstraint(['category_id'], ['categories.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('sku'),
    )
    op.create_index(op.f('ix_items_id'), 'items', ['id'], unique=False)

    # --- Create transactions table ---
    op.create_table(
        'transactions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('item_id', sa.Integer(), nullable=False),
        sa.Column('transaction_type', sa.String(length=50), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.Column('reference_number', sa.String(length=100), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('performed_by', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.ForeignKeyConstraint(['item_id'], ['items.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['performed_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_transactions_id'), 'transactions', ['id'], unique=False)

    # --- Create api_keys table ---
    op.create_table(
        'api_keys',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('key_hash', sa.String(length=255), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=True),
        sa.Column('last_used_at', sa.TIMESTAMP(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('expires_at', sa.TIMESTAMP(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('key_hash'),
    )
    op.create_index(op.f('ix_api_keys_id'), 'api_keys', ['id'], unique=False)


def downgrade() -> None:
    """Drop all tables in reverse dependency order."""
    op.drop_index(op.f('ix_api_keys_id'), table_name='api_keys')
    op.drop_table('api_keys')
    op.drop_index(op.f('ix_transactions_id'), table_name='transactions')
    op.drop_table('transactions')
    op.drop_index(op.f('ix_items_id'), table_name='items')
    op.drop_table('items')
    op.drop_index(op.f('ix_categories_id'), table_name='categories')
    op.drop_table('categories')
    op.drop_index(op.f('ix_users_id'), table_name='users')
    op.drop_table('users')
