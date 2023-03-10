"""add socks_dns_port

Revision ID: 2910ee00d182
Revises: 2b221e84eb82
Create Date: 2019-07-29 12:55:56.462144

"""

# Revision identifiers, used by Alembic.
from __future__ import absolute_import
revision = '2910ee00d182'
down_revision = '2b221e84eb82'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('socks5s', sa.Column("dnsport", sa.Integer, nullable=True))


def downgrade():
    op.drop_column('socks5s', "dnsport")
