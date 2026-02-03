import os
import pandas as pd
from datetime import datetime
from typing import List, Any
from sheets_manager import sheets_manager

# Define File Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PATIENT_METADATA_FILE = os.path.join(BASE_DIR, "patient_metadata.csv")
RAW_SCAN_DATA_FILE = os.path.join(BASE_DIR, "raw_scan_data.csv")
INTERMEDIATE_FEATURES_FILE = os.path.join(BASE_DIR, "intermediate_features.csv")
CLINICAL_RESULTS_FILE = os.path.join(BASE_DIR, "clinical_results.csv")

# CSV Headers
PATIENT_METADATA_COLS = [
    "visit_id", "patient_id", 
    "name", "age", "sex", "height_cm", "weight_kg", 
    "bmi", "skin_tone", "blood_pressure", "had_food", "family_diabetic_history",
    "timestamp", "raw_scan_id", "ml1_status", "ml2_status", "final_glucose", "result_flag", "diet_advice"
]

RAW_SCAN_DATA_COLS = ["visit_id", "sample_index", "signal_value"]

# Expanded Feature Set based on Model 1 integration
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

def initialize_csvs():
    """Checks if CSV files exist, creates them with headers if not."""
    _init_file(PATIENT_METADATA_FILE, PATIENT_METADATA_COLS)
    _init_file(RAW_SCAN_DATA_FILE, RAW_SCAN_DATA_COLS)
    _init_file(INTERMEDIATE_FEATURES_FILE, INTERMEDIATE_FEATURES_COLS) 
    _init_file(CLINICAL_RESULTS_FILE, CLINICAL_RESULTS_COLS)

def _init_file(filepath: str, columns: List[str]):
    if not os.path.exists(filepath):
        df = pd.DataFrame(columns=columns)
        df.to_csv(filepath, index=False)
        print(f"Created {filepath}")

def append_patient_metadata(data: dict):
    """Appends a new patient visit to metadata."""
    # Ensure all columns exist, fill missing with None
    row_data = {col: data.get(col, None) for col in PATIENT_METADATA_COLS}
    df = pd.DataFrame([row_data])
    
    if os.path.exists(PATIENT_METADATA_FILE):
        df.to_csv(PATIENT_METADATA_FILE, mode='a', header=False, index=False)
    else:
        df.to_csv(PATIENT_METADATA_FILE, index=False)

    # Google Sheets Integration
    sheets_manager.append_metadata(data)

def append_raw_data(rows: List[dict]):
    """Appends raw scan data rows."""
    if not rows:
        return

    df = pd.DataFrame(rows)
    # Ensure columns order
    df = df[RAW_SCAN_DATA_COLS]
    if os.path.exists(RAW_SCAN_DATA_FILE):
        df.to_csv(RAW_SCAN_DATA_FILE, mode='a', header=False, index=False)
    else:
        df.to_csv(RAW_SCAN_DATA_FILE, index=False)

    # Google Sheets Integration
    sheets_manager.append_raw_data(rows)

def update_patient_status(visit_id: str, updates: dict):
    """Updates specific columns for a patient visit."""
    if not os.path.exists(PATIENT_METADATA_FILE):
        return
    
    # Read all as string first to avoid type errors, then infer if needed, 
    # but for simple updates reading as-is is safer.
    df = pd.read_csv(PATIENT_METADATA_FILE)
    
    if visit_id in df['visit_id'].values:
        for col, val in updates.items():
            if col in df.columns:
                df.loc[df['visit_id'] == visit_id, col] = val
        df.to_csv(PATIENT_METADATA_FILE, index=False)
        
        # Google Sheets Integration
        sheets_manager.update_status(visit_id, updates)

def save_features(visit_id: str, features: dict):
    """Saves extracted features."""
    features['visit_id'] = visit_id
    
    # Ensure features dict contains all columns (fill missing with 0)
    for col in INTERMEDIATE_FEATURES_COLS:
        if col not in features:
            features[col] = 0

    # Sort columns to match header
    features_ordered = {col: features[col] for col in INTERMEDIATE_FEATURES_COLS}
    
    df = pd.DataFrame([features_ordered])
    
    if os.path.exists(INTERMEDIATE_FEATURES_FILE):
        existing_df = pd.read_csv(INTERMEDIATE_FEATURES_FILE)
        combined_df = pd.concat([existing_df, df], ignore_index=True)
        # Ensure only defined columns are saved
        combined_df = combined_df[INTERMEDIATE_FEATURES_COLS]
        combined_df.to_csv(INTERMEDIATE_FEATURES_FILE, index=False)
    else:
        df.to_csv(INTERMEDIATE_FEATURES_FILE, index=False)

    # Google Sheets Integration
    sheets_manager.append_features(features_ordered)

def save_clinical_result(result: dict):
    """Saves final clinical result."""
    # Ensure all columns exist
    row_data = {col: result.get(col, None) for col in CLINICAL_RESULTS_COLS}
    df = pd.DataFrame([row_data])

    if os.path.exists(CLINICAL_RESULTS_FILE):
        df.to_csv(CLINICAL_RESULTS_FILE, mode='a', header=False, index=False)
    else:
        df.to_csv(CLINICAL_RESULTS_FILE, index=False)

    # Google Sheets Integration
    sheets_manager.append_result(result)

def get_patient_metadata(visit_id: str):
    """Retrieves patient metadata for a specific visit."""
    if not os.path.exists(PATIENT_METADATA_FILE):
        return None
    df = pd.read_csv(PATIENT_METADATA_FILE)
    row = df[df['visit_id'] == visit_id]
    if row.empty:
        return None
    # Replace NaN with None
    return row.iloc[0].where(pd.notnull(row.iloc[0]), None).to_dict()
