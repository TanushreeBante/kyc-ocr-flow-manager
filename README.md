# 🧠 KYC OCR Flow Manager

A FastAPI-based application that automates the OCR (Optical Character Recognition) workflow for KYC (Know Your Customer) document processing.  
It performs image uploads, OCR text extraction using EasyOCR, field parsing (Name & Date of Birth), and saves results to a PostgreSQL database — all managed through a dynamic flow engine.

---

## 🚀 Features

- 📤 Upload and validate KYC document images (Sample Images for upload are in Sample_Image Folder)
- 🔍 Perform OCR extraction using **EasyOCR**
- 🧩 Extract key fields — Name and Date of Birth — from text
- 🗄️ Persist extracted data in a PostgreSQL database
- 🔁 Flow-based task management with success/failure tracking

---

## 🏗️ Tech Stack

| Component | Technology |
|------------|-------------|
| **Backend Framework** | FastAPI |
| **Database ORM** | SQLAlchemy |
| **Database** | PostgreSQL |
| **OCR Engine** | EasyOCR |
| **Migrations** | Alembic |
| **Environment Management** | python-dotenv |
| **Language** | Python 3.10+ |

---
### FLOW TO START PROJECT

## 1. Create and activate virtual environment
python -m venv venv
venv\Scripts\activate

## 2. Install Dependencies 
pip install -r requirements.txt

## 3. Setup .env File  
#DATABASE_URL= "postgresql+psycopg://<USERNAME>:<PASSWORD>@<HOST>:<PORT>/<DATABASE_NAME>"

## 4. Alembic migrations
alembic upgrade head

## 5. Run the FastAPI application
uvicorn main:app --reload


## ⚙️ APIs in This Project 
You currently have 2 core API endpoints, each serving a specific purpose in the KYC OCR flow:

1. POST /upload
(Uploads an image file, validates it, performs OCR, extracts Name and Date of Birth, saves results to the database, and returns an OCRResponse)
2. GET	/flow/{flow_id}	Retrieves details of a specific OCR flow (from FlowManager) — including its status, tasks, and related record ID.

🖼️ Example Inputs:
Sample KYC images for testing the OCR pipeline are available in the example_inputs/ folder.
You can upload any of these using the /upload endpoint from the Swagger UI (http://localhost:8000/docs).

## KYC Flow Design 
1. Task Flow and Dependencies
The flow consists of four sequential tasks, each depending on the success of the previous task:
•	Task 1: Upload Image – Validate file type and size, then save it.
•	Task 2: Perform OCR – Extract text from image using EasyOCR.
•	Task 3: Extract Details – Parse Name and DOB from OCR text using regex.
•	Task 4: Save to DB – Save extracted details into the OCRRecord table.

Start
│
├── [Task 1: Upload Image]
│     ├── Success → Proceed to Task 2 (Perform OCR)
│     └── Fail → End Flow (Invalid file type or size)
│
├── [Task 2: Perform OCR]
│     ├── Success → Proceed to Task 3 (Extract Details)
│     └── Fail → End Flow (No text found in image)
│
├── [Task 3: Extract Details]
│     ├── Success → Proceed to Task 4 (Save to DB)
│     └── Fail → End Flow (Name or DOB not found)
│
├── [Task 4: Save to DB]
│     ├── Success → Flow Completed Successfully
│     └── Fail → End Flow (Failed to save record)
│
└── End

2. Success and Failure Evaluation
Each task defines its own success and failure conditions:
Task	Success Criteria	Failure Criteria
Upload Image	Valid file type (.jpg/.jpeg/.png) and size ≤ 1 MB	Invalid file type or exceeds size limit
Perform OCR	Text successfully extracted from the image	No text found or OCR error
Extract Details	Both Name and DOB successfully extracted	Either Name or DOB missing
Save to DB	Record successfully inserted and committed	Database insert or commit error

3. What happens if a task fails or succeeds
• If a task succeeds → The next task starts automatically.
• If a task fails → Flow halts immediately, logs error details, marks the task as failed in the database, and returns an appropriate HTTP response.





