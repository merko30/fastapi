"""add roles column to users"""

from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = "a09d716627e9"
down_revision = "ffb01a54d61a"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "roles",
            sa.dialects.postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
    )


def downgrade() -> None:
    op.drop_column("users", "roles")
