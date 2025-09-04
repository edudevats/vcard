"""Merge all migration heads for new database setup

Revision ID: 36995f706428
Revises: 47ff92202e31, 84cb581ef2df, add_theme_templates
Create Date: 2025-09-02 19:57:45.946018

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '36995f706428'
down_revision = ('47ff92202e31', '84cb581ef2df')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
