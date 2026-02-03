"""
Async Google Sheets Backup for GlucoLumin
Non-blocking backup layer using background threads
Railway Production Ready - Graceful failure handling
"""
import os
import threading
import queue
import time
from typing import Dict, Any, List

# Try to import gspread with new google-auth
SHEETS_AVAILABLE = False
try:
    import gspread
    from google.oauth2.service_account import Credentials
    GSPREAD_AVAILABLE = True
except ImportError:
    GSPREAD_AVAILABLE = False
    print("[SheetsBackup] gspread not available")

# Constants
CREDENTIALS_FILE = os.path.join(os.path.dirname(__file__), "credentials.json")
SHEET_NAME_METADATA = "GlucoLumin_Patient_Metadata"
SHEET_NAME_RESULTS = "GlucoLumin_Clinical_Results"
SHEET_NAME_RAW_DATA = "GlucoLumin_Raw_Scan_Data"
SHEET_NAME_FEATURES = "GlucoLumin_Intermediate_Features"

SCOPE = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/spreadsheets"
]

# Retry settings
MAX_RETRIES = 3
RETRY_DELAY_BASE = 2

# Column definitions
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


class AsyncSheetsBackup:
    """Non-blocking Google Sheets backup manager with graceful failure handling"""
    
    def __init__(self):
        self.client = None
        self.is_connected = False
        self.backup_queue = queue.Queue()
        self.worker_thread = None
        self.running = False
        
        # Sheet references (lazy loaded)
        self._metadata_sheet = None
        self._results_sheet = None
        self._raw_data_sheet = None
        self._features_sheet = None
        
        # Only start if gspread is available
        if GSPREAD_AVAILABLE:
            self._start_worker()
        else:
            print("[SheetsBackup] Disabled - gspread not installed")
    
    def _authenticate(self) -> bool:
        """Authenticate with Google Sheets API using google-auth"""
        if not GSPREAD_AVAILABLE:
            return False
            
        if self.client and self.is_connected:
            return True
            
        if not os.path.exists(CREDENTIALS_FILE):
            print(f"[SheetsBackup] Warning: {CREDENTIALS_FILE} not found. Backup disabled.")
            return False
        
        try:
            # Use google-auth instead of deprecated oauth2client
            creds = Credentials.from_service_account_file(
                CREDENTIALS_FILE,
                scopes=SCOPE
            )
            self.client = gspread.authorize(creds)
            self.is_connected = True
            print("[SheetsBackup] Authentication successful")
            return True
        except Exception as e:
            print(f"[SheetsBackup] Authentication failed: {e}")
            self.is_connected = False
            return False
    
    def _get_sheet(self, sheet_name: str, columns: List[str]):
        """Get or create a sheet"""
        if not self.is_connected:
            if not self._authenticate():
                return None
        
        try:
            sh = self.client.open(sheet_name)
            return sh.sheet1
        except gspread.SpreadsheetNotFound:
            try:
                print(f"[SheetsBackup] Creating sheet: {sheet_name}")
                sh = self.client.create(sheet_name)
                sheet = sh.sheet1
                sheet.append_row(columns)
                return sheet
            except Exception as e:
                print(f"[SheetsBackup] Error creating sheet: {e}")
                return None
        except Exception as e:
            print(f"[SheetsBackup] Error opening sheet: {e}")
            return None
    
    @property
    def metadata_sheet(self):
        if not self._metadata_sheet:
            self._metadata_sheet = self._get_sheet(SHEET_NAME_METADATA, PATIENT_METADATA_COLS)
        return self._metadata_sheet
    
    @property
    def results_sheet(self):
        if not self._results_sheet:
            self._results_sheet = self._get_sheet(SHEET_NAME_RESULTS, CLINICAL_RESULTS_COLS)
        return self._results_sheet
    
    @property
    def raw_data_sheet(self):
        if not self._raw_data_sheet:
            self._raw_data_sheet = self._get_sheet(SHEET_NAME_RAW_DATA, RAW_SCAN_DATA_COLS)
        return self._raw_data_sheet
    
    @property
    def features_sheet(self):
        if not self._features_sheet:
            self._features_sheet = self._get_sheet(SHEET_NAME_FEATURES, INTERMEDIATE_FEATURES_COLS)
        return self._features_sheet
    
    def _start_worker(self):
        """Start the background worker thread"""
        if self.worker_thread and self.worker_thread.is_alive():
            return
        
        self.running = True
        self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self.worker_thread.start()
        print("[SheetsBackup] Background worker started")
    
    def _worker_loop(self):
        """Main worker loop that processes the backup queue"""
        while self.running:
            try:
                try:
                    task = self.backup_queue.get(timeout=5)
                except queue.Empty:
                    continue
                
                data_type = task.get('type')
                data = task.get('data')
                
                success = self._process_with_retry(data_type, data)
                
                if success:
                    print(f"[SheetsBackup] Backed up {data_type}")
                else:
                    print(f"[SheetsBackup] Failed to backup {data_type} after {MAX_RETRIES} retries")
                
                self.backup_queue.task_done()
                
            except Exception as e:
                print(f"[SheetsBackup] Worker error: {e}")
    
    def _process_with_retry(self, data_type: str, data: Any) -> bool:
        """Process backup with retry logic"""
        for attempt in range(MAX_RETRIES):
            try:
                if data_type == 'metadata':
                    return self._backup_metadata(data)
                elif data_type == 'raw_data':
                    return self._backup_raw_data(data)
                elif data_type == 'features':
                    return self._backup_features(data)
                elif data_type == 'result':
                    return self._backup_result(data)
                elif data_type == 'status_update':
                    return self._backup_status_update(data['visit_id'], data['updates'])
                else:
                    return False
                    
            except Exception as e:
                print(f"[SheetsBackup] Error on attempt {attempt + 1}: {e}")
                delay = RETRY_DELAY_BASE * (2 ** attempt)
                time.sleep(delay)
        
        return False
    
    def _backup_metadata(self, data: Dict[str, Any]) -> bool:
        sheet = self.metadata_sheet
        if not sheet:
            return False
        row = [str(data.get(col, "")) for col in PATIENT_METADATA_COLS]
        sheet.append_row(row)
        return True
    
    def _backup_raw_data(self, rows: List[Dict[str, Any]]) -> bool:
        sheet = self.raw_data_sheet
        if not sheet:
            return False
        formatted_rows = [[str(item.get(col, "")) for col in RAW_SCAN_DATA_COLS] for item in rows]
        if formatted_rows:
            sheet.append_rows(formatted_rows)
        return True
    
    def _backup_features(self, features: Dict[str, Any]) -> bool:
        sheet = self.features_sheet
        if not sheet:
            return False
        row = [str(features.get(col, "")) for col in INTERMEDIATE_FEATURES_COLS]
        sheet.append_row(row)
        return True
    
    def _backup_result(self, result: Dict[str, Any]) -> bool:
        sheet = self.results_sheet
        if not sheet:
            return False
        row = [str(result.get(col, "")) for col in CLINICAL_RESULTS_COLS]
        sheet.append_row(row)
        return True
    
    def _backup_status_update(self, visit_id: str, updates: Dict[str, Any]) -> bool:
        sheet = self.metadata_sheet
        if not sheet:
            return False
        try:
            cell = sheet.find(visit_id)
            if not cell:
                return True
            row_idx = cell.row
            for col_name, value in updates.items():
                if col_name in PATIENT_METADATA_COLS:
                    col_idx = PATIENT_METADATA_COLS.index(col_name) + 1
                    sheet.update_cell(row_idx, col_idx, str(value))
            return True
        except Exception as e:
            print(f"[SheetsBackup] Error updating status: {e}")
            return False
    
    # ============== PUBLIC API ==============
    
    def queue_metadata(self, data: Dict[str, Any]):
        if GSPREAD_AVAILABLE:
            self.backup_queue.put({'type': 'metadata', 'data': data})
            print(f"[SheetsBackup] Queued metadata: {data.get('visit_id')}")
    
    def queue_raw_data(self, rows: List[Dict[str, Any]]):
        if GSPREAD_AVAILABLE:
            self.backup_queue.put({'type': 'raw_data', 'data': rows})
            print(f"[SheetsBackup] Queued raw data: {len(rows)} rows")
    
    def queue_features(self, features: Dict[str, Any]):
        if GSPREAD_AVAILABLE:
            self.backup_queue.put({'type': 'features', 'data': features})
    
    def queue_result(self, result: Dict[str, Any]):
        if GSPREAD_AVAILABLE:
            self.backup_queue.put({'type': 'result', 'data': result})
    
    def queue_status_update(self, visit_id: str, updates: Dict[str, Any]):
        if GSPREAD_AVAILABLE:
            self.backup_queue.put({
                'type': 'status_update',
                'data': {'visit_id': visit_id, 'updates': updates}
            })
    
    def stop(self):
        self.running = False
        if self.worker_thread:
            self.worker_thread.join(timeout=5)


# Global instance
sheets_backup = AsyncSheetsBackup()
