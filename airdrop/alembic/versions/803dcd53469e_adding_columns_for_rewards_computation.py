"""Adding columns for rewards computation

Revision ID: 803dcd53469e
Revises: 6ca95583c82b
Create Date: 2021-12-22 10:34:24.552575

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '803dcd53469e'
down_revision = '6ca95583c82b'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('user_rewards', sa.Column('log10_score', sa.DECIMAL(precision=10, scale=8), nullable=False))
    op.add_column('user_rewards_audit', sa.Column('log10_score', sa.DECIMAL(precision=10, scale=8), nullable=False))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('user_rewards_audit', 'log10_score')
    op.drop_column('user_rewards', 'log10_score')
    # ### end Alembic commands ###