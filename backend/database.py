"""
PostgreSQL Database Layer for GlucoLumin
Primary storage with SQLAlchemy ORM
"""
import os
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager

# Database URL from environment variable (fallback for local dev)
DATABASE_URL = os.environ.get(
    "DATABASE_URL", 
    "postgresql://postgres:PYMfvqFNwvMULtUnXdwDmsWiiXrhZGGr@switchyard.proxy.rlwy.net:38500/railway"
)

# Create engine
engine = create_engine(DATABASE_URL, pool_pre_ping=True, pool_recycle=300)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ============== MODELS ==============

class PatientMetadata(Base):
    """Patient visit records"""
    __tablename__ = "patient_metadata"
    
    id = Column(Integer, primary_key=True, index=True)
    visit_id = Column(String(50), unique=True, index=True, nullable=False)
    patient_id = Column(String(50), index=True)
    name = Column(String(200))
    age = Column(Integer)
    sex = Column(String(20))
    height_cm = Column(Float)
    weight_kg = Column(Float)
    bmi = Column(Float)
    skin_tone = Column(String(50))
    blood_pressure = Column(String(20))
    had_food = Column(String(10))
    family_diabetic_history = Column(String(10))
    timestamp = Column(DateTime, default=datetime.utcnow)
    raw_scan_id = Column(String(100))
    ml1_status = Column(String(20), default="PENDING")
    ml2_status = Column(String(20), default="PENDING")
    final_glucose = Column(Float, nullable=True)
    result_flag = Column(String(50), nullable=True)
    diet_advice = Column(Text, nullable=True)


class RawScanData(Base):
    """Raw sensor readings"""
    __tablename__ = "raw_scan_data"
    
    id = Column(Integer, primary_key=True, index=True)
    visit_id = Column(String(50), index=True, nullable=False)
    sample_index = Column(String(20))
    signal_value = Column(String(50))


class IntermediateFeatures(Base):
    """ML extracted features"""
    __tablename__ = "intermediate_features"
    
    id = Column(Integer, primary_key=True, index=True)
    visit_id = Column(String(50), unique=True, index=True, nullable=False)
    feat_mean = Column(Float, default=0)
    feat_std = Column(Float, default=0)
    feat_rms = Column(Float, default=0)
    fft_peak1_power = Column(Float, default=0)
    fft_peak2_power = Column(Float, default=0)
    spectral_entropy = Column(Float, default=0)
    wavelet_energy_low = Column(Float, default=0)
    wavelet_energy_mid = Column(Float, default=0)
    wavelet_energy_high = Column(Float, default=0)
    autoencoder_recon_error = Column(Float, default=0)
    skin_tone_encoded = Column(Float, default=0)


class ClinicalResult(Base):
    """Final glucose results"""
    __tablename__ = "clinical_results"
    
    id = Column(Integer, primary_key=True, index=True)
    visit_id = Column(String(50), unique=True, index=True, nullable=False)
    patient_id = Column(String(50))
    glucose_mg_dl = Column(Float)
    classification = Column(String(50))
    diet_advice = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)


# ============== DATABASE FUNCTIONS ==============

def create_tables():
    """Create all tables if they don't exist"""
    try:
        Base.metadata.create_all(bind=engine)
        print("[Database] Tables created/verified successfully")
    except Exception as e:
        print(f"[Database] Error creating tables: {e}")
        raise


@contextmanager
def get_db() -> Session:
    """Database session context manager"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def add_patient_metadata(data: Dict[str, Any]) -> bool:
    """Add patient metadata to database"""
    try:
        with get_db() as db:
            # Convert timestamp string to datetime if needed
            if 'timestamp' in data and isinstance(data['timestamp'], str):
                try:
                    data['timestamp'] = datetime.fromisoformat(data['timestamp'])
                except:
                    data['timestamp'] = datetime.utcnow()
            
            patient = PatientMetadata(
                visit_id=data.get('visit_id'),
                patient_id=data.get('patient_id'),
                name=data.get('name'),
                age=data.get('age'),
                sex=data.get('sex'),
                height_cm=data.get('height_cm'),
                weight_kg=data.get('weight_kg'),
                bmi=data.get('bmi'),
                skin_tone=data.get('skin_tone'),
                blood_pressure=data.get('blood_pressure'),
                had_food=data.get('had_food'),
                family_diabetic_history=data.get('family_diabetic_history'),
                timestamp=data.get('timestamp', datetime.utcnow()),
                raw_scan_id=data.get('raw_scan_id', ''),
                ml1_status=data.get('ml1_status', 'PENDING'),
                ml2_status=data.get('ml2_status', 'PENDING'),
                final_glucose=data.get('final_glucose'),
                result_flag=data.get('result_flag'),
                diet_advice=data.get('diet_advice')
            )
            db.add(patient)
            db.commit()
            print(f"[Database] Added patient metadata: {data.get('visit_id')}")
            return True
    except Exception as e:
        print(f"[Database] Error adding patient metadata: {e}")
        return False


def add_raw_data(rows: List[Dict[str, Any]]) -> bool:
    """Add raw scan data to database (bulk insert)"""
    if not rows:
        return True
    try:
        with get_db() as db:
            for row in rows:
                scan = RawScanData(
                    visit_id=row.get('visit_id'),
                    sample_index=str(row.get('sample_index', '')),
                    signal_value=str(row.get('signal_value', ''))
                )
                db.add(scan)
            db.commit()
            print(f"[Database] Added {len(rows)} raw scan records")
            return True
    except Exception as e:
        print(f"[Database] Error adding raw data: {e}")
        return False


def update_patient_status(visit_id: str, updates: Dict[str, Any]) -> bool:
    """Update patient metadata fields"""
    try:
        with get_db() as db:
            patient = db.query(PatientMetadata).filter(
                PatientMetadata.visit_id == visit_id
            ).first()
            
            if patient:
                for key, value in updates.items():
                    if hasattr(patient, key):
                        setattr(patient, key, value)
                db.commit()
                print(f"[Database] Updated patient {visit_id}: {list(updates.keys())}")
                return True
            else:
                print(f"[Database] Patient not found: {visit_id}")
                return False
    except Exception as e:
        print(f"[Database] Error updating patient: {e}")
        return False


def add_features(visit_id: str, features: Dict[str, Any]) -> bool:
    """Save extracted features"""
    try:
        with get_db() as db:
            feat = IntermediateFeatures(
                visit_id=visit_id,
                feat_mean=features.get('feat_mean', 0),
                feat_std=features.get('feat_std', 0),
                feat_rms=features.get('feat_rms', 0),
                fft_peak1_power=features.get('fft_peak1_power', 0),
                fft_peak2_power=features.get('fft_peak2_power', 0),
                spectral_entropy=features.get('spectral_entropy', 0),
                wavelet_energy_low=features.get('wavelet_energy_low', 0),
                wavelet_energy_mid=features.get('wavelet_energy_mid', 0),
                wavelet_energy_high=features.get('wavelet_energy_high', 0),
                autoencoder_recon_error=features.get('autoencoder_recon_error', 0),
                skin_tone_encoded=features.get('skin_tone_encoded', 0)
            )
            db.add(feat)
            db.commit()
            print(f"[Database] Added features for: {visit_id}")
            return True
    except Exception as e:
        print(f"[Database] Error adding features: {e}")
        return False


def add_clinical_result(result: Dict[str, Any]) -> bool:
    """Save clinical result"""
    try:
        with get_db() as db:
            # Convert timestamp if needed
            ts = result.get('timestamp')
            if isinstance(ts, str):
                try:
                    ts = datetime.fromisoformat(ts)
                except:
                    ts = datetime.utcnow()
            
            clinical = ClinicalResult(
                visit_id=result.get('visit_id'),
                patient_id=result.get('patient_id'),
                glucose_mg_dl=result.get('glucose_mg_dl'),
                classification=result.get('classification'),
                diet_advice=result.get('diet_advice'),
                timestamp=ts or datetime.utcnow()
            )
            db.add(clinical)
            db.commit()
            print(f"[Database] Added clinical result: {result.get('visit_id')}")
            return True
    except Exception as e:
        print(f"[Database] Error adding clinical result: {e}")
        return False


def get_patient_metadata(visit_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve patient metadata"""
    try:
        with get_db() as db:
            patient = db.query(PatientMetadata).filter(
                PatientMetadata.visit_id == visit_id
            ).first()
            
            if patient:
                return {
                    'visit_id': patient.visit_id,
                    'patient_id': patient.patient_id,
                    'name': patient.name,
                    'age': patient.age,
                    'sex': patient.sex,
                    'height_cm': patient.height_cm,
                    'weight_kg': patient.weight_kg,
                    'bmi': patient.bmi,
                    'skin_tone': patient.skin_tone,
                    'blood_pressure': patient.blood_pressure,
                    'had_food': patient.had_food,
                    'family_diabetic_history': patient.family_diabetic_history,
                    'timestamp': patient.timestamp.isoformat() if patient.timestamp else None,
                    'raw_scan_id': patient.raw_scan_id,
                    'ml1_status': patient.ml1_status,
                    'ml2_status': patient.ml2_status,
                    'final_glucose': patient.final_glucose,
                    'result_flag': patient.result_flag,
                    'diet_advice': patient.diet_advice
                }
            return None
    except Exception as e:
        print(f"[Database] Error getting patient metadata: {e}")
        return None


def get_raw_data(visit_id: str) -> List[Dict[str, Any]]:
    """Retrieve raw scan data for a visit"""
    try:
        with get_db() as db:
            rows = db.query(RawScanData).filter(
                RawScanData.visit_id == visit_id
            ).all()
            
            return [
                {
                    'visit_id': row.visit_id,
                    'sample_index': row.sample_index,
                    'signal_value': row.signal_value
                }
                for row in rows
            ]
    except Exception as e:
        print(f"[Database] Error getting raw data: {e}")
        return []
