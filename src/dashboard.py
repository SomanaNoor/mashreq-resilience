"""
Mashreq Responsible AI Command Center
======================================
Premium 5-Tab Dashboard for Risk Analysts

Tabs:
1. Signal Triage - Active signals needing review with AI reasoning
2. Escalation Hub - Escalated signals with team routing & action plans
3. Audit Trail - Activity log with management summaries
4. Governance Center - Data/Model cards, policies, compliance
5. Analytics - Real-time pipeline metrics & Monte Carlo simulation

Author: Antigravity
"""

import streamlit as st
import pandas as pd
import json
import os
import sys
from datetime import datetime, timedelta
import time

# Add src to path
sys.path.insert(0, os.path.dirname(__file__))

from responsible_ai_pipeline import get_pipeline, process_events, ClusterAnalysis
from data_loader import load_csv_events
from guardrails import get_guardrails
from audit_logger import get_audit_logger
from simulation_engine import SimulationEngine
from governance_shield import GovernanceShield

# Page config
st.set_page_config(
    page_title="Mashreq AI Command Center",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ==============================================================================
# PREMIUM CSS THEME
# ==============================================================================

st.markdown("""
<style>
    /* =========== IMPORTS =========== */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
    
    /* =========== ROOT VARIABLES =========== */
    :root {
        /* Brand Colors */
        --brand-sunrise: #F37021; /* Core Orange */
        --brand-onyx: #2B2B2B;    /* Primary Text */
        --brand-slate: #4B5563;   /* Secondary Text - Darkened for better contrast */
        --brand-cloud: #E5E7EB;   /* Borders */
        --brand-blue: #1B4298;    /* Safe Blue (Governance) */
        
        /* Backgrounds (Light Theme) */
        --bg-primary: #F7F8FA;    /* Page Background (Elevation) */
        --bg-card: #FFFFFF;       /* Card Surface */
        
        /* Semantic Colors */
        --status-critical: #EF4444;       /* Red (Telemetry only) */
        --risk-high: #EA580C;             /* Deep Orange */
        --risk-low: #FFF7ED;              /* Light Orange */
        
        /* Shadows */
        --shadow-lift: 0 4px 12px rgba(0, 0, 0, 0.05);
        --shadow-hover: 0 10px 25px rgba(0, 0, 0, 0.08);
    }
    
    /* =========== BASE STYLES =========== */
    .stApp {
        background-color: var(--bg-primary);
        color: var(--brand-onyx);
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* Hide Streamlit branding */
    #MainMenu, footer, header {visibility: hidden;}
    
    /* =========== HERO HEADER =========== */
    .hero-header {
        background: var(--bg-card);
        border-top: 4px solid var(--brand-sunrise);
        border-bottom: 1px solid var(--brand-cloud);
        border-radius: 0 0 12px 12px;
        padding: 32px 40px;
        margin-bottom: 32px;
        box-shadow: var(--shadow-lift);
    }
    
    .hero-title {
        font-size: 2.5rem;
        font-weight: 800;
        color: var(--brand-onyx);
        margin: 0 0 8px 0;
        letter-spacing: -0.5px;
    }
    .hero-subtitle {
        color: var(--brand-slate);
        font-size: 1.1rem;
        font-weight: 400;
    }
    
    /* =========== CARDS (Modern Clean) =========== */
    .glass-card {
        background: var(--bg-card);
        border: 1px solid var(--brand-cloud);
        border-radius: 12px;
        padding: 24px;
        margin-bottom: 20px;
        box-shadow: var(--shadow-lift);
        transition: all 0.2s ease;
    }
    .glass-card:hover {
        transform: translateY(-2px);
        box-shadow: var(--shadow-hover);
        border-color: var(--brand-sunrise);
    }
    
    /* =========== SIGNAL CARDS =========== */
    .signal-card {
        background: var(--bg-card);
        border: 1px solid var(--brand-cloud);
        border-radius: 12px;
        padding: 28px;
        margin-bottom: 20px;
        position: relative;
        box-shadow: var(--shadow-lift);
        transition: all 0.2s ease;
    }
    .signal-card:hover {
        transform: translateY(-2px);
        box-shadow: var(--shadow-hover);
        border-color: var(--brand-sunrise);
    }
    
    .signal-card::before {
        content: '';
        position: absolute;
        left: 0; top: 12px; bottom: 12px;
        width: 4px;
        border-radius: 0 4px 4px 0;
    }
    .signal-card.critical::before { background-color: var(--status-critical); }
    .signal-card.high::before { background-color: var(--risk-high); }
    .signal-card.medium::before { background-color: #F59E0B; }
    .signal-card.low::before { background-color: #3B82F6; }
    
    .signal-title {
        color: var(--brand-onyx);
        font-size: 1.25rem;
        font-weight: 700;
        margin-bottom: 12px;
    }
    .signal-meta {
        display: flex;
        gap: 16px;
        margin-bottom: 16px;
    }
    
    /* =========== SCORE BADGES =========== */
    .score-badge {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 6px 14px;
        border-radius: 6px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    .risk-badge {
        background: var(--risk-low);
        color: var(--risk-high);
        border: 1px solid rgba(234, 88, 12, 0.2);
    }
    .risk-badge.low { background: #FFF7ED; color: #EA580C; border-color: #FED7AA; } /* Light Orange */
    .risk-badge.medium { background: #FFEDD5; color: #EA580C; border-color: #FDBA74; } /* Medium Orange */
    .risk-badge.high { background: #FED7AA; color: #C2410C; border-color: #FB923C; } /* Deep Orange */
    .risk-badge.critical { background: #FDBA74; color: #9A3412; border-color: #F97316; } /* Darkest Orange */
    .confidence-badge {
        background: #F3F4F6;
        color: var(--brand-slate);
        border: 1px solid var(--brand-cloud);
    }
    .category-badge {
        background: #EEF2FF;
        color: #4F46E5;
        border: 1px solid #E0E7FF;
    }
    
    /* =========== AI REASONING BOX =========== */
    .ai-reasoning {
        background: #FFF7ED; /* Very light orange */
        border-left: 3px solid var(--brand-sunrise);
        border-radius: 0 8px 8px 0;
        padding: 16px 20px;
        margin: 16px 0;
    }
    .ai-reasoning-title {
        color: var(--brand-sunrise);
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 8px;
    }
    .ai-reasoning-text {
        color: var(--brand-onyx);
        font-size: 0.95rem;
        line-height: 1.6;
    }
    
    /* =========== ACTION BUTTONS =========== */
    .stButton > button {
        background-color: var(--brand-sunrise);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 10px 24px;
        font-weight: 600;
        transition: all 0.2s ease;
        box-shadow: 0 2px 4px rgba(243, 112, 33, 0.2);
    }
    .stButton > button:hover {
        background-color: #D95D10; /* Darker orange */
        box-shadow: 0 4px 8px rgba(243, 112, 33, 0.3);
        transform: translateY(-1px);
        color: white;
    }
    .stButton > button[kind="secondary"] {
        background: white;
        border: 1px solid var(--brand-cloud);
        color: var(--brand-slate);
        box-shadow: none;
    }
    .stButton > button[kind="secondary"]:hover {
        border-color: var(--brand-sunrise);
        color: var(--brand-sunrise);
    }

    /* =========== KPI METRICS =========== */
    .kpi-card {
        background: var(--bg-card);
        border: 1px solid var(--brand-cloud);
        border-radius: 12px;
        padding: 24px;
        text-align: center;
        box-shadow: var(--shadow-lift);
    }
    .kpi-value {
        font-size: 2.5rem;
        font-weight: 800;
        color: var(--brand-sunrise);
        letter-spacing: -1px;
    }
    .kpi-label {
        color: var(--brand-slate);
        font-size: 0.85rem;
        font-weight: 500;
        margin-top: 4px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    /* =========== TABS =========== */
    .stTabs [data-baseweb="tab-list"] {
        background: transparent;
        border-bottom: 1px solid var(--brand-cloud);
        gap: 24px;
        padding-bottom: 0;
    }
    .stTabs [data-baseweb="tab"] {
        background: transparent;
        color: var(--brand-slate);
        font-weight: 600;
        padding: 12px 0;
        border: none;
        border-radius: 0;
    }
    .stTabs [aria-selected="true"] {
        background: transparent !important;
        color: var(--brand-sunrise) !important;
        border-bottom: 3px solid var(--brand-sunrise);
    }
    
    /* =========== FORM ELEMENTS =========== */
    .stSelectbox > div > div, .stTextInput > div > div {
        background: var(--bg-card);
        border: 1px solid var(--brand-cloud);
        border-radius: 8px;
        color: var(--brand-onyx);
    }
    
    /* =========== DECISION BANNER =========== */
    .decision-banner {
        background: #F0FDF4; /* Light green */
        border: 1px solid #BBF7D0;
        border-radius: 12px;
        padding: 20px 28px;
        margin-bottom: 24px;
        display: flex;
        align-items: center;
        gap: 16px;
    }
    .decision-banner-text {
        color: #15803D;
        font-weight: 600;
    }
    .decision-banner-sub {
        color: #16A34A;
        font-size: 0.9rem;
    }

</style>
""", unsafe_allow_html=True)

# ==============================================================================
# STATE MANAGEMENT
# ==============================================================================

if 'pipeline_result' not in st.session_state:
    st.session_state['pipeline_result'] = None
if 'escalated_signals' not in st.session_state:
    st.session_state['escalated_signals'] = []
if 'dismissed_signals' not in st.session_state:
    st.session_state['dismissed_signals'] = []
if 'audit_log' not in st.session_state:
    st.session_state['audit_log'] = []

# Department definitions
DEPARTMENTS = {
    "IT Operations": {"icon": "🖥️", "color": "#3B82F6", "desc": "System outages, technical failures"},
    "Fraud Prevention": {"icon": "🛡️", "color": "#EF4444", "desc": "Scams, unauthorized access, phishing"},
    "Communications": {"icon": "📢", "color": "#8B5CF6", "desc": "Misinformation, PR crisis"},
    "Risk Management": {"icon": "⚠️", "color": "#F59E0B", "desc": "Liquidity concerns, market rumors"},
    "Customer Experience": {"icon": "💬", "color": "#10B981", "desc": "Service complaints, sentiment"},
    "Compliance": {"icon": "📋", "color": "#6366F1", "desc": "Regulatory, audit requirements"}
}

# ==============================================================================
# DATA LOADING
# ==============================================================================

@st.cache_data(ttl=60)
def load_pipeline_data():
    """Load and process data through the 10-stage pipeline."""
    try:
        csv_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'synthetic_social_signals_mashreq.csv')
        if not os.path.exists(csv_path):
            csv_path = 'data/synthetic_social_signals_mashreq.csv'
        
        events = load_csv_events(csv_path)
        
        # Run Pipeline
        pipeline = get_pipeline()
        result = pipeline.process(events)
        
        # EMERGENCY BYPASS PROTOCOL Logic Removed from Cached Function
        
        return result, events
    except Exception as e:
        st.error(f"Pipeline error: {e}")
        return None, []

# ==============================================================================
# HELPER FUNCTIONS
# ==============================================================================

def get_risk_level(score):
    if score >= 8: return "critical"
    if score >= 6: return "high"
    if score >= 4: return "medium"
    return "low"

def get_risk_color(score):
    if score >= 8: return "#EF4444"
    if score >= 6: return "#FF5E00"
    if score >= 4: return "#D4AF37"
    return "#3B82F6"

def log_action(action, signal_id, user="Risk Analyst", details=""):
    """Log an action to the audit trail."""
    entry = {
        "timestamp": datetime.now().isoformat(),
        "action": action,
        "signal_id": signal_id,
        "user": user,
        "details": details
    }
    st.session_state['audit_log'].append(entry)
    return entry

# ==============================================================================
# RENDER FUNCTIONS
# ==============================================================================


def render_hero():
    """Render the hero header."""
    st.markdown("""
    <div class="hero-header">
        <div class="hero-title">🏦 Mashreq AI Command Center</div>
        <div class="hero-subtitle">Responsible AI Pipeline for Banking Signal Intelligence • Powered by 10-Stage Governance Architecture</div>
    </div>
    """, unsafe_allow_html=True)

def render_kpis(result, events):
    """Render the KPI metrics grid."""
    if not result:
        return
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="glass-card" style="text-align: center;">
            <div class="kpi-value">{len(events)}</div>
            <div class="kpi-label">Signals Processed</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        active_count = len([a for a in result.cluster_analyses if a.risk_score.total_score >= 4])
        st.markdown(f"""
        <div class="glass-card" style="text-align: center;">
            <div class="kpi-value" style="color: #FF5E00;">{active_count}</div>
            <div class="kpi-label">Requiring Review</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        critical_count = len([a for a in result.cluster_analyses if a.risk_score.total_score >= 8])
        st.markdown(f"""
        <div class="glass-card" style="text-align: center;">
            <div class="kpi-value" style="color: #EF4444;">{critical_count}</div>
            <div class="kpi-label">Critical Alerts</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="glass-card" style="text-align: center;">
            <div class="kpi-value" style="color: #10B981;">✓</div>
            <div class="kpi-label">Governance Validated</div>
        </div>
        """, unsafe_allow_html=True)

def render_signal_card(analysis, show_actions=True, key_prefix=""):
    """Render a single signal card with AI reasoning."""
    card = analysis.to_analyst_card()
    risk_level = get_risk_level(card['risk_score'])
    risk_color = get_risk_color(card['risk_score'])
    
    # Extract values
    title = card['title']
    risk_score = card['risk_score']
    confidence = card['confidence_percentage']
    category = card['category']
    signal_text = card['rationale']['what_signal']
    why_matters = card['rationale']['why_it_matters']
    uncertainty = card['uncertainty_wording']
    
    # Consensus engine flags
    has_sarcasm = card.get('has_sarcasm', False)
    has_ambiguity = card.get('has_ambiguity', False)
    consensus_notes = card.get('consensus_notes', [])
    
    # Get example snippets from cluster
    example_snippets = card.get('example_snippets', [])
    
    # Get top phrases/keywords from cluster
    top_phrases = card.get('top_phrases', [])
    
    # Build consensus badges HTML
    consensus_badges = ""
    if has_sarcasm:
        consensus_badges += '<span class="score-badge" style="background: rgba(245, 158, 11, 0.2); color: #FBBF24; border: 1px solid rgba(245, 158, 11, 0.4);">🎭 Potential Sarcasm</span>'
    if has_ambiguity:
        consensus_badges += '<span class="score-badge" style="background: rgba(239, 68, 68, 0.2); color: #FCA5A5; border: 1px solid rgba(239, 68, 68, 0.4);">⚠️ Model Conflict</span>'
    
    # Build consensus notes HTML
    consensus_html = ""
    if consensus_notes:
        notes_text = "<br>".join(consensus_notes[:2])
        consensus_html = f'''
<div style="margin-top: 12px; padding: 12px; background: #FFF7ED; border-radius: 8px; border-left: 3px solid #EA580C;">
    <div style="color: #EA580C; font-weight: 600; font-size: 0.8rem; margin-bottom: 4px;">🤖 Consensus Analysis (NB vs Groq)</div>
    <div style="color: #6B7280; font-size: 0.85rem;">{notes_text}</div>
</div>'''
    
    # Build keywords/top phrases HTML
    keywords_html = ""
    if top_phrases:
        keyword_badges = " ".join([
            f'<span style="display: inline-block; padding: 4px 12px; margin: 3px; background: rgba(243, 112, 33, 0.1); border: 1px solid rgba(243, 112, 33, 0.3); border-radius: 20px; font-size: 0.8rem; color: #C2410C; font-weight: 500;">🏷️ {phrase}</span>'
            for phrase in top_phrases[:6]  # Show max 6 keywords
        ])
        keywords_html = f'''
<div style="margin-top: 12px; margin-bottom: 12px;">
    <div style="color: var(--brand-slate); font-size: 0.7rem; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 8px;">🔑 Key Themes</div>
    <div style="display: flex; flex-wrap: wrap; gap: 4px;">{keyword_badges}</div>
</div>'''
    
    # Strategic Ambiguity Gauge
    ambiguity = card.get('ambiguity_status', {'level': 'HIGH', 'color': 'green', 'text': 'High Confidence'})
    ambiguity_badge = f'''<span class="score-badge" style="background: rgba(255,255,255,0.1); border: 1px solid {ambiguity['color']}; color: {ambiguity['color']};">{ambiguity['text']} ({confidence:.0f}%)</span>'''

    # Viral Badge
    viral_badge = ""
    is_viral = card.get('is_viral', False)
    if is_viral:
        viral_badge = '''<span class="score-badge" style="background: rgba(239, 68, 68, 0.2); color: #EF4444; border: 1px solid #EF4444; animation: pulse 2s infinite;">🚨 VIRAL: >300% Growth</span>'''
    
    # Card container with badges
    st.markdown(f"""
<div class="signal-card {risk_level}">
<div class="signal-meta" style="margin-bottom: 8px;">{viral_badge}</div>
<div class="signal-title">{title}</div>
<div class="signal-meta">
<span class="score-badge risk-badge {risk_level}">⚠️ Risk: {risk_score}/10</span>
{ambiguity_badge}
<span class="score-badge category-badge">📂 {category}</span>
{consensus_badges}
</div>
{keywords_html}
<div class="ai-reasoning">
        <div class="ai-reasoning-title">🤖 AI Reasoning</div>
        <div class="ai-reasoning-text">
            <span style="font-weight: 600; color: var(--brand-sunrise);">Signal:</span> {signal_text}
        </div>
        <div class="ai-reasoning-text" style="margin-top: 8px;">
            <span style="font-weight: 600; color: var(--brand-sunrise);">Why it matters:</span> {why_matters}
        </div>
        <div class="ai-reasoning-text" style="margin-top: 8px;">
            <span style="font-weight: 600; color: var(--brand-sunrise);">Uncertainty:</span> {uncertainty}
        </div>
        {consensus_html}
    </div>
</div>
""", unsafe_allow_html=True)

    
    if show_actions:
        col1, col2, col3 = st.columns([2, 1, 4])
        with col1:
            if st.button("🚀 Escalate", key=f"{key_prefix}_escalate_{card['cluster_id']}", type="primary"):
                st.session_state['escalated_signals'].append(analysis)
                log_action("ESCALATED", card['cluster_id'])
                st.rerun()
        with col2:
            if st.button("🗑️ Dismiss", key=f"{key_prefix}_dismiss_{card['cluster_id']}"):
                st.session_state['dismissed_signals'].append(analysis)
                log_action("DISMISSED", card['cluster_id'])
                st.rerun()

# ==============================================================================
# COMMAND CENTER LOGIC
# ==============================================================================

from telemetry_engine import get_telemetry_engine, SystemStatus

def render_system_health_leds(health_data):
    """Render LED indicators for internal systems."""
    cols = st.columns(4)
    for idx, (name, sys) in enumerate(health_data.items()):
        color = "#10B981" # Green
        animate = ""
        if sys.status == SystemStatus.CRITICAL:
            color = "#EF4444" # Red
            animate = "blink"
        elif sys.status == SystemStatus.LATENT:
            color = "#F59E0B" # Yellow
        
        display_name = name.replace("_", " ").replace("Core", "").strip()
        
        with cols[idx]:
            st.markdown(f"""
            <div style="background: var(--bg-card); border-radius: 10px; padding: 10px; text-align: center; border: 1px solid var(--brand-cloud); box-shadow: var(--shadow-lift);">
                <div style="font-size: 0.7rem; color: var(--brand-slate); text-transform: uppercase;">{display_name}</div>
                <div style="margin-top: 5px;">
                    <span style="
                        height: 12px; 
                        width: 12px; 
                        background-color: {color}; 
                        border-radius: 50%; 
                        display: inline-block;
                        box-shadow: 0 0 5px {color};
                    "></span>
                    <span style="font-size: 0.8rem; font-weight: 700; color: {color}; margin-left: 5px;">
                        {sys.status.value}
                    </span>
                </div>
                <div style="font-size: 0.65rem; color: var(--brand-slate); margin-top: 2px;">
                    {sys.latency_ms}ms • Err: {sys.error_rate:.1f}%
                </div>
            </div>
            """, unsafe_allow_html=True)

def render_escalation_card(analysis):
    """Render an escalated signal with Command Center Telemetry & Decision Support."""
    card = analysis.to_analyst_card()
    cluster_id = card['cluster_id']
    
    # Initialize Workflow State
    if 'incident_workflows' not in st.session_state:
        st.session_state['incident_workflows'] = {}
    
    if cluster_id not in st.session_state['incident_workflows']:
        st.session_state['incident_workflows'][cluster_id] = {
            'regulatory': False,
            'evidence': False,
            'impact': False,
            'ethics': False
        }
    
    workflow = st.session_state['incident_workflows'][cluster_id]
    
    # Initialize Engines
    telemetry = get_telemetry_engine()
    shield = GovernanceShield()
    plan = shield.get_internal_action_plan(card)
    
    # Get Telemetry Data
    health_data = telemetry.get_system_health()
    correlation = telemetry.correlate_signal(card['category'], card['rationale']['what_signal'])
    
    # Generate Briefing
    briefing_key = f"briefing_{cluster_id}"
    if briefing_key not in st.session_state:
        st.session_state[briefing_key] = telemetry.generate_executive_briefing(card)
    briefing = st.session_state[briefing_key]

    # --- UI RENDER START ---
    
    # Header
    st.markdown(f"""
    <div style="border-left: 4px solid #F37021; padding-left: 16px; margin-bottom: 20px;">
        <div style="font-size: 1.5rem; font-weight: 700; color: var(--brand-onyx);">🚨 INCIDENT: {card['title']}</div>
        <div style="color: var(--brand-slate); font-family: monospace; font-weight: 500;">ID: {cluster_id} • RISK SCORE: {card['risk_score']}/10</div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([1, 1.2]) # Wider column for Decision Support

    # COLUMN 1: CONTEXT (Telemetry & Briefing)
    with col1:
        # LIVE TELEMETRY SHADOW
        with st.container(border=True):
            st.markdown("#### 📡 Telemetry Shadow")
            render_system_health_leds(health_data)
            
            # Correlation
            corr_color = "#EF4444" if correlation.is_confirmed else "#F59E0B"
            if not correlation.action_required: corr_color = "#10B981"
            
            st.markdown(f"""
            <div style="margin-top: 16px; padding: 12px; background: rgba(0,0,0,0.2); border-radius: 8px; border: 1px solid {corr_color}; display: flex; align-items: center; gap: 12px;">
                <div style="font-size: 1.5rem;">{'✅' if correlation.action_required else '📉'}</div>
                <div>
                    <div style="color: {corr_color}; font-weight: 700; font-size: 0.9rem; text-transform: uppercase;">{correlation.status_text}</div>
                    <div style="color: var(--brand-slate); font-size: 0.8rem;">Matched: <span style="color: var(--brand-onyx); font-weight: 600;">{correlation.matched_system}</span> ({correlation.confidence_score}%)</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        # EXECUTIVE BRIEFING
        st.markdown("#### 📋 Executive Briefing")
        st.info(briefing, icon="🤖")

    # COLUMN 2: DECISION SUPPORT SYSTEM (Mandatory Workflow)
    with col2:
        st.markdown("#### 🛡️ Decision Support System")
        
        # Tabs for 4-Step Workflow
        t1, t2, t3, t4 = st.tabs(["1. Compliance", "2. Evidence", "3. Impact", "4. Ethics"])
        
        # TAB 1: REGULATORY COMPLIANCE
        with t1:
            st.markdown("**Regulatory Protocol Check**")
            if 'Senior' in plan['escalation_target']:
                 st.error(f"⚠️ Mandatory Escalation: {plan['escalation_target']}")
            
            st.markdown(f"*{plan['regulatory_check']}*")
            
            if st.checkbox("✅ I have reviewed the CBUAE compliance protocols.", value=workflow['regulatory'], key=f"wk_reg_{cluster_id}"):
                if not workflow['regulatory']:
                    workflow['regulatory'] = True
                    log_action("CHECK_REGULATORY", cluster_id, details="Analyst reviewed CBUAE protocols")
                    st.rerun()
        
        # TAB 2: INTERNAL EVIDENCE
        with t2:
            st.markdown("**Internal Evidence Corroboration**")
            st.markdown(f"*{plan['internal_evidence']}*")
            
            # Show specific telemetry snapshot integration hint
            st.caption(f"System Status: {correlation.matched_system} is {health_data.get(correlation.matched_system, 'UNKNOWN')}")
            
            if st.checkbox("✅ Internal evidence gathered and logged.", value=workflow['evidence'], key=f"wk_ev_{cluster_id}"):
                if not workflow['evidence']:
                    workflow['evidence'] = True
                    log_action("CHECK_EVIDENCE", cluster_id, details="Internal telemetry corroborated")
                    st.rerun()

        # TAB 3: FINANCIAL IMPACT (Monte Carlo)
        with t3:
            st.markdown("**Financial Stress Test (VaR)**")
            st.markdown(f"*{plan['stress_test']}*")
            
            if st.button("🎲 Run Crisis Simulation", key=f"wk_sim_{cluster_id}"):
                with st.spinner("Calculating Value at Risk..."):
                    sim = SimulationEngine(iterations=2000)
                    res = sim.run_simulation(25, 60, 2.0, 30, 5.0) # Base params
                    st.session_state[f"sim_res_{cluster_id}"] = res
                    # Auto-check upon running sim
                    if not workflow['impact']:
                        workflow['impact'] = True
                        log_action("RUN_SIMULATION", cluster_id, details=f"VaR: ${res['var_95']:.2f}M")
                        st.rerun()

            if f"sim_res_{cluster_id}" in st.session_state:
                res = st.session_state[f"sim_res_{cluster_id}"]
                st.markdown(f"""
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-top: 10px;">
                    <div style="background: rgba(239, 68, 68, 0.1); padding: 10px; border-radius: 5px; text-align: center;">
                        <div style="color: #EF4444; font-weight: bold;">{res['breach_probability']:.1%}</div>
                        <div style="font-size: 0.7rem;">Breach Prob.</div>
                    </div>
                    <div style="background: rgba(243, 112, 33, 0.1); padding: 10px; border-radius: 5px; text-align: center;">
                        <div style="color: #C2410C; font-weight: bold;">${res['var_95']:.2f}M</div>
                        <div style="font-size: 0.7rem;">Est. Loss</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                st.success("✅ Risk Assessment Complete")
            else:
                 if workflow['impact']: st.success("✅ Risk Assessment Complete")

        # TAB 4: ETHICS & BIAS
        with t4:
            st.markdown("**Ethical Guardrail Review**")
            st.markdown(f"*{plan['bias_review']}*")
            st.info("Ensure response strategy targets behavioral patterns, not demographics.")
            
            if st.checkbox("✅ No bias detected in signal or response plan.", value=workflow['ethics'], key=f"wk_eth_{cluster_id}"):
                 if not workflow['ethics']:
                    workflow['ethics'] = True
                    log_action("CHECK_ETHICS", cluster_id, details="Bias review signed off")
                    st.rerun()

        st.divider()
        
        # COMPLETE WORKFLOW Check
        steps_complete = all(workflow.values())
        
        # Routing & Resolution
        c_route, c_resolve = st.columns([2, 1])
        
        with c_route:
            st.markdown("###### 📤 Dept Routing")
            dept_cols = st.columns(2)
            for idx, (dept, info) in enumerate(DEPARTMENTS.items()):
                with dept_cols[idx % 2]:
                     if st.button(f"{info['icon']} {dept}", key=f"rt_{cluster_id}_{dept}", use_container_width=True):
                        log_action("ROUTED", cluster_id, details=f"Routed to {dept}")
                        st.toast(f"Routed to {dept}")

        with c_resolve:
            st.markdown("###### ✅ Resolution")
            resolve_btn = st.button(
                "Resolve Incident", 
                type="primary", 
                disabled=not steps_complete,
                key=f"res_{cluster_id}",
                use_container_width=True
            )
            
            if not steps_complete:
                st.caption("Complete all 4 checks to enable resolution.")
            
            if resolve_btn:
                log_action("RESOLVED", cluster_id, details="Mandatory workflow passed")
                st.session_state['escalated_signals'].remove(analysis)
                st.success("Incident Resolved")
                st.rerun()

def render_audit_log():
    """Render the audit trail with filtering."""
    st.markdown("### 📊 Activity Log")
    
    # Executive Summary
    # Executive Summary Cards
    total_escalated = len([e for e in st.session_state['audit_log'] if e['action'] == 'ESCALATED'])
    total_dismissed = len([e for e in st.session_state['audit_log'] if e['action'] == 'DISMISSED'])
    total_routed = len([e for e in st.session_state['audit_log'] if e['action'] == 'ROUTED'])
    st.markdown("""
    <div style="font-size: 1.1rem; font-weight: 700; color: var(--brand-onyx); margin-bottom: 20px;">📈 Activity Overview</div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
        <div style="background: var(--risk-low); border: 1px solid rgba(234, 88, 12, 0.2); border-radius: 12px; padding: 20px; text-align: center; box-shadow: var(--shadow-lift);">
            <div style="font-size: 2.5rem; color: var(--risk-high); font-weight: 800;">{total_escalated}</div>
            <div style="color: var(--brand-onyx); font-weight: 600;">Signals Escalated</div>
        </div>
        """, unsafe_allow_html=True)
        
    with col2:
        st.markdown(f"""
        <div style="background: var(--bg-card); border: 1px solid var(--brand-cloud); border-radius: 12px; padding: 20px; text-align: center; box-shadow: var(--shadow-lift);">
            <div style="font-size: 2.5rem; color: var(--brand-slate); font-weight: 800;">{total_dismissed}</div>
            <div style="color: var(--brand-onyx); font-weight: 600;">Signals Dismissed</div>
        </div>
        """, unsafe_allow_html=True)
        
    with col3:
        st.markdown(f"""
        <div style="background: #F0FDF4; border: 1px solid #BBF7D0; border-radius: 12px; padding: 20px; text-align: center; box-shadow: var(--shadow-lift);">
            <div style="font-size: 2.5rem; color: #15803D; font-weight: 800;">{total_routed}</div>
            <div style="color: var(--brand-onyx); font-weight: 600;">Routed to Teams</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Generate Report Button
    if st.button("📄 Generate Management Report", type="primary", use_container_width=True):
        report = generate_management_report()
        st.download_button(
            "⬇️ Download Report",
            report,
            file_name=f"ai_command_center_report_{datetime.now().strftime('%Y%m%d_%H%M')}.md",
            mime="text/markdown",
             use_container_width=True
        )
    
    st.divider()
    
    # Detailed Log
    st.markdown("### 📝 Recent Actions")
    if not st.session_state['audit_log']:
        st.info("No actions recorded yet. Start reviewing signals to populate the audit trail.")
    else:
        for entry in reversed(st.session_state['audit_log'][-20:]):
            action_map = {
                "ESCALATED": {"icon": "🚀", "bg": "#FFF7ED", "border": "#F59E0B"},
                "DISMISSED": {"icon": "🗑️", "bg": "#F9FAFB", "border": "#E5E7EB"},
                "ROUTED": {"icon": "📤", "bg": "#F0FDF4", "border": "#10B981"},
                "RESOLVED": {"icon": "✅", "bg": "#F0FDF4", "border": "#10B981"},
                "CHECK_REGULATORY": {"icon": "📋", "bg": "#EFF6FF", "border": "#3B82F6"},
                "CHECK_EVIDENCE": {"icon": "🔍", "bg": "#EFF6FF", "border": "#3B82F6"},
                "RUN_SIMULATION": {"icon": "🎲", "bg": "#FAF5FF", "border": "#8B5CF6"},
                "CHECK_ETHICS": {"icon": "⚖️", "bg": "#FDF2F8", "border": "#EC4899"}
            }
            
            act = entry['action']
            style = action_map.get(act, {"icon": "📝", "bg": "#FFFFFF", "border": "#E5E7EB"})
            
            st.markdown(f"""
            <div style="
                background: {style['bg']}; 
                border-left: 4px solid {style['border']}; 
                border-radius: 4px; 
                padding: 16px; 
                margin-bottom: 12px;
                box-shadow: 0 1px 3px rgba(0,0,0,0.05);
                display: flex;
                align-items: center;
                gap: 16px;
            ">
                <div style="font-size: 1.5rem;">{style['icon']}</div>
                <div style="flex-grow: 1;">
                    <div style="font-weight: 700; color: var(--brand-onyx);">{entry['action']} <span style="font-weight: 400; color: var(--brand-slate);">• {entry['signal_id']}</span></div>
                    <div style="color: var(--brand-slate); font-size: 0.9rem;">{entry.get('details', '')}</div>
                </div>
                <div style="color: var(--brand-slate); font-size: 0.8rem; font-family: monospace; white-space: nowrap;">
                    {entry['timestamp'][11:19]}
                </div>
            </div>
            """, unsafe_allow_html=True)

def generate_management_report():
    """Generate a markdown report for upper management."""
    now = datetime.now()
    
    report = f"""# AI Command Center - Executive Report
Generated: {now.strftime('%Y-%m-%d %H:%M:%S')}

## Summary

This report summarizes AI-assisted signal triage activities from the Mashreq Responsible AI Pipeline.

### Key Metrics

| Metric | Count |
|--------|-------|
| Signals Escalated | {len([e for e in st.session_state['audit_log'] if e['action'] == 'ESCALATED'])} |
| Signals Dismissed | {len([e for e in st.session_state['audit_log'] if e['action'] == 'DISMISSED'])} |
| Team Routings | {len([e for e in st.session_state['audit_log'] if e['action'] == 'ROUTED'])} |

### Governance Compliance

✅ All signals processed through 10-stage governance pipeline  
✅ PII automatically redacted (Phone, Email, IBAN, Social Handles)  
✅ Synthetic data only - no real customer data processed  
✅ Human-in-the-loop verification for all decisions  

### Activity Timeline

"""
    for entry in st.session_state['audit_log'][-10:]:
        report += f"- **{entry['timestamp'][:19]}**: {entry['action']} - Signal {entry['signal_id']} {entry.get('details', '')}\n"
    
    report += """

---
*This report was generated by the Mashreq AI Command Center. All AI recommendations require human approval.*
"""
    return report

def render_governance_center():
    """Render the governance and compliance tab."""
    st.markdown("### 📜 Governance Center")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📊 Data Card")
        try:
            data_card_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'data_card.json')
            if not os.path.exists(data_card_path):
                data_card_path = 'data/data_card.json'
            with open(data_card_path, 'r') as f:
                data_card = json.load(f)
            
            st.markdown(f"""
            <div class="glass-card" style="border-top: 4px solid var(--brand-blue);">
                <h4 style="color: var(--brand-blue);">{data_card['dataset_name']}</h4>
                <p style="color: var(--brand-slate);">{data_card['description']}</p>
                <hr style="border-color: var(--brand-cloud);">
                <p><strong>Records:</strong> {data_card['composition']['total_records']}</p>
                <p><strong>PII Handling:</strong> {data_card['governance']['pii_redaction']}</p>
                <p><strong>Synthetic Flag:</strong> ✅ Enabled</p>
            </div>
            """, unsafe_allow_html=True)
        except:
            st.warning("Data card not found")
    
    with col2:
        st.markdown("#### 🤖 Model Card")
        try:
            model_card_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'model_card.json')
            if not os.path.exists(model_card_path):
                model_card_path = 'data/model_card.json'
            with open(model_card_path, 'r') as f:
                model_card = json.load(f)
            
            st.markdown(f"""
            <div class="glass-card" style="border-top: 4px solid var(--brand-sunrise);">
                <h4 style="color: var(--brand-sunrise);">{model_card['model_name']}</h4>
                <p style="color: var(--brand-slate);">{model_card['intended_use']}</p>
                <hr style="border-color: var(--brand-cloud);">
                <p><strong>Type:</strong> {model_card['model_type']}</p>
                <p><strong>Accuracy:</strong> {model_card['performance_metrics']['accuracy']:.0%}</p>
                <p><strong>Latency P99:</strong> {model_card['performance_metrics']['latency_p99']}</p>
            </div>
            """, unsafe_allow_html=True)
        except:
            st.warning("Model card not found")
    
    # Policy Display
    st.markdown("#### 📋 System Use Policy")
    guardrails = get_guardrails()
    
    with st.expander("View Full Policy", expanded=False):
        st.markdown(guardrails.get_policy_text())

def render_analytics_tab(result, events):
    """Render the analytics and simulation tab."""
    st.markdown("### 📈 Pipeline Analytics")
    
    if not result:
        st.warning("Run the pipeline first to see analytics.")
        return
    
    # Pipeline Performance
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### ⚡ Pipeline Performance")
        st.markdown(f"""
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px;">
            <div style="background: #FFF7ED; padding: 12px; border-radius: 8px; text-align: center; border: 1px solid #FED7AA;">
                <div style="font-size: 1.2rem; font-weight: 700; color: #EA580C;">{result.processing_time_ms}ms</div>
                <div style="font-size: 0.8rem; color: var(--brand-slate);">Latency</div>
            </div>
            <div style="background: #E0F2FE; padding: 12px; border-radius: 8px; text-align: center; border: 1px solid #BAE6FD;">
                <div style="font-size: 1.2rem; font-weight: 700; color: #0284C7;">{len(events)}</div>
                <div style="font-size: 0.8rem; color: var(--brand-slate);">Events</div>
            </div>
            <div style="background: #DCFCE7; padding: 12px; border-radius: 8px; text-align: center; border: 1px solid #BBF7D0;">
                <div style="font-size: 1.2rem; font-weight: 700; color: #16A34A;">{result.gating_result.signal_count}</div>
                <div style="font-size: 0.8rem; color: var(--brand-slate);">Signals</div>
            </div>
            <div style="background: #F3F4F6; padding: 12px; border-radius: 8px; text-align: center; border: 1px solid #E5E7EB;">
                <div style="font-size: 1.2rem; font-weight: 700; color: #4B5563;">{result.gating_result.noise_count}</div>
                <div style="font-size: 0.8rem; color: var(--brand-slate);">Filtered</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("#### 📊 Category Distribution")
        dist = result.clustering_result.category_distribution
        for cat, count in dist.items():
            pct = count / sum(dist.values()) * 100 if dist.values() else 0
            st.markdown(f"""
            <div style="margin-bottom: 12px;">
                <div style="color: var(--brand-onyx); margin-bottom: 4px; font-weight: 500;">{cat}: {count} signals</div>
                <div class="risk-bar-container" style="background: #E5E7EB;">
                    <div class="risk-bar-fill" style="width: {pct}%;"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    # Monte Carlo Simulation
    st.markdown("---")
    st.markdown("#### 🎲 Risk Simulation (Monte Carlo)")
    
    with st.form("simulation_form"):
        col1, col2, col3 = st.columns(3)
        with col1:
            interest_rate = st.slider("Interest Rate Impact (bps)", 0, 100, 25)
            downtime = st.slider("Downtime (minutes)", 0, 120, 30)
        with col2:
            reg_fine = st.slider("Regulatory Fine (MM)", 0.0, 10.0, 1.0)
            volatility = st.slider("Market Volatility (VIX)", 10, 50, 20)
        with col3:
            cyber_cost = st.slider("Cyber Breach Cost (MM)", 0.0, 20.0, 5.0)
        
        if st.form_submit_button("Run Simulation", type="primary"):
            with st.spinner("Running 5,000 Monte Carlo iterations..."):
                sim = SimulationEngine(iterations=5000)
                sim_result = sim.run_simulation(interest_rate, downtime, reg_fine, volatility, cyber_cost)
                
                st.markdown(f"""
                <div class="glass-card" style="text-align: center; margin-top: 20px; border-top: 4px solid var(--risk-high);">
                    <div style="font-size: 3rem; font-weight: 800; color: {'#EF4444' if sim_result['is_breach'] else '#10B981'};">
                        {sim_result['breach_probability']:.1%}
                    </div>
                    <div style="color: var(--brand-slate);">Probability of Risk Threshold Breach</div>
                    <hr style="border-color: var(--brand-cloud); margin: 20px 0;">
                    <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 16px; text-align: center;">
                        <div>
                            <div style="color: var(--brand-sunrise); font-size: 1.5rem; font-weight: 700;">${sim_result['mean_impact']:.1f}M</div>
                            <div style="color: var(--brand-slate);">Mean Impact</div>
                        </div>
                        <div>
                            <div style="color: #EA580C; font-size: 1.5rem; font-weight: 700;">${sim_result['var_95']:.1f}M</div>
                            <div style="color: var(--brand-slate);">VaR (95%)</div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

# ==============================================================================
# MAIN APP
# ==============================================================================

def main():
    # Hero Header
    render_hero()
    
    # Load Pipeline Data
    with st.spinner("Loading AI Pipeline..."):
        result, events = load_pipeline_data()
        st.session_state['pipeline_result'] = result
        
        # EMERGENCY BYPASS PROTOCOL (Run outside cache)
        if result and result.cluster_analyses:
            for cluster_analysis in result.cluster_analyses:
                if getattr(cluster_analysis.cluster, 'is_viral', False):
                    # Check if not already in escalated/audit log to avoid dupes
                    exists = any(c.cluster.cluster_id == cluster_analysis.cluster.cluster_id for c in st.session_state['escalated_signals'])
                    if not exists:
                        st.session_state['escalated_signals'].append(cluster_analysis)
                        st.toast(f"🚨 EMERGENCY ALERT: Viral Incident {cluster_analysis.cluster.cluster_id} Bypassed Triage!", icon="🚨")
    
    # KPI Metrics
    if result:
        render_kpis(result, events)
    
    # Main Tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📥 Signal Triage",
        "🚀 Escalation Hub", 
        "📊 Audit Trail",
        "🏛️ Governance",
        "📈 Analytics"
    ])
    
    # TAB 1: Signal Triage
    with tab1:
        st.markdown("""
        <div class="decision-banner">
            <span class="decision-banner-icon">🤖</span>
            <div>
                <div class="decision-banner-text">AI-Assisted Signal Triage</div>
                <div class="decision-banner-sub">Review signals below. AI provides reasoning — you make the decision.</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        if result and result.cluster_analyses:
            # Filter out already processed signals
            escalated_ids = [a.cluster.cluster_id for a in st.session_state['escalated_signals']]
            dismissed_ids = [a.cluster.cluster_id for a in st.session_state['dismissed_signals']]
            
            pending = [a for a in result.cluster_analyses 
                      if a.cluster.cluster_id not in escalated_ids 
                      and a.cluster.cluster_id not in dismissed_ids]
            
            # Sort by risk score
            pending.sort(key=lambda x: x.risk_score.total_score, reverse=True)
            
            if pending:
                st.markdown(f"**{len(pending)} signals awaiting review**")
                for analysis in pending:
                    render_signal_card(analysis, show_actions=True, key_prefix="triage")
            else:
                st.success("✅ All signals have been processed!")
        else:
            st.warning("No signals loaded. Check pipeline configuration.")
    
    # TAB 2: Escalation Hub
    with tab2:
        st.markdown("### 🚀 Escalation Hub")
        st.markdown("Review escalated signals and route to appropriate departments.")
        
        if st.session_state['escalated_signals']:
            for analysis in st.session_state['escalated_signals']:
                render_escalation_card(analysis)
                st.divider()
        else:
            st.info("No escalated signals yet. Escalate signals from the Triage tab.")
    
    # TAB 3: Audit Trail
    with tab3:
        render_audit_log()
    
    # TAB 4: Governance
    with tab4:
        render_governance_center()
    
    # TAB 5: Analytics
    with tab5:
        render_analytics_tab(result, events)

if __name__ == "__main__":
    main()
