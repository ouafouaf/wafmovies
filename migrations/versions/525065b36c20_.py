"""empty message

Revision ID: 525065b36c20
Revises: 
Create Date: 2021-03-14 09:06:35.387724

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '525065b36c20'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('people',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(), nullable=True),
    sa.Column('imdb_id', sa.Integer(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('show',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('title', sa.String(), nullable=True),
    sa.Column('year', sa.Integer(), nullable=True),
    sa.Column('imdb_id', sa.Integer(), nullable=True),
    sa.Column('imdb_rating', sa.Float(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('storage',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('release',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('show_id', sa.Integer(), nullable=True),
    sa.Column('filename', sa.String(), nullable=True),
    sa.Column('dirname', sa.String(), nullable=True),
    sa.Column('size', sa.Float(), nullable=True),
    sa.Column('duration', sa.Float(), nullable=True),
    sa.Column('bitrate', sa.Float(), nullable=True),
    sa.Column('width', sa.Float(), nullable=True),
    sa.Column('height', sa.Float(), nullable=True),
    sa.Column('unique_id', sa.String(), nullable=True),
    sa.Column('storage_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['show_id'], ['show.id'], ),
    sa.ForeignKeyConstraint(['storage_id'], ['storage.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('show_cast',
    sa.Column('people_id', sa.Integer(), nullable=False),
    sa.Column('show_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['people_id'], ['people.id'], ),
    sa.ForeignKeyConstraint(['show_id'], ['show.id'], ),
    sa.PrimaryKeyConstraint('people_id', 'show_id')
    )
    op.create_table('show_dir',
    sa.Column('people_id', sa.Integer(), nullable=False),
    sa.Column('show_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['people_id'], ['people.id'], ),
    sa.ForeignKeyConstraint(['show_id'], ['show.id'], ),
    sa.PrimaryKeyConstraint('people_id', 'show_id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('show_dir')
    op.drop_table('show_cast')
    op.drop_table('release')
    op.drop_table('storage')
    op.drop_table('show')
    op.drop_table('people')
    # ### end Alembic commands ###