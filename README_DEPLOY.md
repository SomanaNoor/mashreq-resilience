# 🚀 Deployment Guide: Mashreq Responsible AI

The system has been packaged for local deployment.

## 🟢 Quick Start

Double-click the **`run_app.bat`** file in this directory.

This will automatically:
1.  Launch the **FastAPI Backend** on `http://localhost:8000`
2.  Launch the **Streamlit Dashboard** on `http://localhost:8501` and open it in your default browser.

---

## 🔧 Manual Startup

If you prefer running components individually via terminal:

### 1. Start Backend API
```bash
cd src
uvicorn api:app --reload
```

### 2. Start Dashboard UI
```bash
cd src
streamlit run dashboard.py
```

## 📋 System Requirements
- Python 3.8+
- Dependencies installed (`pip install -r requirements.txt`)
- Network ports 8000 (API) and 8501 (Dashboard) must be free.
