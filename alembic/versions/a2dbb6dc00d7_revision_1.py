"""Revision_1

Revision ID: a2dbb6dc00d7
Revises: Revision_2
Create Date: 2025-11-02 13:55:38.661972

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a2dbb6dc00d7'
down_revision: Union[str, Sequence[str], None] = 'Revision_2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
