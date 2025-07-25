"""Create backup_jobs table

Revision ID: 444443b7611c
Revises: f0470f2ad38b
Create Date: 2025-07-20 08:48:56.661702

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '444443b7611c'
down_revision: Union[str, Sequence[str], None] = 'f0470f2ad38b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('backup_jobs',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('job_id', sa.Integer(), nullable=True),
    sa.Column('tenant_id', sa.Integer(), nullable=True),
    sa.Column('status', sa.String(), nullable=True),
    sa.Column('start_time', sa.DateTime(), nullable=True),
    sa.Column('end_time', sa.DateTime(), nullable=True),
    sa.Column('subclient', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_backup_jobs_id'), 'backup_jobs', ['id'], unique=False)
    op.create_index(op.f('ix_backup_jobs_job_id'), 'backup_jobs', ['job_id'], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_backup_jobs_job_id'), table_name='backup_jobs')
    op.drop_index(op.f('ix_backup_jobs_id'), table_name='backup_jobs')
    op.drop_table('backup_jobs')
    # ### end Alembic commands ###
