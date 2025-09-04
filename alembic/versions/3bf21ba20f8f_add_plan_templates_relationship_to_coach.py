"""add plan templates relationship to coach

Revision ID: 3bf21ba20f8f
Revises: ffb01a54d61a
Create Date: 2025-09-03 13:46:29.940413

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3bf21ba20f8f'
down_revision: Union[str, Sequence[str], None] = 'ffb01a54d61a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
