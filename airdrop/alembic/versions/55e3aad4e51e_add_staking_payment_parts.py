"""add staking, payment parts

Revision ID: 55e3aad4e51e
Revises: 6d18e55c5d9c
Create Date: 2025-03-26 17:26:24.526911

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '55e3aad4e51e'
down_revision = '6d18e55c5d9c'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('user_balance_snapshot', sa.Column('payment_part', sa.VARCHAR(length=250), nullable=True))
    op.add_column('user_balance_snapshot', sa.Column('staking_part', sa.VARCHAR(length=250), nullable=True))
    op.create_index('payment_part_staking_part_idx', 'user_balance_snapshot', ['payment_part', 'staking_part'], unique=False)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index('payment_part_staking_part_idx', table_name='user_balance_snapshot')
    op.drop_column('user_balance_snapshot', 'staking_part')
    op.drop_column('user_balance_snapshot', 'payment_part')
    # ### end Alembic commands ###
