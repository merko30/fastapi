"""add template relationship to plans

Revision ID: c61f7caf97ab
Revises: 3bf21ba20f8f
Create Date: 2025-09-03 13:51:18.757120

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c61f7caf97ab'
down_revision: Union[str, Sequence[str], None] = '3bf21ba20f8f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
