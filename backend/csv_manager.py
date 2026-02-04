"""
Data Manager for GlucoLumin
Uses PostgreSQL as primary storage with async Google Sheets backup
"""
import os
import pandas as pd
from datetime import datetime
from typing import List, Any, Dict, Optional

# Import database layer (primary storage)
import database as db
from sheets_backup import sheets_backup

# Legacy CSV paths (kept for backwards compatibility/fallback)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PATIENT_METADATA_FILE = os.path.join(BASE_DIR, "patient_metadata.csv")
RAW_SCAN_DATA_FILE = os.path.join(BASE_DIR, "raw_scan_data.csv")
INTERMEDIATE_FEATURES_FILE = os.path.join(BASE_DIR, "intermediate_features.csv")
CLINICAL_RESULTS_FILE = os.path.join(BASE_DIR, "clinical_results.csv")
INVALID_SCANS_FILE = os.path.join(BASE_DIR, "invalid_scans.csv")

# CSV Headers (kept for reference)
PATIENT_METADATA_COLS = [
    "visit_id", "patient_id", 
    "name", "age", "sex", "height_cm", "weight_kg", 
    "bmi", "skin_tone", "blood_pressure", "had_food", "family_diabetic_history",
    "timestamp", "raw_scan_id", "ml1_status", "ml2_status", "final_glucose", "result_flag", "diet_advice"
]

RAW_SCAN_DATA_COLS = ["visit_id", "sample_index", "signal_value"]

INTERMEDIATE_FEATURES_COLS = [
    "visit_id",
    "feat_mean", "feat_std", "feat_rms", 
    "fft_peak1_power", "fft_peak2_power", "spectral_entropy", 
    "wavelet_energy_low", "wavelet_energy_mid", "wavelet_energy_high", 
    "autoencoder_recon_error", "skin_tone_encoded"
]

CLINICAL_RESULTS_COLS = [
    "visit_id", "patient_id", "glucose_mg_dl", "classification", "diet_advice", "timestamp"
]

INVALID_SCANS_COLS = [
    "visit_id", "reason", "value", "timestamp"
]


def initialize_csvs():
    """Initialize PostgreSQL tables (legacy function name kept for compatibility)"""
    try:
        db.create_tables()
        print("[DataManager] PostgreSQL tables initialized")
    except Exception as e:
        print(f"[DataManager] Error initializing database: {e}")
        # Fallback: create CSV files if database fails
        _init_csv_fallback()


def _init_csv_fallback():
    """Fallback: Initialize CSV files if database is unavailable"""
    _init_file(PATIENT_METADATA_FILE, PATIENT_METADATA_COLS)
    _init_file(RAW_SCAN_DATA_FILE, RAW_SCAN_DATA_COLS)
    _init_file(INTERMEDIATE_FEATURES_FILE, INTERMEDIATE_FEATURES_COLS)
    _init_file(CLINICAL_RESULTS_FILE, CLINICAL_RESULTS_COLS)
    _init_file(INVALID_SCANS_FILE, INVALID_SCANS_COLS)


def _init_file(filepath: str, columns: List[str]):
    if not os.path.exists(filepath):
        df = pd.DataFrame(columns=columns)
        df.to_csv(filepath, index=False)
        print(f"Created {filepath}")


def append_patient_metadata(data: dict):
    """
    Save patient metadata.
    1. PostgreSQL (primary) - synchronous
    2. Google Sheets (backup) - async, non-blocking
    """
    # 1. Save to PostgreSQL (primary)
    success = db.add_patient_metadata(data)
    
    if not success:
        print("[DataManager] PostgreSQL failed, falling back to CSV")
        _csv_append_patient_metadata(data)
    
    # 2. Queue for Google Sheets backup (async, non-blocking)
    sheets_backup.queue_metadata(data)


def _csv_append_patient_metadata(data: dict):
    """Fallback: Append to CSV"""
    row_data = {col: data.get(col, None) for col in PATIENT_METADATA_COLS}
    df = pd.DataFrame([row_data])
    
    if os.path.exists(PATIENT_METADATA_FILE):
        df.to_csv(PATIENT_METADATA_FILE, mode='a', header=False, index=False)
    else:
        df.to_csv(PATIENT_METADATA_FILE, index=False)


def append_raw_data(rows: List[dict]):
    """
    Save raw scan data.
    1. PostgreSQL (primary) - synchronous
    2. Google Sheets (backup) - async, non-blocking
    """
    if not rows:
        return
    
    # 1. Save to PostgreSQL (primary)
    success = db.add_raw_data(rows)
    
    if not success:
        print("[DataManager] PostgreSQL failed for raw data, falling back to CSV")
        _csv_append_raw_data(rows)
    
    # 2. Queue for Google Sheets backup (async, non-blocking)
    sheets_backup.queue_raw_data(rows)


def _csv_append_raw_data(rows: List[dict]):
    """Fallback: Append to CSV"""
    df = pd.DataFrame(rows)
    df = df[RAW_SCAN_DATA_COLS]
    if os.path.exists(RAW_SCAN_DATA_FILE):
        df.to_csv(RAW_SCAN_DATA_FILE, mode='a', header=False, index=False)
    else:
        df.to_csv(RAW_SCAN_DATA_FILE, index=False)


def update_patient_status(visit_id: str, updates: dict):
    """
    Update patient status fields.
    1. PostgreSQL (primary) - synchronous
    2. Google Sheets (backup) - async, non-blocking
    """
    # 1. Update in PostgreSQL (primary)
    success = db.update_patient_status(visit_id, updates)
    
    if not success:
        print("[DataManager] PostgreSQL update failed, falling back to CSV")
        _csv_update_patient_status(visit_id, updates)
    
    # 2. Queue for Google Sheets backup (async, non-blocking)
    sheets_backup.queue_status_update(visit_id, updates)


def _csv_update_patient_status(visit_id: str, updates: dict):
    """Fallback: Update CSV"""
    if not os.path.exists(PATIENT_METADATA_FILE):
        return
    
    df = pd.read_csv(PATIENT_METADATA_FILE)
    
    if visit_id in df['visit_id'].values:
        for col, val in updates.items():
            if col in df.columns:
                df.loc[df['visit_id'] == visit_id, col] = val
        df.to_csv(PATIENT_METADATA_FILE, index=False)


def save_features(visit_id: str, features: dict):
    """
    Save ML features.
    1. PostgreSQL (primary) - synchronous
    2. Google Sheets (backup) - async, non-blocking
    """
    features['visit_id'] = visit_id
    
    # Ensure all columns exist
    for col in INTERMEDIATE_FEATURES_COLS:
        if col not in features:
            features[col] = 0
    
    # Sort columns to match header
    features_ordered = {col: features[col] for col in INTERMEDIATE_FEATURES_COLS}
    
    # 1. Save to PostgreSQL (primary)
    success = db.add_features(visit_id, features_ordered)
    
    if not success:
        print("[DataManager] PostgreSQL failed for features, falling back to CSV")
        _csv_save_features(features_ordered)
    
    # 2. Queue for Google Sheets backup (async, non-blocking)
    sheets_backup.queue_features(features_ordered)


def _csv_save_features(features: dict):
    """Fallback: Save to CSV"""
    df = pd.DataFrame([features])
    
    if os.path.exists(INTERMEDIATE_FEATURES_FILE):
        existing_df = pd.read_csv(INTERMEDIATE_FEATURES_FILE)
        combined_df = pd.concat([existing_df, df], ignore_index=True)
        combined_df = combined_df[INTERMEDIATE_FEATURES_COLS]
        combined_df.to_csv(INTERMEDIATE_FEATURES_FILE, index=False)
    else:
        df.to_csv(INTERMEDIATE_FEATURES_FILE, index=False)


def save_clinical_result(result: dict):
    """
    Save clinical result.
    1. PostgreSQL (primary) - synchronous
    2. Google Sheets (backup) - async, non-blocking
    """
    # Ensure all columns exist
    row_data = {col: result.get(col, None) for col in CLINICAL_RESULTS_COLS}
    
    # 1. Save to PostgreSQL (primary)
    success = db.add_clinical_result(row_data)
    
    if not success:
        print("[DataManager] PostgreSQL failed for result, falling back to CSV")
        _csv_save_clinical_result(row_data)
    
    # 2. Queue for Google Sheets backup (async, non-blocking)
    sheets_backup.queue_result(row_data)


def _csv_save_clinical_result(result: dict):
    """Fallback: Save to CSV"""
    df = pd.DataFrame([result])
    
    if os.path.exists(CLINICAL_RESULTS_FILE):
        df.to_csv(CLINICAL_RESULTS_FILE, mode='a', header=False, index=False)
    else:
        df.to_csv(CLINICAL_RESULTS_FILE, index=False)


def get_patient_metadata(visit_id: str) -> Optional[Dict[str, Any]]:
    """
    Get patient metadata.
    Primary: PostgreSQL
    Fallback: CSV
    """
    # Try PostgreSQL first
    result = db.get_patient_metadata(visit_id)
    
    if result:
        return result
    
    # Fallback to CSV
    print(f"[DataManager] Falling back to CSV for visit: {visit_id}")
    return _csv_get_patient_metadata(visit_id)


def _csv_get_patient_metadata(visit_id: str) -> Optional[Dict[str, Any]]:
    """Fallback: Get from CSV"""
    if not os.path.exists(PATIENT_METADATA_FILE):
        return None
    
    df = pd.read_csv(PATIENT_METADATA_FILE)
    row = df[df['visit_id'] == visit_id]
    
    if row.empty:
        return None
    
    # Replace NaN with None
    return row.iloc[0].where(pd.notnull(row.iloc[0]), None).to_dict()


def get_raw_data(visit_id: str) -> List[Dict[str, Any]]:
    """
    Get raw scan data.
    Primary: PostgreSQL
    Fallback: CSV
    """
    # Try PostgreSQL first
    result = db.get_raw_data(visit_id)
    
    if result:
        return result
    
    # Fallback to CSV
    return _csv_get_raw_data(visit_id)


def _csv_get_raw_data(visit_id: str) -> List[Dict[str, Any]]:
    """Fallback: Get from CSV"""
    if not os.path.exists(RAW_SCAN_DATA_FILE):
        return []
    
    df = pd.read_csv(RAW_SCAN_DATA_FILE)
    rows = df[df['visit_id'] == visit_id]
    
    return rows.to_dict('records')


def log_invalid_scan(visit_id: str, reason: str, value: float):
    """
    Log invalid scan.
    1. PostgreSQL (primary)
    2. Google Sheets (backup)
    """
    data = {
        "visit_id": visit_id,
        "reason": reason,
        "value": value,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    # 1. Save to PostgreSQL (primary)
    success = db.add_invalid_scan(data)
    
    if not success:
        print("[DataManager] PostgreSQL failed for invalid scan, falling back to CSV")
        _csv_log_invalid_scan(data)
    
    # 2. Queue for Google Sheets backup (async, non-blocking)
    sheets_backup.queue_invalid_scan(data)


def _csv_log_invalid_scan(data: dict):
    """Fallback: Save to CSV"""
    df = pd.DataFrame([data])
    
    if os.path.exists(INVALID_SCANS_FILE):
        df.to_csv(INVALID_SCANS_FILE, mode='a', header=False, index=False)
    else:
        df.to_csv(INVALID_SCANS_FILE, index=False)
