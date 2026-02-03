# 🩺 GlucoLumin AI - Backend API

**Non-Invasive Glucose Monitoring System powered by Machine Learning**

GlucoLumin AI is a cutting-edge clinical validation system that predicts blood glucose levels using non-invasive sensor technology combined with advanced machine learning algorithms.

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-009688?logo=fastapi)
![Railway](https://img.shields.io/badge/Railway-Deployed-blueviolet?logo=railway)
![License](https://img.shields.io/badge/License-MIT-green)

---

## 📋 Table of Contents

- [Features](#-features)
- [Architecture](#-architecture)
- [Tech Stack](#-tech-stack)
- [Project Structure](#-project-structure)
- [Installation](#-installation)
- [Deployment](#-deployment)
- [API Endpoints](#-api-endpoints)
- [ML Pipeline](#-ml-pipeline)
- [License](#-license)

---

## ✨ Features

- **Non-Invasive Monitoring**: Uses optical sensor technology for painless glucose measurement
- **2-Stage ML Pipeline**: Advanced signal processing combined with patient-specific glucose prediction
- **Real-Time Processing**: Fast prediction with continuous monitoring support
- **Patient Management**: Complete patient registration and visit tracking
- **Clinical Reports**: Automatic classification (Normal, Low, High) with personalized diet advice
- **REST API**: Clean, documented endpoints for easy integration

---

## 🏗 Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    GlucoLumin AI Backend                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   ┌──────────────┐    ┌──────────────┐    ┌──────────────┐     │
│   │   FastAPI    │───▶│  ML Pipeline │───▶│   Results    │     │
│   │   Server     │    │ (LinearReg)  │    │   Storage    │     │
│   └──────────────┘    └──────────────┘    └──────────────┘     │
│          │                   │                   │              │
│          ▼                   ▼                   ▼              │
│   ┌──────────────┐    ┌──────────────┐    ┌──────────────┐     │
│   │  Endpoints   │    │   Trained    │    │     CSV      │     │
│   │  /api/*      │    │    Model     │    │   Manager    │     │
│   └──────────────┘    └──────────────┘    └──────────────┘     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🛠 Tech Stack

- **FastAPI** - High-performance Python web framework
- **Uvicorn** - ASGI server
- **Pandas & NumPy** - Data processing
- **Scikit-learn** - Machine learning (Linear Regression)
- **SciPy** - Signal processing & wavelet analysis
- **PyWavelets** - Wavelet decomposition

---

## 📁 Project Structure

```
GLUCO-LUMIN_-AI/
├── backend/
│   ├── main.py              # FastAPI application & endpoints
│   ├── ml_pipeline.py       # 2-Stage ML processing pipeline
│   ├── csv_manager.py       # CSV data persistence layer
│   ├── sheets_manager.py    # Google Sheets integration
│   └── requirements.txt     # Python dependencies
│
├── Procfile                 # Railway deployment config
├── railway.json             # Railway settings
└── README.md
```

---

## 🚀 Installation

### Prerequisites
- Python 3.10+

### Local Setup

```bash
# Clone the repository
git clone https://github.com/BHUVI2192/GLUCO-LUMIN_-AI.git
cd GLUCO-LUMIN_-AI

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
cd backend
pip install -r requirements.txt

# Run the server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

---

## 🚂 Deployment (Railway)

This project is configured for easy deployment on Railway:

1. **Fork/Clone** this repository
2. **Connect** to Railway via GitHub
3. **Deploy** - Railway will automatically detect the configuration

Railway will use the `Procfile` and `railway.json` for deployment settings.

### Environment Variables (Optional)
No environment variables required for basic functionality.

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Health check |
| `POST` | `/api/start_scan` | Register new patient & start scan |
| `POST` | `/api/upload_raw` | Upload raw sensor data |
| `GET` | `/api/get_result/{visit_id}` | Retrieve prediction results |

### Health Check

```bash
curl https://your-app.railway.app/
```

Response:
```json
{
  "message": "GlucoLumin AI Backend is Running",
  "status": "active"
}
```

### Start Scan

```bash
curl -X POST https://your-app.railway.app/api/start_scan \
  -H "Content-Type: application/json" \
  -d '{
    "patient_name": "John Doe",
    "patient_age": 35,
    "gender": "Male",
    "height_cm": 175.0,
    "weight_kg": 70.0,
    "skin_tone": "Medium",
    "blood_pressure": "120/80",
    "had_food": "No",
    "family_diabetic_history": "No"
  }'
```

Response:
```json
{
  "visit_id": "V20260203_A1B2C3",
  "status": "registered"
}
```

### Upload Raw Data

```bash
curl -X POST https://your-app.railway.app/api/upload_raw \
  -H "Content-Type: application/json" \
  -d '{
    "lines": [
      "V20260203_A1B2C3,0,95.2",
      "V20260203_A1B2C3,1,94.8",
      "V20260203_A1B2C3,2,95.5"
    ]
  }'
```

### Get Result

```bash
curl https://your-app.railway.app/api/get_result/V20260203_A1B2C3
```

Response:
```json
{
  "visit_id": "V20260203_A1B2C3",
  "status": "DONE",
  "glucose": 94.5,
  "classification": "Normal",
  "diet_advice": "NORMAL: Maintain balanced diet.",
  "timestamp": "2026-02-03T16:30:00"
}
```

---

## 🤖 ML Pipeline

GlucoLumin uses a **2-Stage Machine Learning Pipeline**:

### Stage 1: Signal Processing
- **Savitzky-Golay Filtering** - Noise reduction
- **FFT Analysis** - Frequency domain features
- **Wavelet Decomposition** - Multi-resolution analysis
- **Feature Extraction**: Mean, STD, RMS, Spectral Entropy, etc.

### Stage 2: Linear Regression Model
- Patient-specific adjustments based on:
  - Age, Gender, BMI
  - Blood Pressure (Systolic/Diastolic)
  - Skin Tone (calibration factor)
  - Fasting Duration
- Outputs glucose prediction in mg/dL

### Classification & Diet Advice

| Range (mg/dL) | Classification | Advice |
|---------------|----------------|--------|
| < 70 | Hypoglycemia | Eat fast-acting carbs immediately |
| 70-100 | Normal | Maintain balanced diet |
| 101-125 | Pre-Diabetic | Reduce sugar intake |
| 126-200 | High | Avoid white carbs/sugar |
| > 200 | Critical | Consult doctor immediately |

---

## 📄 License

This project is licensed under the MIT License.

---

<p align="center">
  Made with ❤️ for Healthcare Innovation
</p>
