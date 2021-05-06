"""add Show.plot_outline

Revision ID: 47cd43ad1031
Revises: 6ab9985c0f18
Create Date: 2021-04-02 17:06:52.146122

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '47cd43ad1031'
down_revision = '6ab9985c0f18'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('show', sa.Column('plot_outline', sa.String(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('show', 'plot_outline')
    # ### end Alembic commands ###
