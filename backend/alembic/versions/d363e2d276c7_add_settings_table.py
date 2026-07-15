"""add settings table

Revision ID: d363e2d276c7
Revises: 2b0255843e6f
Create Date: 2026-07-14 15:09:31.857774

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd363e2d276c7'
down_revision: Union[str, Sequence[str], None] = '2b0255843e6f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:

    op.create_table(

        "settings",
        sa.Column("id", sa.UUID(), nullable=False),

        sa.Column("company_email", sa.String(), nullable=True),
        sa.Column("company_phone", sa.String(), nullable=True),
        sa.Column("company_logo_url", sa.String(), nullable=True),
        sa.Column("rfq_email_template", sa.Text(), nullable=True),
        sa.Column("technical_offer_template", sa.Text(), nullable=True),
        sa.Column("commercial_offer_template", sa.Text(), nullable=True),
        sa.Column("po_template", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS settings")
