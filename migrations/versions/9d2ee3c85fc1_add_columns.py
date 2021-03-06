"""add columns

Revision ID: 9d2ee3c85fc1
Revises: 8f14acc8a818
Create Date: 2021-03-26 10:14:32.400796

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9d2ee3c85fc1'
down_revision = '8f14acc8a818'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('show', sa.Column('no_imdb', sa.Boolean(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('show', 'no_imdb')
    # ### end Alembic commands ###
