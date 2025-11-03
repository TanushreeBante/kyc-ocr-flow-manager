"""create flow_manager and ocr_records tables"""

from alembic import op
import sqlalchemy as sa


# Revision identifiers, used by Alembic.
revision = "Revision_1"
down_revision = "e467e97c2273"
branch_labels = None
depends_on = None


def upgrade():
    # Create ocr_records table
    op.create_table(
        "ocr_records",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("dob", sa.String(), nullable=False),
        sa.Column("image_name", sa.String(), nullable=False),
    )


def downgrade():
    # Drop tables in reverse order
    op.drop_table("ocr_records")
