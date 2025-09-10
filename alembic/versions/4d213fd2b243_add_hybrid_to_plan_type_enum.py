"""add HYBRID to plan type enum

Revision ID: 4d213fd2b243
Revises: 62a770eaea1c
Create Date: 2025-09-10 15:31:19.499138

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "4d213fd2b243"
down_revision: Union[str, Sequence[str], None] = "62a770eaea1c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE type ADD VALUE IF NOT EXISTS 'HYBRID'")


def downgrade() -> None:
    """Downgrade schema."""
    pass
