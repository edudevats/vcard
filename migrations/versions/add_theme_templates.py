"""add theme templates

Revision ID: add_theme_templates
Revises: f7fe1d8c99b0
Create Date: 2025-09-02 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_theme_templates'
down_revision = 'f7fe1d8c99b0'
branch_labels = None
depends_on = None


def upgrade():
    # Production-safe migration for theme template columns
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    
    # Check if theme table exists
    table_names = inspector.get_table_names()
    if 'theme' not in table_names:
        print("Warning: theme table does not exist, skipping migration")
        return
    
    # Get existing columns
    existing_columns = [col['name'] for col in inspector.get_columns('theme')]
    
    # Add new columns to theme table only if they don't exist
    with op.batch_alter_table('theme') as batch_op:
        if 'template_name' not in existing_columns:
            batch_op.add_column(sa.Column('template_name', sa.String(50), nullable=True, default='classic'))
        
        if 'preview_image' not in existing_columns:
            batch_op.add_column(sa.Column('preview_image', sa.String(255), nullable=True))
        
        if 'is_active' not in existing_columns:
            batch_op.add_column(sa.Column('is_active', sa.Boolean(), nullable=True, default=True))
    
    # Update existing themes to have template_name = 'classic' only if column was just added
    if 'template_name' not in existing_columns:
        conn.execute(sa.text("UPDATE theme SET template_name = 'classic' WHERE template_name IS NULL"))
    
    if 'is_active' not in existing_columns:
        conn.execute(sa.text("UPDATE theme SET is_active = 1 WHERE is_active IS NULL"))


def downgrade():
    # Remove the columns
    with op.batch_alter_table('theme') as batch_op:
        batch_op.drop_column('template_name')
        batch_op.drop_column('preview_image')
        batch_op.drop_column('is_active')