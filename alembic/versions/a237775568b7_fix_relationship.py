"""fix-relationship

Revision ID: a237775568b7
Revises: c61f7caf97ab
Create Date: 2025-09-03 13:52:41.605214

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a237775568b7'
down_revision: Union[str, Sequence[str], None] = 'c61f7caf97ab'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
