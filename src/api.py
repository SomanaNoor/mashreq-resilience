from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import json
import os
import csv
import io
from datetime import datetime

# Import pipeline components
import sys
sys.path.insert(0, os.path.dirname(__file__))

from simulation_engine import SimulationEngine
from guardrails import get_guardrails
from responsible_ai_pipeline import get_pipeline
from audit_logger import get_audit_logger

app = FastAPI(
    title="Mashreq Responsible AI API", 
    version="2.0",
    description="10-Stage Responsible AI Pipeline API"
)

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


# ============================================================================
# NEW RESPONSIBLE AI ENDPOINTS
# ============================================================================

class ProcessEventsRequest(BaseModel):
    events: List[Dict[str, Any]]

class HumanDecisionRequest(BaseModel):
    cluster_id: str
    decision: str  # APPROVED, DISMISSED, MORE_REVIEW
    user: str
    reason: Optional[str] = None


@app.get("/governance")
def get_governance():
    """Get governance guardrails and policy information."""
    guardrails = get_guardrails()
    return {
        "policy": guardrails.get_policy_text(),
        "boundaries": guardrails.get_boundaries(),
        "footer": guardrails.get_governance_footer(),
        "decision_banner": guardrails.get_decision_banner()
    }


@app.get("/governance/data-card")
def get_data_card():
    """Get the data card documentation."""
    card_path = "data/data_card.json"
    if os.path.exists(card_path):
        with open(card_path, 'r') as f:
            return json.load(f)
    return {"error": "Data card not found"}


@app.get("/governance/model-card")
def get_model_card():
    """Get the model card documentation."""
    card_path = "data/model_card.json"
    if os.path.exists(card_path):
        with open(card_path, 'r') as f:
            return json.load(f)
    return {"error": "Model card not found"}


@app.post("/pipeline/process")
def process_events(req: ProcessEventsRequest):
    """Process events through the 10-stage Responsible AI pipeline."""
    if not req.events:
        raise HTTPException(status_code=400, detail="No events provided")
    
    pipeline = get_pipeline()
    result = pipeline.process(req.events)
    
    # Convert cluster analyses to JSON-serializable format
    clusters = []
    for analysis in result.cluster_analyses:
        clusters.append(analysis.to_analyst_card())
    
    return {
        "governance_validated": result.governance_validated,
        "validation_issues": result.validation_issues,
        "gating": {
            "signal_count": result.gating_result.signal_count,
            "noise_count": result.gating_result.noise_count,
            "summary": result.gating_result.gating_summary
        },
        "clustering": {
            "cluster_count": result.clustering_result.cluster_count,
            "category_distribution": result.clustering_result.category_distribution
        },
        "clusters": clusters,
        "processing_time_ms": result.processing_time_ms,
        "timestamp": result.timestamp
    }


@app.post("/pipeline/run-from-csv")
def run_from_csv():
    """
    CRITICAL: Trigger strict 10-stage pipeline from the validated CSV.
    Ensures 'Synthetic Data Only' governance.
    """
    try:
        from data_loader import load_csv_events
        # Load directly from the governed source
        events = load_csv_events("data/synthetic_social_signals_mashreq.csv")
        
        # Process through pipeline
        pipeline = get_pipeline()
        result = pipeline.process(events)
        
        # Format for Analyst View
        clusters = [analysis.to_analyst_card() for analysis in result.cluster_analyses]
        
        return {
             "status": "success",
             "source": "synthetic_social_signals_mashreq.csv",
             "events_processed": len(events),
             "clusters_formed": len(clusters),
             "analyst_cards": clusters,
             "governance_check": result.governance_validated
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/pipeline/decision")
def log_human_decision(req: HumanDecisionRequest, x_role: str = "analyst"):
    """
    Log a human decision. Enforces RBAC.
    
    Headers:
        X-Role: 'analyst' | 'reviewer' | 'admin'
    """
    # 1. RBAC Check (Stage 10)
    from authz import validate_decision_authority
    if not validate_decision_authority(x_role, req.decision):
        raise HTTPException(
            status_code=403, 
            detail=f"Role '{x_role}' is not authorized to perform decision '{req.decision}'"
        )

    pipeline = get_pipeline()
    success = pipeline.log_human_decision(
        cluster_id=req.cluster_id,
        decision=req.decision,
        user=req.user,
        reason=req.reason
    )
    
    return {"status": "logged" if success else "failed", "cluster_id": req.cluster_id}


@app.get("/audit/records")
def get_audit_records(limit: int = 50):
    """Get recent audit records."""
    logger = get_audit_logger()
    return logger.get_recent_records(limit)


@app.get("/audit/stats")
def get_audit_stats():
    """Get audit log statistics."""
    logger = get_audit_logger()
    return logger.get_stats()


@app.get("/audit/export")
def export_audit_csv():
    """Export audit log as CSV."""
    logger = get_audit_logger()
    csv_data = logger.export_csv()
    
    return StreamingResponse(
        io.BytesIO(csv_data),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=audit_trail.csv"}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

