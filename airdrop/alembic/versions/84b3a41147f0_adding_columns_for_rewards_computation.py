"""Adding columns for rewards computation

Revision ID: 84b3a41147f0
Revises: 03431fb8fd1d
Create Date: 2021-12-22 12:44:18.290004

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '84b3a41147f0'
down_revision = '03431fb8fd1d'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('user_rewards_audit',
    sa.Column('row_id', sa.BIGINT(), autoincrement=True, nullable=False),
    sa.Column('row_created', mysql.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
    sa.Column('row_updated', mysql.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'), nullable=False),
    sa.Column('airdrop_id', sa.BIGINT(), nullable=False),
    sa.Column('airdrop_window_id', sa.BIGINT(), nullable=False),
    sa.Column('address', sa.VARCHAR(length=50), nullable=False),
    sa.Column('balance', sa.BIGINT(), nullable=False),
    sa.Column('staked', sa.BIGINT(), nullable=False),
    sa.Column('score', sa.DECIMAL(precision=18, scale=8), nullable=False),
    sa.Column('normalized_score', sa.DECIMAL(precision=18, scale=8), nullable=False),
    sa.Column('rewards_awarded', sa.BIGINT(), nullable=False),
    sa.Column('snapshot_guid', sa.VARCHAR(length=50), nullable=False),
    sa.Column('comment', sa.VARCHAR(length=512), nullable=True),
    sa.ForeignKeyConstraint(['airdrop_id'], ['airdrop.row_id'], ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['airdrop_window_id'], ['airdrop_window.row_id'], ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('row_id'),
    sa.UniqueConstraint('airdrop_window_id', 'address')
    )
    op.create_index(op.f('ix_user_rewards_audit_address'), 'user_rewards_audit', ['address'], unique=False)
    op.add_column('airdrop', sa.Column('rewards_processor', sa.VARCHAR(length=256), nullable=True))
    op.add_column('airdrop_window', sa.Column('last_snapshot_at', mysql.TIMESTAMP(), nullable=True))
    op.add_column('user_balance_snapshot', sa.Column('snapshot_guid', sa.VARCHAR(length=50), nullable=False))
    op.add_column('user_balance_snapshot', sa.Column('staked', sa.BIGINT(), nullable=False))
    op.add_column('user_balance_snapshot', sa.Column('total', sa.BIGINT(), nullable=False))
    op.add_column('user_rewards', sa.Column('normalized_score', sa.DECIMAL(precision=18, scale=8), nullable=False))
    op.add_column('user_rewards', sa.Column('score', sa.DECIMAL(precision=18, scale=8), nullable=False))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('user_rewards', 'score')
    op.drop_column('user_rewards', 'normalized_score')
    op.drop_column('user_balance_snapshot', 'total')
    op.drop_column('user_balance_snapshot', 'staked')
    op.drop_column('user_balance_snapshot', 'snapshot_guid')
    op.drop_column('airdrop_window', 'last_snapshot_at')
    op.drop_column('airdrop', 'rewards_processor')
    op.drop_index(op.f('ix_user_rewards_audit_address'), table_name='user_rewards_audit')
    op.drop_table('user_rewards_audit')
    # ### end Alembic commands ###
