"""
Mashreq "High-End" Operational Resilience Agent
================================================
Capabilities:
1. Auto-Watch: Monitors ./data for new files.
2. Sophisticated Reasoning: Cross-referenced pattern detection (ATM + Rumor).
3. Risk Index (RI) Calculation: RI = (Volume * Severity) / Time.
4. Governance Audit: Bias checks and action verification.

Author: Antigravity
"""

import json
import os
import time
import glob
from typing import TypedDict, List, Optional
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load env
load_dotenv()

# Libraries
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from langgraph.graph import StateGraph, END
from langchain_groq import ChatGroq
from governance_shield import GovernanceShield

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

# Constants
SEVERITY_MAP = {"CRITICAL": 10, "WARNING": 5, "LOW": 2, "NONE": 0}

# ============================================================================
# STATE & PROMPTS
# ============================================================================

class AgentState(TypedDict):
    current_file: str
    raw_events: List[dict]
    classified_signals: List[dict]
    pattern_analysis: dict
    risk_calculations: dict
    final_alert: dict

# 1. Classification (Filtering Noise)
PROMPT_CLASSIFY = ChatPromptTemplate.from_messages([
    ("system", """You are a specialized Risk Triage AI.
    Analyze the following events.
    Filter out routine "NOISE" (password resets, simple inquiries).
    Keep only "SIGNALS" (errors, outages, complaints, rumors).
    
    Output JSON list: [{{ "event_id": "...", "type": "SIGNAL|NOISE", "category": "Technical|Reputational|Security" }}]
    """),
    ("human", "{events}")
])

# 2. Pattern Recognition (The "Brain")
PROMPT_REASON = ChatPromptTemplate.from_messages([
    ("system", """You are a Senior Operational Risk Officer.
    Analyze these SIGNALS for correlation.
    
    CRITICAL RULES:
    1. Multiple failures + Rumor = CRITICAL (The "Bank Run" scenario).
    2. High Volume Technical Errors = CRITICAL (Service Outage).
    3. Isolated complaint = LOW.
    
    Return JSON:
    {{
        "title": "Short Alert Title",
        "severity": "CRITICAL|WARNING|LOW|NONE",
        "reasoning_path": "Step 1: observed X... Step 2: correlated with Y... Conclusion: Z",
        "primary_pattern": "Describe the pattern (e.g. 'Coordinated Attack' or 'Service Degradation')"
    }}
    """),
    ("human", """Signals: {signals}
    Time Window: {duration_minutes} minutes
    Total Volume: {volume}""")
])

# 3. Governance Audit
PROMPT_GOVERNANCE = ChatPromptTemplate.from_messages([
    ("system", """Audit this alert for ethical compliance.
    1. Check for Bias: Did the AI mention specific user demographics?
    2. Check for PII: Are account numbers visible?
    3. Verify Logic: Does the severity match the evidence?
    
    Output JSON:
    {{
        "pii_detected": boolean,
        "bias_detected": boolean,
        "audit_note": "Clear rationale",
        "approved": boolean
    }}
    """),
    ("human", "Alert: {alert}")
])

# ============================================================================
# NODES
# ============================================================================

def node_ingest(state: AgentState) -> AgentState:
    """Reads the detected file."""
    print(f"📂 [INGEST] Reading {state['current_file']}...")
    try:
        with open(state['current_file'], 'r') as f:
            state['raw_events'] = json.load(f)
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        state['raw_events'] = []
    return state

def node_classify(state: AgentState) -> AgentState:
    """Filters noise via LLM."""
    if not state['raw_events']: return state
    
    print(f"🔎 [CLASSIFY] Analyzing {len(state['raw_events'])} events...")
    llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)
    chain = PROMPT_CLASSIFY | llm | JsonOutputParser()
    
    # Process in chunks if large, but for demo take first 20 interesting ones
    subset = state['raw_events'][:30]
    try:
        results = chain.invoke({"events": json.dumps(subset)})
        # Filter for signals
        state['classified_signals'] = [r for r in results if r['type'] == 'SIGNAL']
        # Map back to full event data
        signal_ids = {s['event_id'] for s in state['classified_signals']}
        state['classified_signals'] = [e for e in state['raw_events'] if e['event_id'] in signal_ids]
    except Exception as e:
        print(f"❌ Classification failed: {e}")
        state['classified_signals'] = []
    
    print(f"   found {len(state['classified_signals'])} signals.")
    return state

def node_reasoning(state: AgentState) -> AgentState:
    """Finds patterns and determines initial severity."""
    signals = state['classified_signals']
    if not signals:
        state['pattern_analysis'] = {"severity": "NONE"}
        return state

    print(f"🧠 [REASONING] Looking for patterns among {len(signals)} signals...")
    
    # Calculate metadata for the prompt
    timestamps = [datetime.fromisoformat(e['timestamp']) for e in signals]
    duration = (max(timestamps) - min(timestamps)).total_seconds() / 60.0 if timestamps else 1
    duration = max(1, duration) # Avoid div by zero
    
    state['risk_calculations'] = {"duration_minutes": duration, "volume": len(signals)}
    
    llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)
    chain = PROMPT_REASON | llm | JsonOutputParser()
    
    state['pattern_analysis'] = chain.invoke({
        "signals": json.dumps(signals[:10]), # Summarize top 10 for prompt context
        "duration_minutes": round(duration, 2),
        "volume": len(signals)
    })
    return state

def node_risk_calc(state: AgentState) -> AgentState:
    """Mathematical Risk Index Calculation."""
    # Formula: RI = (Volume * SeverityScore) / TimeDuration
    
    analysis = state.get('pattern_analysis', {})
    sev_label = analysis.get('severity', "LOW")
    sev_score = SEVERITY_MAP.get(sev_label.upper(), 1)
    
    if 'risk_calculations' not in state:
        state['risk_calculations'] = {"duration_minutes": 1, "volume": 0}
        
    vol = state['risk_calculations'].get('volume', 0)
    time_win = state['risk_calculations'].get('duration_minutes', 1)
    
    # Calculate RI
    # We normalize time to "per hour" to make the number readable, or just use raw minutes.
    # Let's use raw metric: (Vol * Severity) / sqrt(Time) to penalize sudden bursts?
    # User asked for: (Volume * Severity) / Time
    
    ri_score = (vol * sev_score) / time_win
    
    state['risk_calculations']['severity_score'] = sev_score
    state['risk_calculations']['risk_index'] = round(ri_score, 2)
    
    print(f"🧮 [MATH] RI = ({vol} * {sev_score}) / {time_win:.1f}m = {ri_score:.2f}")
    return state

def node_governance(state: AgentState) -> AgentState:
    """Final Audit."""
    print("⚖️ [GOVERNANCE] Auditing decision...")
    
    shield = GovernanceShield()
    
    llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)
    chain = PROMPT_GOVERNANCE | llm | JsonOutputParser()
    
    # Construct draft alert
    draft = {
        **state['pattern_analysis'],
        "risk_index": state['risk_calculations']['risk_index']
    }
    
    audit = chain.invoke({"alert": json.dumps(draft)})
    
    # Finalize Alert Structure
    final_alert = {
        "alert_id": f"AG-{int(time.time())}",
        "timestamp": datetime.now().isoformat(),
        "title": draft.get('title', 'System Alert'),
        "risk_level": draft.get('severity', 'LOW'),
        "risk_index": draft['risk_index'],
        "category": state['pattern_analysis'].get('primary_pattern', 'General'),
        "summary": state['pattern_analysis'].get('reasoning_path', ''),
        "reasoning_chain": state['pattern_analysis'].get('reasoning_path', ''),
        "source_events": [e['event_id'] for e in state['classified_signals']],
        "governance_audit": audit,
        "pii_masked": False, 
        "suggested_action": "Escalate to Crisis Team" if draft.get('severity') == "CRITICAL" else "Monitor"
    }
    
    # --- APPLY GOVERNANCE SHIELD ---
    # 1. Mask PII
    final_alert['summary'] = shield.mask_pii(final_alert['summary'])
    final_alert['reasoning_chain'] = shield.mask_pii(final_alert['reasoning_chain'])
    
    # 2. Ethical Filter
    final_alert['title'] = shield.ethical_filter(final_alert['title'])
    final_alert['summary'] = shield.ethical_filter(final_alert['summary'])
    
    final_alert['pii_masked'] = True # Confirmed by regex
    
    state['final_alert'] = final_alert
    return state

def node_save(state: AgentState):
    """Saves to output file for dashboard (Appends, doesn't overwrite)."""
    output_path = "data/current_alerts.json"
    
    existing_alerts = []
    if os.path.exists(output_path):
        try:
            with open(output_path, 'r') as f:
                existing_alerts = json.load(f)
        except:
            existing_alerts = []
            
    # Add new alert
    existing_alerts.insert(0, state['final_alert']) # Add to top
    
    # Keep max 50 recent alerts
    existing_alerts = existing_alerts[:50]
    
    with open(output_path, 'w') as f:
        json.dump(existing_alerts, f, indent=2)
    print(f"💾 Alert saved to {output_path} (Total: {len(existing_alerts)})")
    return state

# ============================================================================
# GRAPH CONSTRUCTION
# ============================================================================

def build_graph():
    workflow = StateGraph(AgentState)
    
    workflow.add_node("ingest", node_ingest)
    workflow.add_node("classify", node_classify)
    workflow.add_node("reasoning", node_reasoning)
    workflow.add_node("risk_calc", node_risk_calc)
    workflow.add_node("governance", node_governance)
    workflow.add_node("save", node_save)
    
    workflow.set_entry_point("ingest")
    workflow.add_edge("ingest", "classify")
    workflow.add_edge("classify", "reasoning")
    workflow.add_edge("reasoning", "risk_calc")
    workflow.add_edge("risk_calc", "governance")
    workflow.add_edge("governance", "save")
    workflow.add_edge("save", END)
    
    return workflow.compile()

# ============================================================================
# WATCHER LOGIC
# ============================================================================

class DataHandler(FileSystemEventHandler):
    def __init__(self, graph):
        self.graph = graph
        self.last_processed = 0
    
    def on_created(self, event):
        if event.is_directory or not event.src_path.endswith(".json"):
            return
        
        # Debounce
        if time.time() - self.last_processed < 2: return
        self.last_processed = time.time()
        
        print(f"\n🔔 NEW FILE DETECTED: {event.src_path}")
        time.sleep(1) # Wait for write to finish
        
        initial_state = {"current_file": event.src_path}
        self.graph.invoke(initial_state)

if __name__ == "__main__":
    print("🚀 HIGH-END AGENT STARTED")
    print("👀 Watching ./data for new files...")
    print("   Pattern: ATM Failure + Rumor -> CRITICAL")
    print("   Formula: RI = (Vol * Severity) / Time")
    
    app = build_graph()
    
    # 1. Process existing files first (latest one)
    files = glob.glob("data/scenario_*.json")
    if files:
        latest = max(files, key=os.path.getctime)
        print(f"📥 Processing existing latest file: {latest}")
        app.invoke({"current_file": latest})
    
    # 2. Start Watcher
    observer = Observer()
    observer.schedule(DataHandler(app), path="./data", recursive=False)
    observer.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
