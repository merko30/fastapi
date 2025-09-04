"""fix-relationship

Revision ID: f7ca39cc655d
Revises: a237775568b7
Create Date: 2025-09-03 13:54:42.679391

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f7ca39cc655d'
down_revision: Union[str, Sequence[str], None] = 'a237775568b7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
