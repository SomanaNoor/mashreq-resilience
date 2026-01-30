import streamlit as st
import json
import os
import time
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

import csv
from datetime import datetime
from simulation_engine import SimulationEngine


# ==============================================================================
# CONFIG & THEME
# ==============================================================================

st.set_page_config(
    page_title="Mashreq Command Center",
    page_icon="🟠",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Brand Colors (Mashreq Identity)
COLOR_BG = "#F8F9FA"  # Enterprise Light Gray
COLOR_CARD = "#FFFFFF"
COLOR_TEXT = "#0A0E17"
COLOR_MASHREQ_ORANGE = "#FF5E00" # Mashreq Orange
COLOR_MASHREQ_BLUE = "#1B4298"   # Secondary Corporate Blue
COLOR_GOLD = "#D4AF37"           # Premium/Wealth
COLOR_CRITICAL = "#D9534F"       # Soft Red for alerts

st.markdown(f"""
<style>
    /* Global Reset */
    .stApp {{
        background-color: {COLOR_BG};
        color: {COLOR_TEXT};
    }}
    
    /* Typography */
    h1, h2, h3 {{
        color: {COLOR_MASHREQ_BLUE} !important;
        font-family: 'Segoe UI', system-ui, sans-serif;
        text-transform: uppercase;
        font-weight: 700;
        letter-spacing: 0.5px;
    }}
    
    /* Card Design */
    .resilience-card {{
        background-color: {COLOR_CARD};
        border: 1px solid #E9ECEF;
        border-radius: 8px;
        padding: 24px;
        margin-bottom: 20px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05); /* Soft corporate shadow */
        transition: transform 0.2s ease;
    }}
    
    .war-room-card:hover {{
        transform: translateY(-2px);
        box-shadow: 0 8px 16px rgba(0,0,0,0.08);
    }}
    
    /* Pulse Animation for Critical */
    @keyframes pulse-orange {{
        0% {{ box-shadow: 0 0 0 0 rgba(255, 94, 0, 0.4); }}
        70% {{ box-shadow: 0 0 0 15px rgba(255, 94, 0, 0); }}
        100% {{ box-shadow: 0 0 0 0 rgba(255, 94, 0, 0); }}
    }}
    
    .critical-pulse {{
        border-left: 5px solid {COLOR_MASHREQ_ORANGE} !important;
        animation: pulse-orange 2s infinite;
    }}
    
    /* Governance Badges */
    .gov-badge {{
        padding: 6px 12px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.75rem;
        display: inline-block;
        margin-right: 8px;
        letter-spacing: 0.5px;
    }}
    
    .badge-green {{ 
        background-color: #E6F4EA; 
        color: #1E8E3E; 
        border: 1px solid #1E8E3E; 
    }}
    
    .badge-red {{ 
        background-color: #FCE8E6; 
        color: {COLOR_MASHREQ_ORANGE}; 
        border: 1px solid {COLOR_MASHREQ_ORANGE}; 
    }}
    
    /* Metrics */
    .metric-value {{
        font-size: 3rem;
        font-weight: 800;
        color: {COLOR_MASHREQ_ORANGE};
        margin-bottom: 0;
        line-height: 1;
    }}
    
    .metric-label {{
        font-size: 0.85rem;
        font-weight: 600;
        color: #6C757D;
        text-transform: uppercase;
    }}
    
    /* Buttons */
    div.stButton > button:first-child {{
        border-radius: 6px;
        font-weight: 600;
    }}
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# STATE & DATABASE
# ==============================================================================

if 'alerts_db' not in st.session_state:
    st.session_state['alerts_db'] = {}

DATA_FILE = "data/current_alerts.json"

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r') as f:
                new_alerts = json.load(f)
                # Keep most recent
                for alert in new_alerts:
                    aid = alert.get('alert_id')
                    if aid and aid not in st.session_state['alerts_db']:
                        alert['status'] = 'PENDING'
                        st.session_state['alerts_db'][aid] = alert
        except:
            pass

load_data()

# ==============================================================================
# SCENARIO STRESS TEST (SIDEBAR)
# ==============================================================================

with st.sidebar:
    st.markdown("## 🎲 STRESS TEST ENGINE")
    st.markdown("Adjust stress variables to forecast **Impact Tolerance Breach** probability.")
    
    with st.expander("Stress Variables", expanded=True):
        sim_rates = st.slider("Interest Rate (bps)", 0, 500, 100)
        sim_downtime = st.slider("Downtime (min)", 0, 1440, 60)
        sim_fines = st.slider("Reg. Fines ($MM)", 0.0, 100.0, 5.0)
        sim_vix = st.slider("Market Vol (VIX)", 10.0, 100.0, 20.0)
        sim_cyber = st.slider("Cyber Breach Cost ($MM)", 0.0, 50.0, 0.0)
        
    if st.button("RUN MONTE CARLO (5,000 RUNS)", type="primary"):
        sim_engine = SimulationEngine()
        results = sim_engine.run_simulation(
            sim_rates, sim_downtime, sim_fines, sim_vix, sim_cyber
        )
        st.session_state['sim_results'] = results
        st.rerun()

# ==============================================================================
# AUDIT LOGGING
# ==============================================================================

def log_audit(action, alert):
    csv_file = "data/audit_trail.csv"
    file_exists = os.path.isfile(csv_file)
    with open(csv_file, mode='a', newline='') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["Timestamp", "User", "Action", "AlertID", "AI_Context"])
        writer.writerow([
            datetime.now().isoformat(), "Risk_Officer_01", action, alert.get('alert_id'),
            f"Risk: {alert.get('risk_level')} | Reasoning: {alert.get('reasoning_chain')[:100]}..."
        ])

# ==============================================================================
# UI COMPONENTS
# ==============================================================================

def render_alert_card(alert):
    aid = alert['alert_id']
    status = alert.get('status', 'PENDING')
    risk = alert.get("risk_level", "LOW")
    conf = min(alert.get('risk_index', 0) * 10 + 50, 99)
    
    # Dynamic Badge Logic
    gov_badge = f"<div class='gov-badge badge-green'>✅ STANDARD CHECK (Conf: {conf:.0f}%)</div>"
    if conf < 80:
        gov_badge = f"<div class='gov-badge badge-red'>⚠️ HIGH OVERWATCH (Conf: {conf:.0f}%)</div>"
    
    border_color = COLOR_MASHREQ_ORANGE if risk == "CRITICAL" else COLOR_MASHREQ_BLUE
    
    with st.container():
        # Clean Enterprise Card
        st.markdown(f"""
        <div class='resilience-card {'critical-pulse' if risk == 'CRITICAL' else ''}' style='border-left: 5px solid {border_color}'>
        """, unsafe_allow_html=True)
        
        c1, c2 = st.columns([9, 3])
        with c1:
            st.markdown(f"### {alert.get('title')}")
            st.markdown(gov_badge + f" <span style='color:#6C757D; font-size:0.8rem; margin-left:10px;'>ID: {aid}</span>", unsafe_allow_html=True)
            st.markdown(f"**AI Reasoning:** <span style='color:{COLOR_TEXT}'>{alert.get('reasoning_chain')}</span>", unsafe_allow_html=True)
            
            # Show PII Masking Status
            if alert.get('pii_masked'):
                st.markdown(f"<span style='color:{COLOR_MASHREQ_ORANGE}; font-size:0.8rem;'>🔒 PII REDACTED BY GOVERNANCE SHIELD</span>", unsafe_allow_html=True)

        with c2:
            st.markdown(f"<div style='text-align:right; font-weight:bold; color:{COLOR_MASHREQ_BLUE}'>STATUS: {status}</div>", unsafe_allow_html=True)
            st.markdown("---")
            if status == 'PENDING':
                if st.button("🚨 ESCALATE", key=f"esc_{aid}", type="primary", use_container_width=True):
                    st.session_state['alerts_db'][aid]['status'] = 'ESCALATED'
                    log_audit("ESCALATE", alert)
                    st.rerun()
                if st.button("🛡️ DISMISS", key=f"dis_{aid}", use_container_width=True):
                    st.session_state['alerts_db'][aid]['status'] = 'DISMISSED'
                    log_audit("DISMISS", alert)
                    st.rerun()
            elif status == 'ESCALATED':
                st.info("Active Incident")
                if st.button("✅ RESOLVE", key=f"res_{aid}", use_container_width=True):
                     st.session_state['alerts_db'][aid]['status'] = 'RESOLVED'
                     log_audit("RESOLVE", alert)
                     st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

# ==============================================================================
# MAIN PAGE
# ==============================================================================

# Header
c1, c2 = st.columns([1, 15])
with c1:
    # Use a generic bank icon or Mashreq logo URL if verifiable (using text for safety)
    st.markdown(f"<div style='font-size:3rem;'>🟠</div>", unsafe_allow_html=True)
with c2:
    st.markdown(f"<h1>Mashreq <span style='color:{COLOR_MASHREQ_ORANGE}'>Resilience Core</span></h1>", unsafe_allow_html=True)
    st.markdown(f"**Enterprise Operational Risk Monitor** | Basel III Compliant | Singapore Governance Model")

st.markdown("---")

# KPI Row
k1, k2, k3, k4 = st.columns(4)
with k1:
     st.markdown(f"<div class='resilience-card'><div class='metric-label'>System Status</div><div class='metric-value' style='color:{COLOR_MASHREQ_BLUE}'>ONLINE</div></div>", unsafe_allow_html=True)
with k2:
    active_count = len([a for a in st.session_state['alerts_db'].values() if a['status'] == 'ESCALATED'])
    st.markdown(f"<div class='resilience-card'><div class='metric-label'>Active Risks</div><div class='metric-value' style='{'color:'+COLOR_MASHREQ_ORANGE if active_count > 0 else 'color:#1E8E3E'}'>{active_count}</div></div>", unsafe_allow_html=True)
with k3:
    # Quick Heatmap Mock
    st.markdown(f"<div class='resilience-card' style='padding:15px;'><div class='metric-label'>Regional Stress</div><div style='height:40px; background: linear-gradient(90deg, #E9ECEF 70%, {COLOR_MASHREQ_ORANGE} 100%); border-radius:4px; margin-top:10px;'></div><div style='font-size:0.7rem; text-align:right'>UAE Operations</div></div>", unsafe_allow_html=True)
with k4:
     st.markdown(f"<div class='resilience-card'><div class='metric-label'>Gov. Shield</div><div class='metric-value' style='font-size:1.5rem; color:{COLOR_GOLD}; padding-top:10px;'>ACTIVE 🔒</div></div>", unsafe_allow_html=True)

     st.markdown(f"<div class='resilience-card'><div class='metric-label'>Gov. Shield</div><div class='metric-value' style='font-size:1.5rem; color:{COLOR_GOLD}; padding-top:10px;'>ACTIVE 🔒</div></div>", unsafe_allow_html=True)


# ==============================================================================
# SIMULATION RESULTS (IF ACTIVE)
# ==============================================================================

if 'sim_results' in st.session_state:
    res = st.session_state['sim_results']
    st.markdown("### 🎲 MONTE CARLO PROJECTIONS")
    
    col_s1, col_s2 = st.columns([1, 3])
    
    with col_s1:
        breach_prob = res['breach_probability']
        color = COLOR_MASHREQ_ORANGE if res['is_breach'] else "#1E8E3E"
        st.markdown(f"""
        <div class='resilience-card' style='text-align:center'>
            <div class='metric-label'>Breach Probability</div>
            <div class='metric-value' style='color:{color}; font-size:4rem'>{breach_prob:.1f}%</div>
            <div style='font-size:0.8rem; margin-top:10px'>Impact Tolerance: 5.0%</div>
        </div>
        """, unsafe_allow_html=True)
        
    with col_s2:
        # Plotly Histogram
        df_sim = pd.DataFrame(res['simulation_data'], columns=["Impact Score"])
        df_sim['Breached'] = df_sim['Impact Score'] > 80
        
        fig = px.histogram(df_sim, x="Impact Score", nbins=50, 
                           color="Breached", 
                           color_discrete_map={False: "#1B4298", True: "#FF5E00"},
                           title="Scenario Distribution (5,000 Simulations)")
        
        fig.add_vline(x=80, line_width=3, line_dash="dash", line_color="red", annotation_text="TOLERANCE LIMIT")
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True)


# Tabs
tab_triage, tab_active, tab_audit, tab_decision = st.tabs(["🚀 TRIAGE QUEUE", "🔥 ACTIVE INCIDENTS", "📜 AUDIT TRAIL", "🧠 DECISION SUPPORT"])

with tab_decision:
    st.markdown("### 🧠 RESILIENCE DECISION SUPPORT")
    
    if 'sim_results' in st.session_state:
        res = st.session_state['sim_results']
        data = res['simulation_data']
        
        # 1. INSIGHT GENERATOR
        target_score = 60 # Arbitrary "Safe" budget
        confidence = np.sum(data <= target_score) / len(data) * 100
        
        # Determine driver (mock logic based on known weights)
        drivers = {"Operational Downtime": 30, "Cyber Attack": 25, "Regulatory Fines": 20, "Interest Rates": 15}
        primary_driver = max(drivers, key=drivers.get)
        contribution = drivers[primary_driver]
        
        st.info(f"💡 **STRATEGIC INSIGHT:** You have a **{confidence:.1f}% confidence level** of staying within the Resilience Target (Score < {target_score}). "
                f"The primary driver of uncertainty is **{primary_driver}**, contributing to **{contribution}%** of the variance.")
        
        col_d1, col_d2 = st.columns(2)
        
        # 2. TORNADO CHART (SENSITIVITY)
        with col_d1:
            st.markdown("#### 🌪️ RISK SENSITIVITY (TORNADO)")
            # Mock Sensitivity Data (Impact swing +/- from Mean)
            sensitivity = pd.DataFrame({
                "Risk Factor": ["IT Latency / Downtime", "Cyber Breach", "Regulatory Fines", "Interest Rates", "Market Volatility"],
                "Positive Swing": [15, 12, 10, 7, 5], # Gold (Outcome improves)
                "Negative Swing": [20, 18, 12, 9, 6]  # Red (Outcome worsens)
            })
            
            fig_tornado = go.Figure()
            
            # Positive (Improvement - Gold)
            fig_tornado.add_trace(go.Bar(
                y=sensitivity["Risk Factor"], x=-sensitivity["Positive Swing"],
                name="Opportunity (Better)", orientation='h',
                marker=dict(color=COLOR_GOLD)
            ))
            
            # Negative (Risk - Red)
            fig_tornado.add_trace(go.Bar(
                y=sensitivity["Risk Factor"], x=sensitivity["Negative Swing"],
                name="Threat (Worse)", orientation='h',
                marker=dict(color=COLOR_CRITICAL)
            ))
            
            fig_tornado.update_layout(barmode='overlay', title="Impact Variance by Factor", 
                                      xaxis_title="Impact Score Swing", showlegend=True,
                                      paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig_tornado, use_container_width=True)
            
        # 3. S-CURVE (CUMULATIVE PROBABILITY)
        with col_d2:
            st.markdown("#### 📈 CONFIDENCE CURVE (S-CURVE)")
            
            # Calculate CDF
            sorted_data = np.sort(data)
            y_vals = np.arange(1, len(sorted_data)+1) / len(sorted_data)
            
            fig_s = go.Figure()
            fig_s.add_trace(go.Scatter(x=sorted_data, y=y_vals, mode='lines', 
                                       name='Cumulative Probability', line=dict(color=COLOR_MASHREQ_BLUE, width=3)))
            
            # Vertical Lines
            mean_val = np.mean(data)
            fig_s.add_vline(x=target_score, line_dash="dash", line_color=COLOR_GOLD, annotation_text="Target Budget")
            fig_s.add_vline(x=mean_val, line_dash="dot", line_color=COLOR_MASHREQ_ORANGE, annotation_text="Current Forecast")
            
            fig_s.update_layout(title="Probability of Meeting Target", 
                                xaxis_title="Impact Score", yaxis_title="Probability",
                                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig_s, use_container_width=True)
            
    else:
        st.warning("⚠️ Run Simulation to generate Decision Support data.")

with tab_triage:
    pending = [a for a in st.session_state['alerts_db'].values() if a['status'] == 'PENDING']
    if not pending:
        st.success("✅ No pending operational signals.")
    for a in pending:
        render_alert_card(a)

with tab_active:
    active = [a for a in st.session_state['alerts_db'].values() if a['status'] == 'ESCALATED']
    if not active:
        st.info("No active incidents.")
    for a in active:
        render_alert_card(a)

with tab_audit:
    if os.path.exists("data/audit_trail.csv"):
        df = pd.read_csv("data/audit_trail.csv")
        st.dataframe(df, use_container_width=True)
    else:
        st.info("Log is empty.")

# Refresh
time.sleep(5)
st.rerun()
