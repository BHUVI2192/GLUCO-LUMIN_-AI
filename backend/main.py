"""
GlucoLumin FastAPI Backend
Railway Production Ready
"""
from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import uuid
import os
import traceback
from sqlalchemy import text
import numpy as np
from database import get_db, RawScanData as RawScanDataORM


# Initialize FastAPI
app = FastAPI(title="GlucoLumin Backend", version="2.0.0")

from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

# CORS - Allow all origins for mobile app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global status flags
DB_AVAILABLE = False
MODELS_LOADED = False
SHEETS_AVAILABLE = False

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    body = await request.body()
    print(f"\n[ERROR] 422 Validation Error:")
    print(f"Request URL: {request.url}")
    print(f"Body: {body.decode('utf-8', errors='replace')[:500]}")
    print(f"Details: {exc}\n")
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors(), "body": body.decode('utf-8', errors='replace')[:200]},
    )

@app.on_event("startup")
async def startup_event():
    """Initialize all services on startup"""
    global DB_AVAILABLE, MODELS_LOADED, SHEETS_AVAILABLE
    
    print("=" * 60)
    print("=== GLUCOLUMIN BACKEND STARTING ===")
    print(f"Railway URL: glucolumin-ai.up.railway.app")
    print(f"Port: {os.getenv('PORT', 'Not Set')}")
    print(f"DATABASE_URL: {'Present' if os.getenv('DATABASE_URL') else 'Missing'}")
    print("=" * 60)
    
    # 1. Initialize Database
    try:
        import csv_manager
        csv_manager.initialize_csvs()
        DB_AVAILABLE = True
        print("[DB] PostgreSQL tables initialized ✓")
    except Exception as e:
        print(f"[DB] Initialization failed: {e}")
        DB_AVAILABLE = False
    
    # 2. Check ML Models
    try:
        import ml_pipeline
        # Pre-load models
        _ = ml_pipeline.pipeline.predictor
        MODELS_LOADED = True
        print("[ML] Models loaded ✓")
    except Exception as e:
        print(f"[ML] Model loading failed: {e}")
        MODELS_LOADED = False
    
    # 3. Check Sheets (optional)
    try:
        from sheets_backup import sheets_backup
        SHEETS_AVAILABLE = sheets_backup.is_connected if hasattr(sheets_backup, 'is_connected') else False
        if SHEETS_AVAILABLE:
            print("[SHEETS] Google Sheets backup enabled ✓")
        else:
            print("[SHEETS] Disabled - using PostgreSQL only")
    except Exception as e:
        print(f"[SHEETS] Initialization failed: {e}")
        SHEETS_AVAILABLE = False
    
    print("=" * 60)
    print(f"=== STARTUP COMPLETE ===")
    print(f"Database: {'✓' if DB_AVAILABLE else '✗'}")
    print(f"Models: {'✓' if MODELS_LOADED else '✗'}")
    print(f"Sheets Backup: {'✓' if SHEETS_AVAILABLE else '✗'}")
    print("=" * 60)


# --- Data Models ---
class PatientRegistration(BaseModel):
    patient_name: str
    patient_age: int
    gender: str = "Male"
    height_cm: float
    weight_kg: float
    skin_tone: str
    blood_pressure: str
    had_food: str
    family_diabetic_history: str


class RawScanData(BaseModel):
    visit_id: str
    raw_data: str
    timestamp: Optional[str] = None



# --- Endpoints ---

@app.get("/")
def read_root():
    return {
        "message": "GlucoLumin AI Backend is Running",
        "status": "active",
        "version": "2.0.0",
        "url": "https://glucolumin-ai.up.railway.app"
    }


@app.get("/health")
def health_check():
    """Comprehensive health check for Railway"""
    import os
    
    # Check database
    db_status = "unknown"
    try:
        from database import engine
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)[:50]}"
    
    # Check models
    model1_exists = os.path.exists(os.path.join(os.path.dirname(__file__), "glucose_model.pkl"))
    model2_exists = os.path.exists(os.path.join(os.path.dirname(__file__), "glucose_linear_model_v5.pkl"))

    
    return {
        "status": "healthy",
        "url": "https://glucolumin-ai.up.railway.app",
        "environment": "railway" if os.getenv("RAILWAY_ENVIRONMENT") else "local",
        "port": os.getenv("PORT", "8000"),
        "database": db_status,
        "models": {
            "model1": model1_exists,
            "model2": model2_exists,
            "loaded": MODELS_LOADED
        },
        "sheets_backup": SHEETS_AVAILABLE,
        "timestamp": datetime.now().isoformat()
    }


@app.post("/api/start_scan")
def start_scan(patient: PatientRegistration):
    """Register a new patient scan"""
    try:
        import csv_manager
        
        # Generate Unique Visit ID
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
        print(f"[API] Patient registered: {visit_id}")
        return {"visit_id": visit_id, "status": "registered"}
        
    except Exception as e:
        print(f"[ERROR] start_scan failed: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/upload_raw")
async def upload_raw(data: RawScanData, background_tasks: BackgroundTasks):
    """
    Strict contract: JSON payload with comma-separated numbers in 'raw_data'.
    1. Parse & Validate
    2. Store in DB (COMMIT)
    3. Trigger ML Pipeline
    """
    import csv_manager
    import ml_pipeline
    from sheets_backup import sheets_backup

    print(f"[API] Raw payload for {data.visit_id}: {data.raw_data[:100]}...")

    # 1. Parse raw string -> list of floats
    values = parse_raw_values(data.raw_data)
    
    # 2. Basic Validation (No finger / Sensor Error)
    if not values:
        # Case: Empty or totally non-numeric
        msg = "NO_NUMERIC_DATA"
        log_invalid_scan(data.visit_id, msg, 0.0)
        return {"status": "error", "message": msg}

    # Statistical checks
    arr = np.array(values, dtype=float)
    mean_val = float(arr.mean())
    std_val = float(arr.std())
    
    # Heuristic thresholds (from prototype experience)
    # Mean > 200 (saturated) or < 5 (floating/open)
    # Std < 0.01 (flatline)
    if mean_val > 500 or mean_val < 5 or std_val < 0.01:
        flag = "NO_FINGER_DETECTED" if mean_val > 500 or std_val < 0.01 else "SENSOR_ERROR"
        
        print(f"[REJECT] {data.visit_id}: {flag} (Mean={mean_val:.2f}, Std={std_val:.2f})")
        
        # Log error state
        error_update = {
            "ml1_status": "ERROR",
            "ml2_status": "ERROR", 
            "result_flag": flag,
            "final_glucose": None,
            "diet_advice": "No valid signal detected. Please rescan."
        }
        
        # Update DB/Sheets via Manager
        csv_manager.update_patient_status(data.visit_id, error_update)
        csv_manager.log_invalid_scan(data.visit_id, flag, mean_val)
        
        return {"status": "error", "message": flag}

    # 3. Valid Data -> Store in DB (Synchronous Commit)
    try:
        timestamp = datetime.utcnow()
        if data.timestamp:
            try:
                timestamp = datetime.fromisoformat(data.timestamp.replace('Z', '+00:00'))
            except:
                pass

        with get_db() as db:
            # Create bulk objects
            rows = [
                RawScanDataORM(
                    visit_id=data.visit_id,
                    sample_index=str(i),
                    signal_value=str(v)
                )
                for i, v in enumerate(values)
            ]
            db.add_all(rows)
            db.commit()
            print(f"[API] Committed {len(rows)} raw rows for {data.visit_id}")

        # 4. Trigger ML Pipeline
        # Also update status to 'processing'
        csv_manager.update_patient_status(data.visit_id, {
            "raw_scan_id": f"RAW_{len(values)}",
            "ml1_status": "PENDING"
        })
        
        background_tasks.add_task(ml_pipeline.run_pipeline, data.visit_id)
        
        return {"status": "processing", "visit_id": data.visit_id}

    except Exception as e:
        print(f"[ERROR] upload_raw failed: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


def parse_raw_values(raw_str: str) -> List[float]:
    """
    Robustly parse comma-separated string into list of floats.
    Handles extra whitespace, newlines, and mixed content.
    """
    if "No finger" in raw_str:
        return []
        
    vals = []
    # Split by comma or newline
    tokens = raw_str.replace('\n', ',').split(',')
    
    for token in tokens:
        token = token.strip()
        if not token:
            continue
        try:
            # Remove potential null bytes or odd chars
            clean_token = token.replace('\x00', '')
            vals.append(float(clean_token))
        except ValueError:
            continue
            
    return vals



def log_invalid_scan(visit_id, reason, value):
    # Save to separate "invalid_scans" table for audit
    # Also log to Google Sheets with "ERROR" status
    print(f"[INVALID SCAN] {visit_id}: {reason} (value={value})")
    import csv_manager
    csv_manager.log_invalid_scan(visit_id, reason, value)


@app.get("/api/get_result/{visit_id}")
def get_result(visit_id: str):
    """Get ML pipeline results for a visit"""
    try:
        import csv_manager
        
        metadata = csv_manager.get_patient_metadata(visit_id)
        if not metadata:
            raise HTTPException(status_code=404, detail="Visit not found")

        ml2_status = metadata.get("ml2_status", "PENDING")
        final_glucose = metadata.get("final_glucose")
        classification = metadata.get("result_flag")
        diet_advice = metadata.get("diet_advice")
        
        # Return proper status format for Android app
        if ml2_status == "DONE" and final_glucose is not None:
            return {
                "visit_id": visit_id,
                "status": "completed",
                "final_glucose": float(final_glucose),
                "glucose": float(final_glucose),
                "confidence": 0.92,
                "classification": classification or "Normal",
                "diet_advice": diet_advice or "Maintain balanced diet.",
                "timestamp": metadata.get("timestamp"),
                "message": "Prediction successful"
            }
        elif ml2_status == "ERROR":
            return {
                "visit_id": visit_id,
                "status": "error",
                "message": "ML processing failed. Please try again."
            }
        else:
            # Still processing
            return {
                "visit_id": visit_id,
                "status": "processing",
                "ml1_status": metadata.get("ml1_status", "PENDING"),
                "ml2_status": ml2_status,
                "message": "Processing scan data..."
            }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] get_result failed: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))



@app.post("/api/upload_invalid_scan")
async def upload_invalid_scan(data: dict):
    """Log invalid/rejected scans for audit trail"""
    try:
        import csv_manager
        
        visit_id = data.get('visit_id')
        error_message = data.get('error_message', 'Unknown error')
        timestamp = data.get('timestamp')
        
        # Log using centralized manager serves all destinations (DB, CSV, Sheets)
        # Value is 0.0 as it's a generic invalid scan without a specific sensor reading value usually
        csv_manager.log_invalid_scan(visit_id, error_message, 0.0)
        
        return {"status": "logged", "message": "Invalid scan recorded for audit"}
        
    except Exception as e:
        print(f"[ERROR] upload_invalid_scan: {e}")
        return {"status": "error"}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    print(f"Starting server on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
