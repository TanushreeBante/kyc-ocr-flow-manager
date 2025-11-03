# flow_manager.py
import logging
from datetime import datetime
from functools import wraps
from sqlalchemy.orm import Session

from models import FlowTask, FlowManager, FlowCondition

logger = logging.getLogger("FlowManagerEngine")


# ---------------------------------------------------------------------
# FLOW CREATION UTILITY
# ---------------------------------------------------------------------
def create_flow(db: Session, flow_name: str, start_task: str, related_table: str, task_sequence: list[str]) -> FlowManager:
    """
    Create a new flow record and its associated flow conditions.

    This function initializes a `FlowManager` entry in the database and automatically
    generates a series of `FlowCondition` records linking each task to the next one.
    It can be reused for different flows (OCR, KYC, etc.) by changing the inputs.

    Args:
        db (Session): SQLAlchemy session.
        flow_name (str): Name of the flow (e.g., 'kyc_ocr_flow').
        start_task (str): The first task in the flow.
        related_table (str): The database table related to this flow.
        task_sequence (list[str]): Ordered list of task names in the flow.

    Returns:
        FlowManager: The created FlowManager instance with conditions attached.

    Example:
        >>> create_flow(
        ...     db,
        ...     flow_name="kyc_ocr_flow",
        ...     start_task="upload_image",
        ...     related_table="ocr_records",
        ...     task_sequence=["upload_image", "perform_ocr", "extract_details", "save_to_db"]
        ... )
    """
    try:
        # Create main flow entry
        flow = FlowManager(
            flow_name=flow_name,
            start_task=start_task,
            related_table=related_table,
        )
        db.add(flow)
        db.commit()
        db.refresh(flow)

        # Create flow conditions dynamically
        for i in range(len(task_sequence) - 1):
            src, target = task_sequence[i], task_sequence[i + 1]
            db.add(
                FlowCondition(
                    flow_id=flow.id,
                    name=f"condition_{src}_result",
                    description=(
                        f"If Task-{i+1} ({src}) succeeds, go to Task-{i+2} ({target}); "
                        f"else, stop the flow."
                    ),
                    source_task=src,
                    outcome="success",
                    target_task_success=target,
                    target_task_failure="end",
                )
            )
        db.commit()

        logger.info(f"✅ Flow '{flow_name}' (ID: {flow.id}) created with {len(task_sequence)} tasks.")
        return flow

    except Exception as e:
        db.rollback()
        logger.error(f"❌ Failed to create flow '{flow_name}': {e}")
        raise



class FlowEngine:
    """Manages task execution and updates normalized flow/task tables."""

    def __init__(self, db, flow_obj):
        self.db = db
        self.flow = flow_obj

    def flow_task(self, name: str, description: str = None):
        """Decorator to wrap each task with DB tracking (create row when task starts)."""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                logger.info(f"▶️ Starting task '{name}' (Flow {self.flow.id})")

                # Create the task row IF it doesn't exist yet
                task = self.db.query(FlowTask).filter_by(flow_id=self.flow.id, name=name).first()
                if not task:
                    task = FlowTask(
                        flow_id=self.flow.id,
                        name=name,
                        description=description or f"Execute {name}",
                        status="running",                        
                    )
                    self.db.add(task)
                else:
                    task.status = "running"

                self.db.commit()

                try:
                    result = func(*args, **kwargs)
                    task.status = "success"
                    task.end_time = datetime.utcnow()
                    self.db.commit()
                    logger.info(f"✅ Task '{name}' succeeded.")
                    return result
                except Exception as e:
                    task.status = "failed"
                    task.error_message = str(e)
                    task.end_time = datetime.utcnow()
                    self.db.commit()
                    logger.error(f"❌ Task '{name}' failed: {e}")
                    raise
            return wrapper
        return decorator
