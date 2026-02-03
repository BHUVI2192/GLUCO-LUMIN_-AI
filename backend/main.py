from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import uuid
import csv_manager
import ml_pipeline

app = FastAPI(title="GlucoLumin Backend")

from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

# Trigger reload: LinearRegression Model v5

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow all for local dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    body = await request.body()
    print(f"\n[ERROR] 422 Validation Error:")
    print(f"Request URL: {request.url}")
    print(f"Body: {body.decode('utf-8', errors='replace')}")
    print(f"Details: {exc}\n")
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors(), "body": body.decode('utf-8', errors='replace')},
    )

# Initialize CSVs on startup
@app.on_event("startup")
async def startup_event():
    csv_manager.initialize_csvs()
    # Trigger model loading/training on startup to avoid delay on first request
    # This might take a few seconds if training is needed
    print("Initializing ML Pipeline...")
    _ = ml_pipeline.pipeline.predictor 

# --- Data Models ---
class PatientRegistration(BaseModel):
    # Prompt asked for: patient_name, patient_age, height_cm, weight_kg, skin_tone, blood_pressure, had_food, family_diabetic_history
    patient_name: str
    patient_age: int
    gender: str = "Male" 
    height_cm: float
    weight_kg: float
    skin_tone: str # (Very Fair, Fair, Medium, Dark)
    blood_pressure: str # "120/80"
    had_food: str # (Yes, No)
    family_diabetic_history: str # (Yes, No)

class RawDataLines(BaseModel):
    lines: List[str] 

# --- Endpoints ---

# --- Endpoints ---

@app.get("/")
def read_root():
    return {"message": "GlucoLumin AI Backend is Running", "status": "active"}

@app.post("/api/start_scan")
def start_scan(patient: PatientRegistration):
    # Generate Unique Visit ID: VYYYYMMDD_XXX
    timestamp = datetime.now()
    date_str = timestamp.strftime("%Y%m%d")
    unique_suffix = str(uuid.uuid4().hex)[:6].upper()
    visit_id = f"V{date_str}_{unique_suffix}"

    # Calculate BMI
    bmi = 0.0
    if patient.height_cm > 0:
        height_m = patient.height_cm / 100
        bmi = round(patient.weight_kg / (height_m * height_m), 2)

    data = {
        "visit_id": visit_id,
        "patient_id": f"P-{unique_suffix}", 
        "name": patient.patient_name,
        "age": patient.patient_age,
        "sex": patient.gender,
        "height_cm": patient.height_cm,
        "weight_kg": patient.weight_kg,
        "bmi": bmi,
        "skin_tone": patient.skin_tone,
        "blood_pressure": patient.blood_pressure,
        "had_food": patient.had_food,
        "family_diabetic_history": patient.family_diabetic_history,
        "timestamp": timestamp.isoformat(),
        "raw_scan_id": "",
        "ml1_status": "PENDING",
        "ml2_status": "PENDING",
        "final_glucose": None,
        "result_flag": None,
        "diet_advice": None
    }

    csv_manager.append_patient_metadata(data)
    return {"visit_id": visit_id, "status": "registered"}

@app.post("/api/upload_raw")
async def upload_raw(payload: RawDataLines, background_tasks: BackgroundTasks):
    lines = payload.lines
    if not lines:
        print(f"[ERROR 400] No data provided. Payload: {payload}")
        raise HTTPException(status_code=400, detail="No data provided")
    
    # DEBUG: Log first 5 lines to see what's being received
    print(f"[DEBUG] Received {len(lines)} lines of raw data")
    for i, line in enumerate(lines[:5]):
        print(f"[DEBUG] Line {i}: {line[:100] if len(line) > 100 else line}")

    # Parse first line to get visit_id
    try:
        first_line = lines[0].strip().split(',')
        visit_id = first_line[0]
        if not visit_id.startswith("V"): 
             print(f"[WARN] Visit ID does not start with V: '{visit_id}'")
    except Exception as e:
        print(f"[ERROR 400] Invalid data format. First line: '{lines[0] if lines else 'EMPTY'}', Error: {e}")
        raise HTTPException(status_code=400, detail="Invalid data format")

    parsed_rows = []
    numeric_count = 0
    non_numeric_count = 0
    
    for line in lines:
        parts = line.strip().split(',')
        if len(parts) >= 3:
            signal_val = parts[2]
            # Count numeric vs non-numeric
            try:
                float(signal_val)
                numeric_count += 1
            except:
                non_numeric_count += 1
            
            parsed_rows.append({
                "visit_id": parts[0],
                "sample_index": parts[1],
                "signal_value": signal_val
            })
    
    print(f"[DEBUG] Parsed: {len(parsed_rows)} rows, {numeric_count} numeric, {non_numeric_count} non-numeric")
    
    csv_manager.append_raw_data(parsed_rows)
    csv_manager.update_patient_status(visit_id, {
        "raw_scan_id": f"RAW_{len(parsed_rows)}",
        "ml1_status": "PENDING"
    })

    # Trigger ML Pipeline
    background_tasks.add_task(ml_pipeline.run_pipeline, visit_id)

    return {"status": "uploaded", "count": len(parsed_rows)}

@app.get("/api/get_result/{visit_id}")
def get_result(visit_id: str):
    metadata = csv_manager.get_patient_metadata(visit_id)
    if not metadata:
        raise HTTPException(status_code=404, detail="Visit not found")
    
    return {
        "visit_id": visit_id,
        "status": metadata.get("ml2_status", "PENDING"),
        "glucose": metadata.get("final_glucose"),
        "classification": metadata.get("result_flag"),
        "diet_advice": metadata.get("diet_advice"),
        "timestamp": metadata.get("timestamp")
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))  # Railway provides PORT
    uvicorn.run(app, host="0.0.0.0", port=port)
