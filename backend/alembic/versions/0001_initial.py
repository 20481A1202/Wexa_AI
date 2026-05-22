"""initial schema placeholder

Revision ID: 0001_initial
Revises:
Create Date: 2026-05-22
"""

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # The local demo uses SQLAlchemy create_all on startup. This placeholder
    # marks Alembic as configured for production migration generation.
    pass


def downgrade() -> None:
    pass
