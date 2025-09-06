"""add order field, plan template type

Revision ID: 62a770eaea1c
Revises: a09d716627e9
Create Date: 2025-09-06 17:30:58.048813

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "62a770eaea1c"
down_revision: Union[str, Sequence[str], None] = "a09d716627e9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add order columns
    op.add_column("days", sa.Column("order", sa.Integer(), nullable=False))
    op.add_column("weeks", sa.Column("order", sa.Integer(), nullable=False))
    op.alter_column("weeks", "template_id", existing_type=sa.INTEGER(), nullable=True)
    op.add_column("workouts", sa.Column("order", sa.Integer(), nullable=False))
    op.add_column("workout_sets", sa.Column("order", sa.Integer(), nullable=False))
    op.add_column("workout_sets", sa.Column("name", sa.String(), nullable=False))
    op.add_column("workout_sets", sa.Column("description", sa.String(), nullable=True))

    # Add new enum type for plan/workout kind
    plan_type_enum = sa.Enum("RUN", "BIKE", "STRENGTH", "HYBRID", name="type")
    plan_type_enum.create(op.get_bind(), checkfirst=True)

    op.add_column(
        "plan_templates",
        sa.Column("type", plan_type_enum, nullable=False),
    )
    op.add_column(
        "plans",
        sa.Column("type", plan_type_enum, nullable=False),
    )

    # Update level enum (rename plan_level → level)
    new_level_enum = sa.Enum("BEGINNER", "INTERMEDIATE", "ADVANCED", name="level")
    old_level_enum = postgresql.ENUM(
        "BEGINNER", "INTERMEDIATE", "ADVANCED", name="plan_level"
    )

    # make sure new enum exists
    new_level_enum.create(op.get_bind(), checkfirst=True)

    op.alter_column(
        "plan_templates",
        "level",
        existing_type=old_level_enum,
        type_=new_level_enum,
        existing_nullable=False,
        postgresql_using="level::text::level",
    )
    op.alter_column(
        "plans",
        "level",
        existing_type=old_level_enum,
        type_=new_level_enum,
        existing_nullable=False,
        postgresql_using="level::text::level",
    )

    # drop old enum type
    old_level_enum.drop(op.get_bind(), checkfirst=True)


def downgrade() -> None:
    """Downgrade schema."""
    # recreate old enum type
    old_level_enum = postgresql.ENUM(
        "BEGINNER", "INTERMEDIATE", "ADVANCED", name="plan_level"
    )
    old_level_enum.create(op.get_bind(), checkfirst=True)

    # downgrade level enums
    op.alter_column(
        "plans",
        "level",
        existing_type=sa.Enum("BEGINNER", "INTERMEDIATE", "ADVANCED", name="level"),
        type_=old_level_enum,
        existing_nullable=False,
        postgresql_using="level::text::plan_level",
    )
    op.alter_column(
        "plan_templates",
        "level",
        existing_type=sa.Enum("BEGINNER", "INTERMEDIATE", "ADVANCED", name="level"),
        type_=old_level_enum,
        existing_nullable=False,
        postgresql_using="level::text::plan_level",
    )

    # drop new level enum
    sa.Enum("BEGINNER", "INTERMEDIATE", "ADVANCED", name="level").drop(
        op.get_bind(), checkfirst=True
    )

    # drop type column and enum
    op.drop_column("plans", "type")
    op.drop_column("plan_templates", "type")
    sa.Enum("RUN", "BIKE", "STRENGTH", "HYBRID", name="type").drop(
        op.get_bind(), checkfirst=True
    )

    # drop added columns
    op.drop_column("workout_sets", "description")
    op.drop_column("workout_sets", "name")
    op.drop_column("workout_sets", "order")
    op.drop_column("workouts", "order")
    op.alter_column("weeks", "template_id", existing_type=sa.INTEGER(), nullable=False)
    op.drop_column("weeks", "order")
    op.drop_column("days", "order")
