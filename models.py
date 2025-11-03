from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    ForeignKey,
    Enum as SAEnum,
    UniqueConstraint,
    Index,
)
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime
from database import Base
from enum import Enum


# class TaskStatusEnum(str, Enum):
#     PENDING = "pending"
#     SUCCESS = "success"
#     FAILED = "failed"

class OCRRecord(Base):
    __tablename__ = "ocr_records"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    dob = Column(String, nullable=False)
    image_name = Column(String, nullable=False)


class FlowManager(Base):
    __tablename__ = "flow_manager"

    id = Column(Integer, primary_key=True, index=True)
    flow_name = Column(String, nullable=False)          # e.g. "kyc_ocr_flow"
    start_task = Column(String, nullable=False)         # e.g. "upload_image"

    # generic linkage to any produced record (ocr, payroll, etc.)
    related_table = Column(String, nullable=True)
    related_record_id = Column(Integer, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # relationships
    tasks = relationship(
        "FlowTask",
        back_populates="flow",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    conditions = relationship(
        "FlowCondition",
        back_populates="flow",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def __repr__(self):
        return f"<FlowManager(id={self.id}, name={self.flow_name})>"


class FlowTask(Base):
    __tablename__ = "flow_tasks"

    id = Column(Integer, primary_key=True, index=True)
    flow_id = Column(
        Integer,
        ForeignKey("flow_manager.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name = Column(String, nullable=False)               # e.g. "upload_image"
    description = Column(Text, nullable=True)
    status = Column(String, default="pending", nullable=False)

    flow = relationship("FlowManager", back_populates="tasks")

    __table_args__ = (
        UniqueConstraint("flow_id", "name", name="uq_flowtask_flow_taskname"),
        Index("ix_flow_tasks_flow_pos", "flow_id"),
    )

    def __repr__(self):
        return f"<FlowTask(flow_id={self.flow_id}, name={self.name}, status={self.status})>"


class FlowCondition(Base):
    __tablename__ = "flow_conditions"

    id = Column(Integer, primary_key=True, index=True)
    flow_id = Column(
        Integer,
        ForeignKey("flow_manager.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name = Column(String, nullable=False)             
    description = Column(Text, nullable=True)
    source_task = Column(String, nullable=False)         # e.g. "upload_image"
    outcome = Column(String, nullable=False)             # e.g. "success"
    target_task_success = Column(String, nullable=True)  # e.g. "perform_ocr"
    target_task_failure = Column(String, nullable=True)  # e.g. "end"

    flow = relationship("FlowManager", back_populates="conditions")

    __table_args__ = (
        UniqueConstraint("flow_id", "name", name="uq_flowcond_flow_name"),
        Index("ix_flow_conditions_flow_source", "flow_id", "source_task"),
    )

    def __repr__(self):
        return f"<FlowCondition(flow_id={self.flow_id}, src={self.source_task}, outcome={self.outcome})>"
