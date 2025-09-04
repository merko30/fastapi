"""make template id nullable in weeks table

Revision ID: 298e1eaec876
Revises: f7ca39cc655d
Create Date: 2025-09-03 14:45:45.658468

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '298e1eaec876'
down_revision: Union[str, Sequence[str], None] = 'f7ca39cc655d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
