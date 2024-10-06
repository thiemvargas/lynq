"""Initial migration

Revision ID: 5dbed30ad69a
Revises: 
Create Date: 2024-10-06 06:19:32.761247

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5dbed30ad69a'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('admin', schema=None) as batch_op:
        batch_op.alter_column('password',
               existing_type=sa.VARCHAR(length=120),
               type_=sa.String(length=255),
               existing_nullable=False)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('admin', schema=None) as batch_op:
        batch_op.alter_column('password',
               existing_type=sa.String(length=255),
               type_=sa.VARCHAR(length=120),
               existing_nullable=False)

    # ### end Alembic commands ###
