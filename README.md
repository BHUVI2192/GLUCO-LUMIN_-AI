# 🩺 GlucoLumin AI

**Non-Invasive Glucose Monitoring System powered by Machine Learning**

GlucoLumin AI is a cutting-edge clinical validation system that predicts blood glucose levels using non-invasive sensor technology combined with advanced machine learning algorithms.

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python)
![Next.js](https://img.shields.io/badge/Next.js-16+-black?logo=next.js)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-009688?logo=fastapi)
![License](https://img.shields.io/badge/License-MIT-green)

---

## 📋 Table of Contents

- [Features](#-features)
- [Architecture](#-architecture)
- [Tech Stack](#-tech-stack)
- [Project Structure](#-project-structure)
- [Installation](#-installation)
- [Usage](#-usage)
- [API Endpoints](#-api-endpoints)
- [ML Pipeline](#-ml-pipeline)
- [Contributing](#-contributing)
- [License](#-license)

---

## ✨ Features

- **Non-Invasive Monitoring**: Uses optical sensor technology for painless glucose measurement
- **2-Stage ML Pipeline**: Advanced signal processing combined with patient-specific glucose prediction
- **Real-Time Processing**: Fast prediction with continuous monitoring support
- **Patient Management**: Complete patient registration and visit tracking
- **Clinical Reports**: Automatic classification (Normal, Low, High) with personalized diet advice
- **Web Serial API**: Direct hardware communication through the browser
- **Mobile-First Design**: Responsive interface optimized for clinical use

---

## 🏗 Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        GlucoLumin AI                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   ┌──────────────┐    ┌──────────────┐    ┌──────────────┐     │
│   │   Frontend   │───▶│   Backend    │───▶│  ML Pipeline │     │
│   │  (Next.js)   │    │  (FastAPI)   │    │ (LinearReg)  │     │
│   └──────────────┘    └──────────────┘    └──────────────┘     │
│          │                   │                   │              │
│          ▼                   ▼                   ▼              │
│   ┌──────────────┐    ┌──────────────┐    ┌──────────────┐     │
│   │  Web Serial  │    │  CSV Storage │    │   Trained    │     │
│   │     API      │    │   Manager    │    │    Model     │     │
│   └──────────────┘    └──────────────┘    └──────────────┘     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🛠 Tech Stack

### Backend
- **FastAPI** - High-performance Python web framework
- **Uvicorn** - ASGI server
- **Pandas & NumPy** - Data processing
- **Scikit-learn** - Machine learning (Linear Regression)
- **SciPy** - Signal processing & wavelet analysis
- **PyWavelets** - Wavelet decomposition

### Frontend
- **Next.js 16** - React framework
- **TypeScript** - Type-safe JavaScript
- **Tailwind CSS** - Utility-first styling
- **Lucide React** - Icon library
- **Web Serial API** - Hardware communication

---

## 📁 Project Structure

```
GLUCO LUMIN AI/
├── backend/
│   ├── main.py              # FastAPI application & endpoints
│   ├── ml_pipeline.py       # 2-Stage ML processing pipeline
│   ├── csv_manager.py       # CSV data persistence layer
│   ├── sheets_manager.py    # Google Sheets integration
│   ├── requirements.txt     # Python dependencies
│   ├── patient_metadata.csv # Patient records
│   ├── raw_scan_data.csv    # Raw sensor readings
│   └── clinical_results.csv # Final predictions
│
├── frontend/
│   ├── app/
│   │   ├── page.tsx         # Main application page
│   │   ├── layout.tsx       # Root layout
│   │   └── globals.css      # Global styles
│   ├── hooks/               # Custom React hooks
│   ├── lib/                 # Utility functions
│   ├── package.json         # Node.js dependencies
│   └── tailwind.config.ts   # Tailwind configuration
│
└── README.md
```

---

## 🚀 Installation

### Prerequisites
- Python 3.10+
- Node.js 18+
- npm or yarn

### Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install additional dependencies for signal processing
pip install pywavelets joblib
```

### Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Or using yarn
yarn install
```

---

## 💻 Usage

### Start Backend Server

```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The backend will be available at `http://localhost:8000`

### Start Frontend Development Server

```bash
cd frontend
npm run dev
```

The frontend will be available at `http://localhost:3000`

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Health check |
| `POST` | `/api/start_scan` | Register new patient & start scan |
| `POST` | `/api/upload_raw` | Upload raw sensor data |
| `GET` | `/api/get_result/{visit_id}` | Retrieve prediction results |

### Example: Start Scan

```json
POST /api/start_scan
{
  "patient_name": "John Doe",
  "patient_age": 35,
  "gender": "Male",
  "height_cm": 175.0,
  "weight_kg": 70.0,
  "skin_tone": "Medium",
  "blood_pressure": "120/80",
  "had_food": "No",
  "family_diabetic_history": "No"
}
```

### Example: Response

```json
{
  "visit_id": "V20260203_A1B2C3",
  "status": "registered"
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

## 🧪 Testing

### Run ML Pipeline Tests

```bash
cd backend
python ml_pipeline.py --test
```

### Manual API Testing

```bash
# Health check
curl http://localhost:8000/

# Start a scan
curl -X POST http://localhost:8000/api/start_scan \
  -H "Content-Type: application/json" \
  -d '{"patient_name":"Test User","patient_age":30,"height_cm":170,"weight_kg":65,"skin_tone":"Medium","blood_pressure":"120/80","had_food":"No","family_diabetic_history":"No"}'
```

---

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 👥 Team

**GlucoLumin AI** - Revolutionizing diabetes management through non-invasive technology.

---

<p align="center">
  Made with ❤️ for Healthcare Innovation
</p>
