"""merge migration heads

Revision ID: 3d1ebd622a5c
Revises: 69615aa09fb0, 996680f9a118
Create Date: 2026-05-20 16:59:10.843456

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3d1ebd622a5c'
down_revision: Union[str, Sequence[str], None] = ('69615aa09fb0', '996680f9a118')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
