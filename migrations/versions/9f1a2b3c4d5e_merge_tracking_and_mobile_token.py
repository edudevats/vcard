"""merge appointment tracking and mobile token heads

Revision ID: 9f1a2b3c4d5e
Revises: 20251010_024908, c3d986682e2a
Create Date: 2026-06-08 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9f1a2b3c4d5e'
down_revision = ('20251010_024908', 'c3d986682e2a')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
