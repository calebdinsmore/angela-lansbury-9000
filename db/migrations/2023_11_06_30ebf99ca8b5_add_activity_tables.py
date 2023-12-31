"""add activity tables

Revision ID: 30ebf99ca8b5
Revises: 5a838b753ec1
Create Date: 2023-11-06 13:49:18.953975

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '30ebf99ca8b5'
down_revision: Union[str, None] = '5a838b753ec1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('activity_module_settings',
    sa.Column('guild_id', sa.Integer(), nullable=False),
    sa.Column('excluded_channels', sa.String(), nullable=True),
    sa.Column('inactive_role_id', sa.Integer(), nullable=True),
    sa.Column('break_role_id', sa.Integer(), nullable=True),
    sa.Column('log_channel', sa.Integer(), nullable=True),
    sa.PrimaryKeyConstraint('guild_id')
    )
    op.create_table('rolling_message_log',
    sa.Column('message_id', sa.Integer(), nullable=False),
    sa.Column('guild_id', sa.Integer(), nullable=False),
    sa.Column('author_id', sa.Integer(), nullable=False),
    sa.Column('sent_at', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('message_id')
    )
    op.create_index(op.f('ix_rolling_message_log_author_id'), 'rolling_message_log', ['author_id'], unique=False)
    op.create_index(op.f('ix_rolling_message_log_guild_id'), 'rolling_message_log', ['guild_id'], unique=False)
    op.create_table('user_activity',
    sa.Column('guild_id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('tracking_started_on', sa.DateTime(), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('sent_thirty_day_notice', sa.Boolean(), nullable=False),
    sa.Column('sent_sixty_day_notice', sa.Boolean(), nullable=False),
    sa.PrimaryKeyConstraint('guild_id', 'user_id')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('user_activity')
    op.drop_index(op.f('ix_rolling_message_log_guild_id'), table_name='rolling_message_log')
    op.drop_index(op.f('ix_rolling_message_log_author_id'), table_name='rolling_message_log')
    op.drop_table('rolling_message_log')
    op.drop_table('activity_module_settings')
    # ### end Alembic commands ###
