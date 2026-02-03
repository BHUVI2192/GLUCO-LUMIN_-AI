import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
import time

# Constants
CREDENTIALS_FILE = os.path.join(os.path.dirname(__file__), "credentials.json")
SHEET_NAME_METADATA = "GlucoLumin_Patient_Metadata"
SHEET_NAME_RESULTS = "GlucoLumin_Clinical_Results"
SHEET_NAME_RAW_DATA = "GlucoLumin_Raw_Scan_Data"
SHEET_NAME_FEATURES = "GlucoLumin_Intermediate_Features"

SCOPE = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

class SheetsManager:
    def __init__(self):
        self.client = None
        self.metadata_sheet = None
        self.results_sheet = None
        self.raw_data_sheet = None
        self.features_sheet = None
        self.is_connected = False
        self._authenticate()

    def _authenticate(self):
        """Authenticates with Google Sheets API if credentials exist."""
        if not os.path.exists(CREDENTIALS_FILE):
            print(f"[SheetsManager] Warning: {CREDENTIALS_FILE} not found. Sheets integration disabled.")
            return

        try:
            creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, SCOPE)
            self.client = gspread.authorize(creds)
            self.is_connected = True
            print("[SheetsManager] Custom Authentication successful.")
            self._init_sheets()
        except Exception as e:
            print(f"[SheetsManager] Authentication failed: {e}")
            self.is_connected = False

    def _init_sheets(self):
        """Opens or creates the necessary sheets."""
        if not self.is_connected: return

        try:
            # Metadata Sheet
            self.metadata_sheet = self._get_or_create_sheet(SHEET_NAME_METADATA, "PATIENT_METADATA_COLS")
            
            # Results Sheet
            self.results_sheet = self._get_or_create_sheet(SHEET_NAME_RESULTS, "CLINICAL_RESULTS_COLS")

            # Raw Data Sheet
            self.raw_data_sheet = self._get_or_create_sheet(SHEET_NAME_RAW_DATA, "RAW_SCAN_DATA_COLS")

            # Intermediate Features Sheet
            self.features_sheet = self._get_or_create_sheet(SHEET_NAME_FEATURES, "INTERMEDIATE_FEATURES_COLS")

        except Exception as e:
            print(f"[SheetsManager] Error initializing sheets: {e}")
            self.is_connected = False

    def _get_or_create_sheet(self, sheet_name, cols_var_name):
        """Helper to get a sheet or create it with headers if missing."""
        try:
            sh = self.client.open(sheet_name)
            print(f"[SheetsManager] Connected to: {sh.title} ({sh.url})")
            return sh.sheet1
        except gspread.SpreadsheetNotFound:
            print(f"[SheetsManager] Creating new sheet: {sheet_name}")
            sh = self.client.create(sheet_name)
            print(f"[SheetsManager] Created new sheet at: {sh.url}")
            # Optional: Make it accessible to anyone with link if strict privacy isn't required for dev
            # sh.share(None, perm_type='anyone', role='reader') 
            
            sheet = sh.sheet1
            
            # Initialize headers
            from csv_manager import PATIENT_METADATA_COLS, CLINICAL_RESULTS_COLS, RAW_SCAN_DATA_COLS, INTERMEDIATE_FEATURES_COLS
            
            if cols_var_name == "PATIENT_METADATA_COLS": headers = PATIENT_METADATA_COLS
            elif cols_var_name == "CLINICAL_RESULTS_COLS": headers = CLINICAL_RESULTS_COLS
            elif cols_var_name == "RAW_SCAN_DATA_COLS": headers = RAW_SCAN_DATA_COLS
            elif cols_var_name == "INTERMEDIATE_FEATURES_COLS": headers = INTERMEDIATE_FEATURES_COLS
            else: headers = []

            if headers:
                sheet.append_row(headers)
            
            return sheet
            return sheet
        except gspread.exceptions.APIError as e:
            if 'quota' in str(e).lower() or '403' in str(e):
                 print(f"[SheetsManager] CRITICAL ERROR: Google Drive Storage Full! Cannot create/write sheets.")
                 print(f"[SheetsManager] Please clear space in your Google Drive or use a different account.")
                 print(f"[SheetsManager] Switching to OFFLINE MODE (CSV only).")
                 self.is_connected = False
                 # Raise to stop further initialization attempts for this session if needed, or just return None
                 return None
            else:
                 print(f"[SheetsManager] API Error: {e}")
                 return None
        except Exception as e:
            print(f"[SheetsManager] Error opening/creating {sheet_name}: {e}")
            return None

    def append_metadata(self, data: dict):
        """Appends a row to the metadata sheet."""
        if not self.is_connected or not self.metadata_sheet: return
        try:
            from csv_manager import PATIENT_METADATA_COLS
            row = [str(data.get(col, "")) for col in PATIENT_METADATA_COLS]
            self.metadata_sheet.append_row(row)
        except Exception as e:
            print(f"[SheetsManager] Error appending metadata: {e}")

    def append_result(self, data: dict):
        """Appends a row to the results sheet."""
        if not self.is_connected or not self.results_sheet: return
        try:
            from csv_manager import CLINICAL_RESULTS_COLS
            row = [str(data.get(col, "")) for col in CLINICAL_RESULTS_COLS]
            self.results_sheet.append_row(row)
        except Exception as e:
            print(f"[SheetsManager] Error appending result: {e}")

    def append_raw_data(self, rows: list):
        """Appends multiple rows to the raw data sheet."""
        if not self.is_connected or not self.raw_data_sheet: return
        try:
            # Batch updates are better, but simple append_rows might be supported in newer gspread
            # or we loop. 'append_rows' is available in gspread v5.
            from csv_manager import RAW_SCAN_DATA_COLS
            
            # Convert dicts to lists
            formatted_rows = []
            for item in rows:
                formatted_rows.append([str(item.get(col, "")) for col in RAW_SCAN_DATA_COLS])
            
            self.raw_data_sheet.append_rows(formatted_rows)
        except Exception as e:
            print(f"[SheetsManager] Error appending raw data: {e}")

    def append_features(self, features: dict):
        """Appends a row to the features sheet."""
        if not self.is_connected or not self.features_sheet: return
        try:
            from csv_manager import INTERMEDIATE_FEATURES_COLS
            row = [str(features.get(col, "")) for col in INTERMEDIATE_FEATURES_COLS]
            self.features_sheet.append_row(row)
        except Exception as e:
            print(f"[SheetsManager] Error appending features: {e}")

    def update_status(self, visit_id: str, updates: dict):
        """Updates status columns for a specific visit_id."""
        if not self.is_connected or not self.metadata_sheet: return

        try:
            cell = self.metadata_sheet.find(visit_id)
            if not cell: return 
            
            row_idx = cell.row
            from csv_manager import PATIENT_METADATA_COLS
            
            for col_name, value in updates.items():
                if col_name in PATIENT_METADATA_COLS:
                    col_idx = PATIENT_METADATA_COLS.index(col_name) + 1 
                    self.metadata_sheet.update_cell(row_idx, col_idx, str(value))
                    
        except Exception as e:
            print(f"[SheetsManager] Error updating status: {e}")

# Global Instance
sheets_manager = SheetsManager()
