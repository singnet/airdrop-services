"""Add signed data column.

Revision ID: 384051a9013e
Revises: 72366f6844ea
Create Date: 2022-06-16 15:56:49.362355

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '384051a9013e'
down_revision = '72366f6844ea'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('user_registrations', sa.Column('signed_data', sa.JSON(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('user_registrations', 'signed_data')
    # ### end Alembic commands ###
