"""Fix plan level enum

Revision ID: 3210c31a74b9
Revises: 5908a95468ae
Create Date: 2025-08-17 14:23:25.684589

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "3210c31a74b9"
down_revision: Union[str, Sequence[str], None] = "5908a95468ae"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # create new enum type
    plan_level_enum = postgresql.ENUM(
        "beginner", "intermediate", "advanced", name="level"
    )
    plan_level_enum.create(op.get_bind(), checkfirst=True)

    # alter column using explicit cast
    op.execute(
        "ALTER TABLE plans ALTER COLUMN level TYPE level USING level::text::level"
    )


def downgrade():
    # revert column to old enum type
    op.execute(
        "ALTER TABLE plans ALTER COLUMN level TYPE workout_type USING level::text::workout_type"
    )

    # drop the new enum
    plan_level_enum = postgresql.ENUM(
        "beginner", "intermediate", "advanced", name="level"
    )
    plan_level_enum.drop(op.get_bind(), checkfirst=True)
