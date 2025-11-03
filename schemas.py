from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


# ---------------------------------------------------------------------
# OCR RECORD RESPONSE SCHEMA
# ---------------------------------------------------------------------
class OCRResponse(BaseModel):
    id: int
    name: str
    dob: str
    image_name: str
    flow_id: Optional[int] = None  
    class Config:
        from_attributes = True  


# ---------------------------------------------------------------------
# FLOW TASK SCHEMA
# ---------------------------------------------------------------------
class FlowTaskResponse(BaseModel):
    id: int
    flow_id: int
    name: str
    description: Optional[str]
    status: str
    

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------
# FLOW CONDITION SCHEMA
# ---------------------------------------------------------------------
class FlowConditionResponse(BaseModel):
    id: int
    flow_id: int
    name: str
    description: str
    source_task: str
    outcome: str
    target_task_success: Optional[str]
    target_task_failure: Optional[str]

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------
# FLOW MANAGER SCHEMA (MAIN FLOW)
# ---------------------------------------------------------------------
class FlowManagerResponse(BaseModel):
    id: int
    flow_name: str
    start_task: str
    related_table: Optional[str] = None
    related_record_id: Optional[int] = None

    # Relationships
    tasks: List[FlowTaskResponse] = []
    conditions: List[FlowConditionResponse] = []

    class Config:
        from_attributes = True
