from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
import os
import csv
from datetime import datetime
from .simulation_engine import SimulationEngine

app = FastAPI(title="Mashreq Resilience API", version="1.0")

# Allow CORS for Next.js (usually runs on port 3000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict to frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Data Schemas ---
class SimulationRequest(BaseModel):
    interest_rate_bps: int
    downtime_minutes: int
    regulatory_fine_mm: float
    market_volatility_vix: float
    cyber_breach_cost_mm: float

class AuditAction(BaseModel):
    alert_id: str
    action: str # "ESCALATED", "DISMISSED", "RESOLVED"
    context: str

# --- Endpoints ---

@app.get("/health")
def health_check():
    return {"status": "nominal", "timestamp": datetime.now().isoformat()}

@app.get("/alerts")
def get_alerts():
    """Fetch all active alerts from the JSON store."""
    data_path = "data/current_alerts.json"
    if not os.path.exists(data_path):
        return []
    try:
        with open(data_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/audit")
def log_audit(action: AuditAction):
    """Log a human decision to the immutable audit trail."""
    csv_file = "data/audit_trail.csv"
    file_exists = os.path.isfile(csv_file)
    try:
        with open(csv_file, mode='a', newline='') as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(["Timestamp", "User", "Action", "AlertID", "AI_Context"])
            writer.writerow([
                datetime.now().isoformat(),
                "Risk_Officer_API",
                action.action,
                action.alert_id,
                action.context
            ])
        return {"status": "logged"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/simulate")
def run_simulation(req: SimulationRequest):
    """Run the Monte Carlo Simulation Engine."""
    sim = SimulationEngine(iterations=5000)
    result = sim.run_simulation(
        req.interest_rate_bps,
        req.downtime_minutes,
        req.regulatory_fine_mm,
        req.market_volatility_vix,
        req.cyber_breach_cost_mm
    )
    
    # Numpy arrays aren't JSON serializable directy
    return {
        "breach_probability": result['breach_probability'],
        "mean_impact": result['mean_impact'],
        "var_95": result['var_95'],
        "is_breach": bool(result['is_breach']),
        # Return a sample or histogram buckets to reduce payload size? 
        # For now, let's return a sample of 500 points for the chart
        "simulation_sample": result['simulation_data'].tolist()[:500] 
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
