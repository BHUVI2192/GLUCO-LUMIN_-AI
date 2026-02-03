
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

print("Importing csv_manager...")
try:
    import csv_manager
    print("csv_manager imported successfully.")
except ImportError as e:
    print(f"Failed to import csv_manager: {e}")
    sys.exit(1)

print("Importing main...")
try:
    from main import app, PatientRegistration
    print("main imported successfully.")
except ImportError as e:
    print(f"Failed to import main: {e}")
    sys.exit(1)

print("Importing ml_pipeline...")
try:
    import ml_pipeline
    print("ml_pipeline imported successfully.")
except ImportError as e:
    print(f"Failed to import ml_pipeline: {e}")
    sys.exit(1)

print("Initializing CSVs...")
try:
    csv_manager.initialize_csvs()
    print("CSVs initialized.")
except Exception as e:
    print(f"Failed to initialize CSVs: {e}")
    sys.exit(1)

print("Testing Pipeline & Feature Extraction...")
try:
    # This should trigger training if model doesn't exist
    from ml_pipeline import pipeline
    print("Pipeline instantiated.")
    
    # Test Synthetic Data Gen (Check columns)
    df = pipeline.predictor._generate_synthetic_data()
    expected_col = 'Spectral_Entropy'
    if expected_col in df.columns:
        print(f"Verified: Synthetic data contains '{expected_col}'")
    else:
        print(f"ERROR: Synthetic data missing '{expected_col}'")
        sys.exit(1)

    if pipeline.predictor.pipeline:
        print("Model loaded/trained successfully.")
    else:
        print("Model pipeline is None!")
        
except Exception as e:
    print(f"Failed to load pipeline: {e}")
    sys.exit(1)

print("verification_complete")
