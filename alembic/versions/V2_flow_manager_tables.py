"""normalize flow tables: flow_manager, flow_tasks, flow_conditions"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "Revision_2"
down_revision = "Revision_1"  # set to previous revision id if you already have one
branch_labels = None
depends_on = None


def upgrade():


    # flow_manager
    op.create_table(
        "flow_manager",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("flow_name", sa.String(), nullable=False),
        sa.Column("start_task", sa.String(), nullable=False),
        sa.Column("related_table", sa.String(), nullable=True),
        sa.Column("related_record_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index("ix_flow_manager_id", "flow_manager", ["id"])

    # flow_tasks
    op.create_table(
        "flow_tasks",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("flow_id", sa.Integer(), sa.ForeignKey("flow_manager.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default="pending"),
        sa.UniqueConstraint("flow_id", "name", name="uq_flowtask_flow_taskname"),
    )
    op.create_index("ix_flow_tasks_id", "flow_tasks", ["id"])
    op.create_index("ix_flow_tasks_flow_id", "flow_tasks", ["flow_id"])

    # flow_conditions
    op.create_table(
        "flow_conditions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("flow_id", sa.Integer(), sa.ForeignKey("flow_manager.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("source_task", sa.String(), nullable=False),
        sa.Column("outcome", sa.String(), nullable=False),
        sa.Column("target_task_success", sa.String(), nullable=True),
        sa.Column("target_task_failure", sa.String(), nullable=True),
        sa.UniqueConstraint("flow_id", "name", name="uq_flowcond_flow_name"),
    )
    op.create_index("ix_flow_conditions_id", "flow_conditions", ["id"])
    op.create_index("ix_flow_conditions_flow_id", "flow_conditions", ["flow_id"])
    op.create_index("ix_flow_conditions_flow_source", "flow_conditions", ["flow_id", "source_task"])


def downgrade():
    op.drop_table("flow_conditions")
    op.drop_table("flow_tasks")

    op.drop_table("flow_manager")


 

 