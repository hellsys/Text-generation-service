"""User schema update

Revision ID: 4818a323e595
Revises: 4eac14f854d0
Create Date: 2025-03-16 00:43:39.530377

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4818a323e595'
down_revision: Union[str, None] = '4eac14f854d0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('age', sa.Integer(), nullable=True))
    op.add_column('users', sa.Column('country', sa.String(), nullable=True))
    op.add_column('users', sa.Column('fullname', sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'fullname')
    op.drop_column('users', 'country')
    op.drop_column('users', 'age')
