"""

Revision ID: efdc17fbdec4
Revises:
Create Date: 2025-03-20 14:08:57.309860

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "efdc17fbdec4"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "sentiment_score",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("time", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("symbol", sa.String(length=20), nullable=False),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("label", sa.String(), nullable=False),
        sa.Column("source", sa.String(length=20), nullable=False),
        sa.Column("headline", sa.Text(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_symbol", "sentiment_score", ["symbol"], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("idx_symbol", table_name="sentiment_score")
    op.drop_table("sentiment_score")
