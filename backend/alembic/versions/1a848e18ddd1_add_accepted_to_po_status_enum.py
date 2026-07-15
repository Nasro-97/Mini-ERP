"""add accepted to po status enum

Revision ID: 1a848e18ddd1
Revises: d363e2d276c7
Create Date: 2026-07-15 19:31:20.140472

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1a848e18ddd1'
down_revision: Union[str, Sequence[str], None] = 'd363e2d276c7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE postatus ADD VALUE IF NOT EXISTS 'ACCEPTED'")

def downgrade() -> None:
    pass
