"""add original_anchor_message column

Revision ID: cc5e559df3ad
Revises: 
Create Date: 2023-09-28 10:35:18.700833

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'cc5e559df3ad'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('auto_delete_channel_config', sa.Column('original_anchor_message', sa.Integer(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('auto_delete_channel_config', 'original_anchor_message')
    # ### end Alembic commands ###
