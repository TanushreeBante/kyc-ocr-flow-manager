from fastapi import FastAPI, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import OCRRecord, FlowManager
from schemas import OCRResponse, FlowManagerResponse
from flow_manager import FlowEngine
import easyocr, os, re, uuid, logging
from flow_manager import create_flow
from tasks import upload_task, ocr_task, extract_task, save_task
# ------------------------------------------------------------------
# LOGGING CONFIGURATION
# ------------------------------------------------------------------
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

logging.basicConfig(
    filename=os.path.join(LOG_DIR, "flow_manager.log"),
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("FlowManagerApp")

# ------------------------------------------------------------------
# FASTAPI CONFIG
# ------------------------------------------------------------------
app = FastAPI(title="KYC Flow Manager", version="4.0")

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ------------------------------------------------------------------
# MAIN UPLOAD ENDPOINT
# ------------------------------------------------------------------
@app.post("/upload", response_model=OCRResponse)
async def upload_image(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    Handle OCR-based KYC document upload and automated data extraction workflow.

    This endpoint orchestrates a multi-step OCR flow:
      1. **run_upload** – Validates and saves the uploaded image file.
      2. **run_ocr** – Performs OCR text extraction using EasyOCR.
      3. **run_extract** – Extracts key fields such as Name and Date of Birth.
      4. **run_save** – Persists extracted results into the database.

    The flow dynamically manages task dependencies using `FlowManager` and `FlowEngine`.
    Each task’s success or failure determines whether the next task executes.
    If any task fails, the flow stops gracefully and logs the error.

    Args:
        file (UploadFile): The uploaded image file from the request body.
        db (Session): Active SQLAlchemy database session (injected via dependency).

    Returns:
        OCRResponse: The final OCR extraction result including name, date of birth,
                     image name, and flow reference ID.

    Raises:
        HTTPException(400): If file validation (type or size) fails.
        HTTPException(500): If any task in the OCR flow fails unexpectedly.

    Example:
        curl -X POST "http://localhost:8000/upload" \
             -F "file=@/path/to/id_card.jpg"
    """

    logger.info("🔄 Starting new OCR flow execution.")

    try:
        # 1️⃣ Initialize new flow record
        flow = create_flow(
            db=db,
            flow_name="kyc_ocr_flow",
            start_task="upload_image",
            related_table="ocr_records",
            task_sequence=["upload_image", "perform_ocr", "extract_details", "save_to_db"],
        )

        # 3️⃣ Initialize flow engine
        flow_engine = FlowEngine(db, flow)

        # ---------------- Task Definitions ----------------

         # Step 2: Initialize engine for tracking
        flow_engine = FlowEngine(db, flow)

        # Step 3: Decorate task executions dynamically
        @flow_engine.flow_task("upload_image", description="Task-1 Save uploaded file")
        def run_upload():
            return upload_task(file)

        @flow_engine.flow_task("perform_ocr", description="Task-2 Run EasyOCR")
        def run_ocr(file_path):
            return ocr_task(file_path)

        @flow_engine.flow_task("extract_details", description="Task-3 Extract name & DoB")
        def run_extract(text):
            return extract_task(text)

        @flow_engine.flow_task("save_to_db", description="Task-4 Save record to DB")
        def run_save(name, dob, file_path):
            return save_task(db, flow, name, dob, file_path)
        
        # ---------------- Execute Flow ----------------
        # Step 4: Execute the flow sequentially
        file_path = run_upload()
        text = run_ocr(file_path)
        name, dob = run_extract(text)
        record = run_save(name, dob, file_path)

        logger.info(f"✅ Flow {flow.id} completed successfully.")
        return OCRResponse(
            id=record.id,
            name=record.name,
            dob=record.dob,
            image_name=record.image_name,
            flow_id=flow.id,
        )

    except HTTPException as e:
        # Validation or known FastAPI error
        logger.error(f"⚠️ Flow {flow.id} validation failed: {e.detail}")
        raise HTTPException(status_code=e.status_code, detail={"error": e.detail,"flow_id": flow.id })

    except ValueError as e:
        # Known logical/validation failure
        logger.error(f"❌ Flow {flow.id} failed: {e}")
        raise HTTPException(status_code=400, detail={"error" : str(e), "flow_id": flow.id})

    except Exception as e:
        # Unexpected exception (catch-all)
        logger.exception(f"💥 Unhandled error in Flow {flow.id}: {e}")
        raise HTTPException(status_code=500, detail="Unexpected server error occurred.")

# ------------------------------------------------------------------
# FLOW RETRIEVAL
# ------------------------------------------------------------------
@app.get("/flow/{flow_id}", response_model=FlowManagerResponse)
def get_flow(flow_id: int, db: Session = Depends(get_db)):
    """
    Retrieve a specific OCR flow record by its unique flow ID.

    This endpoint fetches a `FlowManager` record from the database, including
    details such as flow name, status, and associated tasks. It is typically used
    to monitor the progress or result of a previously executed OCR flow.

    Args:
        flow_id (int): The unique identifier of the OCR flow to retrieve.
        db (Session): The active SQLAlchemy session (injected via dependency).

    Returns:
        FlowManagerResponse: A response model containing the flow details, such as
                             flow name, start task, related record, and current status.

    Raises:
        HTTPException(404): If no flow with the given ID exists.

    Example:
        curl -X GET "http://localhost:8000/flow/12"
    """
    flow = db.query(FlowManager).filter(FlowManager.id == flow_id).first()
    if not flow:
        raise HTTPException(status_code=404, detail="Flow not found")
    return flow
