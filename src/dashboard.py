"""
Mashreq Responsible AI Dashboard
=================================
Complete 10-stage Responsible AI interface with:
- Guardrails Panel (Stage 0)
- Classification Explainer (Stage 1)
- Archived (Noise) Tab (Stage 2)
- Cluster Cards (Stage 3)
- Risk Breakdown Bar (Stage 4)
- Confidence Display (Stage 5)
- Rationale Box (Stage 6)
- Queue Suggestion (Stage 7)
- Human Decision Screen (Stage 8)
- Audit & Reports (Stage 9)

Author: Antigravity
"""

import streamlit as st
import json
import os
import time
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from datetime import datetime

# Import pipeline and components
import sys
sys.path.insert(0, os.path.dirname(__file__))

from responsible_ai_pipeline import get_pipeline, PipelineOutput, ClusterAnalysis
from guardrails import get_guardrails
from simulation_engine import SimulationEngine
from audit_logger import get_audit_logger

# ==============================================================================
# CONFIG & THEME
# ==============================================================================

st.set_page_config(
    page_title="Mashreq Responsible AI",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Brand Colors
COLOR_BG = "#F8F9FA"
COLOR_CARD = "#FFFFFF"
COLOR_TEXT = "#0A0E17"
COLOR_MASHREQ_ORANGE = "#FF5E00"
COLOR_MASHREQ_BLUE = "#1B4298"
COLOR_GOLD = "#D4AF37"
COLOR_CRITICAL = "#D9534F"
COLOR_SUCCESS = "#1E8E3E"

st.markdown("""
<style>
    /* =========== CLINICAL-WHITE BASE THEME =========== */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    
    .stApp {
        background: linear-gradient(180deg, #FFFFFF 0%, #FAFAFA 100%);
        color: #1A1A1A;
        font-family: 'Inter', 'Segoe UI', system-ui, sans-serif;
    }
    
    h1, h2, h3 {
        color: #FF5E00 !important;
        font-family: 'Inter', 'Segoe UI', system-ui, sans-serif;
        font-weight: 700;
    }
    
    /* =========== GLASSMORPHISM ON WHITE (.stCard) =========== */
    .stCard {
        background: rgba(255, 255, 255, 0.7);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 94, 0, 0.1);
        border-radius: 20px;
        padding: 28px;
        box-shadow: 0 10px 40px -10px rgba(255, 94, 0, 0.15);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    .stCard:hover {
        transform: translateY(-4px);
        box-shadow: 0 15px 50px -10px rgba(255, 94, 0, 0.22);
    }
    
    /* =========== GLASSMORPHISM KPI CARDS =========== */
    .glass-metric {
        background: rgba(255, 255, 255, 0.85);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border: 1px solid rgba(255, 94, 0, 0.12);
        border-radius: 20px;
        padding: 24px 20px;
        text-align: center;
        box-shadow: 0 10px 40px -10px rgba(255, 94, 0, 0.15);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    .glass-metric:hover {
        transform: translateY(-4px);
        box-shadow: 0 15px 50px -10px rgba(255, 94, 0, 0.22);
    }
    .glass-metric .metric-value {
        font-size: 2.4rem;
        font-weight: 800;
        color: #FF5E00;
        margin-bottom: 4px;
    }
    .glass-metric .metric-label {
        font-size: 0.8rem;
        color: #666666;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    /* =========== CLINICAL RESILIENCE CARD =========== */
    .resilience-card {
        background: #FFFFFF;
        border-radius: 24px;
        padding: 32px;
        margin-bottom: 24px;
        position: relative;
        overflow: hidden;
        border: 1px solid rgba(255, 94, 0, 0.08);
        box-shadow: 0 10px 40px -10px rgba(255, 94, 0, 0.12);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    .resilience-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 15px 50px -10px rgba(255, 94, 0, 0.18);
    }
    .resilience-card::before {
        content: '';
        position: absolute;
        left: 0;
        top: 0;
        bottom: 0;
        width: 5px;
        background: linear-gradient(180deg, #FF5E00 0%, #FFD700 100%);
        border-radius: 24px 0 0 24px;
    }
    
    /* =========== LED BADGE - GLOWING INDICATOR =========== */
    .led-badge {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 10px 18px;
        border-radius: 50px;
        font-weight: 700;
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 1px;
        transition: all 0.3s ease;
    }
    .led-badge::before {
        content: '';
        width: 10px;
        height: 10px;
        border-radius: 50%;
        display: inline-block;
    }
    .led-badge.led-high {
        background: rgba(255, 94, 0, 0.1);
        color: #FF5E00;
        border: 1px solid rgba(255, 94, 0, 0.3);
    }
    .led-badge.led-high::before {
        background: #FF5E00;
        box-shadow: 0 0 15px #FF5E00, 0 0 30px rgba(255, 94, 0, 0.5);
        animation: led-pulse 1.5s ease-in-out infinite;
    }
    .led-badge.led-medium {
        background: rgba(255, 215, 0, 0.15);
        color: #CC9900;
        border: 1px solid rgba(255, 215, 0, 0.4);
    }
    .led-badge.led-medium::before {
        background: #FFD700;
        box-shadow: 0 0 10px #FFD700;
    }
    .led-badge.led-low {
        background: rgba(100, 100, 100, 0.08);
        color: #666666;
        border: 1px solid rgba(100, 100, 100, 0.2);
    }
    .led-badge.led-low::before {
        background: #999999;
    }
    @keyframes led-pulse {
        0%, 100% { box-shadow: 0 0 15px #FF5E00, 0 0 30px rgba(255, 94, 0, 0.5); }
        50% { box-shadow: 0 0 25px #FF5E00, 0 0 50px rgba(255, 94, 0, 0.7); }
    }
    
    /* =========== CRITICAL CARD PULSE =========== */
    .critical-pulse {
        animation: card-breathe 3s ease-in-out infinite;
        border: 1px solid rgba(255, 94, 0, 0.2);
    }
    .critical-pulse::before {
        background: #FF5E00 !important;
        box-shadow: 0 0 20px rgba(255, 94, 0, 0.6);
    }
    @keyframes card-breathe {
        0%, 100% { box-shadow: 0 10px 40px -10px rgba(255, 94, 0, 0.2); }
        50% { box-shadow: 0 15px 50px -10px rgba(255, 94, 0, 0.35); }
    }
    
    /* =========== ORANGE-YELLOW RISK BARS =========== */
    .risk-bar-container {
        background: #F0F0F0;
        border-radius: 50px;
        height: 12px;
        overflow: visible;
        margin: 10px 0;
        position: relative;
    }
    .risk-bar-fill {
        height: 100%;
        border-radius: 50px;
        transition: width 1s cubic-bezier(0.4, 0, 0.2, 1);
        background: linear-gradient(90deg, #FF5E00 0%, #FFD700 100%);
        position: relative;
    }
    .risk-bar-fill::after {
        content: '';
        position: absolute;
        right: -3px;
        top: 50%;
        transform: translateY(-50%);
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: #FFD700;
        box-shadow: 0 0 12px #FFD700, 0 0 20px rgba(255, 215, 0, 0.6);
    }
    
    /* =========== CONFIDENCE STRIP =========== */
    .confidence-strip {
        height: 12px;
        border-radius: 50px;
        margin: 16px 0;
        background: #F0F0F0;
        overflow: visible;
        position: relative;
    }
    .confidence-fill {
        height: 100%;
        border-radius: 50px;
        transition: width 1.2s cubic-bezier(0.4, 0, 0.2, 1);
        background: linear-gradient(90deg, #FF5E00 0%, #FFD700 100%);
        position: relative;
    }
    
    /* =========== PAPER-EFFECT RATIONALE BOX =========== */
    .rationale-box {
        background: #FFFFFF;
        border-left: 4px solid #FF5E00;
        padding: 24px;
        border-radius: 0 16px 16px 0;
        margin: 20px 0;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
    }
    
    /* =========== DECISION BANNER =========== */
    .decision-banner {
        background: linear-gradient(135deg, rgba(255, 94, 0, 0.05) 0%, rgba(255, 215, 0, 0.05) 100%);
        border: 2px solid rgba(255, 94, 0, 0.2);
        border-radius: 16px;
        padding: 18px 28px;
        text-align: center;
        font-weight: 600;
        margin: 24px 0;
        color: #FF5E00;
    }
    
    /* =========== GOVERNANCE FOOTER =========== */
    .governance-footer {
        background: linear-gradient(135deg, rgba(255, 215, 0, 0.1) 0%, rgba(255, 215, 0, 0.05) 100%);
        border: 1px solid rgba(255, 215, 0, 0.3);
        border-radius: 16px;
        padding: 16px 24px;
        margin-top: 24px;
        font-size: 0.85rem;
        color: #666666;
    }
    
    /* =========== ESCALATION BOX =========== */
    .escalation-box {
        background: rgba(255, 94, 0, 0.04);
        padding: 20px 24px;
        border-radius: 16px;
        margin: 20px 0;
        border: 1px solid rgba(255, 94, 0, 0.12);
    }
    
    /* =========== MONTE CARLO RESULT CARD =========== */
    .mc-result-card {
        background: #FFFFFF;
        border-radius: 24px;
        padding: 36px;
        text-align: center;
        border: 1px solid rgba(255, 94, 0, 0.1);
        box-shadow: 0 10px 40px -10px rgba(255, 94, 0, 0.15);
    }
    .mc-result-value {
        font-size: 4rem;
        font-weight: 800;
        animation: count-up 1s ease-out;
    }
    @keyframes count-up {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    /* =========== STREAMLIT BUTTON OVERRIDES (GHOST PILL) =========== */
    .stButton > button {
        border-radius: 50px !important;
        padding: 12px 28px !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
    }
    .stButton > button[kind="primary"] {
        background: transparent !important;
        border: 2px solid #FF5E00 !important;
        color: #FF5E00 !important;
    }
    .stButton > button[kind="primary"]:hover {
        background: #FF5E00 !important;
        color: white !important;
        box-shadow: 0 8px 25px rgba(255, 94, 0, 0.35) !important;
    }
    .stButton > button:not([kind="primary"]) {
        background: transparent !important;
        border: 2px solid #CCCCCC !important;
        color: #666666 !important;
    }
    .stButton > button:not([kind="primary"]):hover {
        background: #F5F5F5 !important;
        border-color: #999999 !important;
    }
</style>
""", unsafe_allow_html=True)






# ==============================================================================
# STATE MANAGEMENT
# ==============================================================================

if 'pipeline_output' not in st.session_state:
    st.session_state['pipeline_output'] = None

if 'cluster_decisions' not in st.session_state:
    st.session_state['cluster_decisions'] = {}

if 'active_tab' not in st.session_state:
    st.session_state['active_tab'] = 0

# ==============================================================================
# DATA LOADING
# ==============================================================================

def load_and_process_data():
    """Load scenario data and process through pipeline."""
    data_files = [
        "data/scenario_baseline_normal.json",
        "data/scenario_story_liquidity.json",
        "data/scenario_story_cloud_outage.json"
    ]
    
    events = []
    for f in data_files:
        if os.path.exists(f):
            try:
                with open(f, 'r') as file:
                    events.extend(json.load(file))
            except:
                pass
    
    if not events:
        # Generate synthetic events if none exist
        events = [
            {"event_id": f"syn-{i}", "content": f"Synthetic event {i}", "source": "Synthetic"}
            for i in range(10)
        ]
    
    # Process through pipeline
    pipeline = get_pipeline()
    return pipeline.process(events[:100])  # Limit for demo

# ==============================================================================
# UI COMPONENTS
# ==============================================================================

def render_guardrails_panel():
    """Stage 0: Render guardrails and governance panel."""
    guardrails = get_guardrails()
    
    with st.expander("🛡️ GOVERNANCE GUARDRAILS", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### System Use Policy")
            policy = guardrails.system_use_policy
            st.markdown(f"**Purpose:** {policy['purpose']}")
            
            st.markdown("**Allowed Uses:**")
            for use in policy['allowed_uses'][:4]:
                st.markdown(f"- ✅ {use}")
            
            st.markdown("**Prohibited Uses:**")
            for use in policy['prohibited_uses'][:4]:
                st.markdown(f"- ❌ {use}")
        
        with col2:
            st.markdown("### Data Boundaries")
            boundaries = guardrails.get_boundaries()
            
            st.markdown("**Input Boundaries:**")
            st.success("✓ " + ", ".join(boundaries['input_boundaries']['allowed'][:3]))
            st.error("✗ " + ", ".join(boundaries['input_boundaries']['prohibited'][:3]))
            
            st.markdown("### Human Oversight")
            st.info(policy['human_oversight'])


def render_data_card():
    """Render data card information."""
    card_path = "data/data_card.json"
    if os.path.exists(card_path):
        with open(card_path, 'r') as f:
            card = json.load(f)
        
        with st.expander("📋 DATA CARD", expanded=False):
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"**Dataset:** {card['name']}")
                st.markdown(f"**Version:** {card['version']}")
                st.markdown("**In Scope:**")
                for item in card['in_scope']['data_types'][:3]:
                    st.markdown(f"- {item}")
            with col2:
                st.markdown("**Out of Scope:**")
                for item in card['out_of_scope']['excluded_data'][:4]:
                    st.markdown(f"- {item}")
                st.markdown("**Limitations:**")
                for lim in card['limitations'][:2]:
                    st.markdown(f"- ⚠️ {lim}")


def render_classification_explainer(result):
    """Stage 1: Render classification explanation."""
    if not result or not result.classification_result:
        return
    
    st.markdown("### 🔍 Classification Breakdown")
    
    # Show class distribution
    dist = result.classification_result.class_distribution
    if dist:
        df = pd.DataFrame({
            'Class': list(dist.keys()),
            'Count': list(dist.values())
        })
        
        fig = px.bar(df, x='Class', y='Count', color='Count',
                     color_continuous_scale=['#FFD700', '#FF5E00'], # Yellow to Orange
                     title="Signal Classification Distribution")
        
        fig.update_layout(
            showlegend=False, 
            height=300,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            coloraxis_showscale=False,
            xaxis=dict(showgrid=False, showline=False, tickfont=dict(color='#666')),
            yaxis=dict(showgrid=False, showline=False, tickfont=dict(color='#666')),
            title_font=dict(color='#FF5E00', family='Inter, sans-serif')
        )
        st.plotly_chart(fig, use_container_width=True)


def render_noise_tab(result):
    """Stage 2: Render archived (noise) signals."""
    if not result or not result.gating_result:
        st.info("No gating results available.")
        return
    
    gating = result.gating_result
    
    col1, col2 = st.columns([1, 3])
    with col1:
        st.metric("Archived Items", gating.noise_count)
        st.metric("Surfaced Signals", gating.signal_count)
    
    with col2:
        if gating.gating_summary.get('archive_reasons'):
            st.markdown("**Archive Reasons:**")
            for reason, count in gating.gating_summary['archive_reasons'].items():
                st.markdown(f"- {reason}: {count} items")
    
    if gating.noise:
        st.markdown("### Archived Items (Reviewable)")
        for item in gating.noise[:10]:
            with st.expander(f"📁 {item.event_id} - {item.predicted_class}"):
                st.markdown(f"**Confidence:** {item.confidence:.1%}")
                if item.archive_reason:
                    st.markdown(f"**Reason:** {item.archive_reason.description}")
                st.markdown("*This item was archived but remains reviewable for audit purposes.*")


def render_cluster_card(analysis: ClusterAnalysis):
    """Stages 3-8: Render complete analyst card for a cluster."""
    card = analysis.to_analyst_card()
    cluster = analysis.cluster
    
    is_critical = card['is_critical']
    border_color = COLOR_MASHREQ_ORANGE if is_critical else COLOR_MASHREQ_BLUE
    
    st.markdown(f"""
    <div class='resilience-card {'critical-pulse' if is_critical else ''}' 
         style='border-left: 5px solid {border_color}'>
    """, unsafe_allow_html=True)
    
    # Header
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(f"### {card['title']}")
        st.markdown(f"**Cluster ID:** {card['cluster_id']} | **Volume:** {card['volume']} signals")
    with col2:
        badge_class = 'led-high' if is_critical or card['risk_level'] == 'HIGH' else ('led-medium' if card['risk_level'] == 'MEDIUM' else 'led-low')
        st.markdown(f"<div class='led-badge {badge_class}'>"
                   f"{card['risk_level']}</div>", unsafe_allow_html=True)
    
    # Top phrases (Stage 3)
    if card['top_phrases']:
        st.markdown(f"**Top Phrases:** {', '.join(card['top_phrases'])}")
    
    # Risk Breakdown Bar (Stage 4) - Clinical Orange Bars
    st.markdown("#### 📊 Risk Score Breakdown")
    
    risk_html = "<div style='display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin: 16px 0;'>"
    bar_labels = {"severity": "⚡ Severity", "velocity": "🚀 Velocity", "volume": "📊 Volume", "trust_impact": "🛡️ Trust"}
    
    for name, data in card['risk_breakdown'].items():
        pct = (data['score'] / data['max']) * 100
        risk_html += f"""
        <div style='text-align: center;'>
            <div style='font-weight: 600; font-size: 0.8rem; margin-bottom: 8px; color: #666;'>{bar_labels.get(name, name.title())}</div>
            <div class='risk-bar-container'>
                <div class='risk-bar-fill' style='width: {pct}%;'></div>
            </div>
            <div style='font-size: 0.9rem; font-weight: 700; color: #333;'>{data['score']:.1f}<span style='color: #999;'>/{data['max']:.1f}</span></div>
        </div>
        """
    risk_html += "</div>"
    st.markdown(risk_html, unsafe_allow_html=True)
    
    st.markdown(f"""
    <div style='text-align: center; font-size: 1.1rem; font-weight: 700; margin: 12px 0;'>
        Total Risk Score: <span style='color: {COLOR_MASHREQ_ORANGE if card['risk_score'] >= 7 else "#333"};'>{card['risk_score']:.1f}</span>/10.0
    </div>
    """, unsafe_allow_html=True)
    
    # Confidence Display (Stage 5) - Clinical Strip
    st.markdown(f"""
    <div class='confidence-strip'>
        <div class='confidence-fill' style='width: {card['confidence_percentage']}%;'></div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown(f"**Confidence:** {card['confidence_percentage']:.0f}% ({card['confidence_level']}) - {card['uncertainty_wording']}")
    
    # Rationale Box (Stage 6) - Paper Effect
    st.markdown("""
    <div class='rationale-box'>
        <h4>📋 Model Rationale</h4>
    """, unsafe_allow_html=True)
    
    rationale = card['rationale']
    st.markdown(f"**🔍 What Signal:** {rationale['what_signal']}")
    st.markdown(f"**📈 What Changed:** {rationale['what_changed']}")
    st.markdown(f"**⚠️ Why It Matters:** {rationale['why_it_matters']}")
    st.markdown(f"**❓ What We Don't Know:** {rationale['what_we_dont_know']}")
    
    st.markdown("</div>", unsafe_allow_html=True) # Close rationale-box
    
    with st.expander("View Assumptions & Evidence"):
        st.markdown("**Assumptions:**")
        for a in rationale['assumptions']:
            st.markdown(f"- {a}")
        st.markdown("**Evidence Used:**")
        for e in rationale['evidence_used'][:5]:
            st.markdown(f"- {e}")
    
    # Escalation Suggestion (Stage 7)
    st.markdown(f"""
    <div class='escalation-box'>
        <strong>📋 Suggested Queue:</strong> {card['suggested_queue']} 
        <span class='gov-badge badge-{'red' if card['priority'] == 'CRITICAL' else 'orange' if card['priority'] == 'HIGH' else 'green'}'>{card['priority']}</span><br>
        <small style='color: #5A6A85;'>{card['escalation_reason']}</small>
    </div>
    """, unsafe_allow_html=True)
    
    # Human Decision Screen (Stage 8)
    st.markdown("""
    <div class='decision-banner'>
        ⚠️ Decision support only — no automated action
    </div>
    """, unsafe_allow_html=True)
    
    cluster_id = card['cluster_id']
    current_decision = st.session_state['cluster_decisions'].get(cluster_id, 'PENDING')
    
    if current_decision == 'PENDING':
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("🚨 Approve Escalation", key=f"approve_{cluster_id}", type="primary"):
                st.session_state['cluster_decisions'][cluster_id] = 'APPROVED'
                get_pipeline().log_human_decision(cluster_id, 'APPROVED', 'analyst_01')
                st.rerun()
        with col2:
            if st.button("🔄 Request More Review", key=f"review_{cluster_id}"):
                st.session_state['cluster_decisions'][cluster_id] = 'MORE_REVIEW'
                get_pipeline().log_human_decision(cluster_id, 'MORE_REVIEW', 'analyst_01')
                st.rerun()
        with col3:
            if st.button("❌ Dismiss", key=f"dismiss_{cluster_id}"):
                st.session_state['cluster_decisions'][cluster_id] = 'DISMISSED'
                get_pipeline().log_human_decision(cluster_id, 'DISMISSED', 'analyst_01')
                st.rerun()
    else:
        decision_colors = {'APPROVED': COLOR_MASHREQ_ORANGE, 'DISMISSED': '#95A5A6', 'MORE_REVIEW': COLOR_GOLD}
        st.markdown(f"""
        <div style='background-color: {decision_colors.get(current_decision, '#E9ECEF')}22; 
             padding: 12px; border-radius: 8px; text-align: center;'>
            <strong>Decision: {current_decision}</strong>
        </div>
        """, unsafe_allow_html=True)
    
    # Governance Footer
    st.markdown("""
    <div class='governance-footer'>
        🛡️ No automated action. No personal data. Synthetic signals only.
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)


def render_audit_tab():
    """Stage 9: Render audit log and reports."""
    logger = get_audit_logger()
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### 📜 Audit Trail")
        records = logger.get_recent_records(20)
        
        if records:
            df = pd.DataFrame([
                {
                    'Timestamp': r.get('timestamp', '')[:19],
                    'Cluster': r.get('cluster_id', ''),
                    'Category': r.get('signal_category', ''),
                    'Risk': r.get('risk_score', 0),
                    'Confidence': f"{r.get('confidence_percentage', 0):.0f}%",
                    'Decision': r.get('human_decision', 'PENDING')
                }
                for r in records
            ])
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No audit records yet.")
    
    with col2:
        st.markdown("### 📊 Statistics")
        stats = logger.get_stats()
        st.metric("Total Records", stats.get('total_records', 0))
        
        if stats.get('decisions'):
            st.markdown("**Decisions:**")
            for dec, count in stats['decisions'].items():
                st.markdown(f"- {dec}: {count}")
        
        st.markdown("### 📥 Export")
        if st.button("Download CSV", use_container_width=True):
            csv_data = logger.export_csv()
            st.download_button(
                "📁 Download Full Audit Log",
                csv_data,
                "audit_trail.csv",
                "text/csv"
            )
    
    # Model Card Link
    with st.expander("📋 MODEL CARD"):
        card_path = "data/model_card.json"
        if os.path.exists(card_path):
            with open(card_path, 'r') as f:
                model_card = json.load(f)
            
            st.markdown(f"**Model:** {model_card['model_details']['name']}")
            st.markdown(f"**Type:** {model_card['model_details']['type']}")
            st.markdown(f"**Purpose:** {model_card['intended_use']['primary_purpose']}")
            
            st.markdown("**Known Limitations:**")
            for lim in model_card['known_limitations'][:5]:
                st.markdown(f"- {lim}")


# ==============================================================================
# SIDEBAR
# ==============================================================================

with st.sidebar:
    st.markdown("## 🎛️ CONTROLS")
    
    if st.button("🔄 Process New Data", type="primary", use_container_width=True):
        with st.spinner("Processing through 10-stage pipeline..."):
            st.session_state['pipeline_output'] = load_and_process_data()
            st.session_state['cluster_decisions'] = {}
        st.success("Pipeline complete!")
        st.rerun()
    
    st.markdown("---")
    
    # Monte Carlo Stress Test
    st.markdown("### 🎲 Stress Test")
    with st.expander("Stress Variables", expanded=False):
        sim_rates = st.slider("Interest Rate (bps)", 0, 500, 100)
        sim_downtime = st.slider("Downtime (min)", 0, 1440, 60)
        sim_fines = st.slider("Reg. Fines ($MM)", 0.0, 100.0, 5.0)
        sim_vix = st.slider("Market Vol (VIX)", 10.0, 100.0, 20.0)
        sim_cyber = st.slider("Cyber Breach ($MM)", 0.0, 50.0, 0.0)
    
    if st.button("Run Monte Carlo", use_container_width=True):
        sim_engine = SimulationEngine()
        results = sim_engine.run_simulation(
            sim_rates, sim_downtime, sim_fines, sim_vix, sim_cyber
        )
        st.session_state['sim_results'] = results
        st.rerun()

# ==============================================================================
# MAIN PAGE
# ==============================================================================

# Header
col1, col2 = st.columns([1, 15])
with col1:
    st.markdown("<div style='font-size:3rem;'>🛡️</div>", unsafe_allow_html=True)
with col2:
    st.markdown(f"<h1>Mashreq <span style='color:{COLOR_MASHREQ_ORANGE}'>Responsible AI</span></h1>", 
                unsafe_allow_html=True)
    st.markdown("**Operational Resilience Monitor** | 10-Stage Pipeline | Human-in-the-Loop")

st.markdown("---")

# Governance Panels (Stage 0)
render_guardrails_panel()
render_data_card()

# Load/process data if needed
if not st.session_state.get('pipeline_output'):
    st.info("👆 Click 'Process New Data' in the sidebar to start the pipeline.")
    st.stop()

result = st.session_state['pipeline_output']

# KPI Row - Glassmorphism Cards
k1, k2, k3, k4 = st.columns(4)
with k1:
    st.markdown(f"""
    <div class='glass-metric'>
        <div class='metric-value'>{len(result.classification_result.results)}</div>
        <div class='metric-label'>Signals Processed</div>
    </div>
    """, unsafe_allow_html=True)
with k2:
    st.markdown(f"""
    <div class='glass-metric'>
        <div class='metric-value'>{result.gating_result.noise_count}</div>
        <div class='metric-label'>Noise Filtered</div>
    </div>
    """, unsafe_allow_html=True)
with k3:
    st.markdown(f"""
    <div class='glass-metric'>
        <div class='metric-value'>{result.clustering_result.cluster_count}</div>
        <div class='metric-label'>Clusters Formed</div>
    </div>
    """, unsafe_allow_html=True)
with k4:
    st.markdown(f"""
    <div class='glass-metric'>
        <div class='metric-value'>{result.processing_time_ms}<span style='font-size:1rem'>ms</span></div>
        <div class='metric-label'>Processing Time</div>
    </div>
    """, unsafe_allow_html=True)

# Monte Carlo Results
if 'sim_results' in st.session_state:
    res = st.session_state['sim_results']
    st.markdown("### 🎲 Monte Carlo Projection")
    
    col1, col2 = st.columns([1, 3])
    with col1:
        color = COLOR_MASHREQ_ORANGE if res['is_breach'] else COLOR_SUCCESS
        status_text = "⚠️ BREACH RISK" if res['is_breach'] else "✅ WITHIN TOLERANCE"
        st.markdown(f"""
        <div class='mc-result-card'>
            <div class='mc-result-value' style='color:{color}'>{res['breach_probability']:.1f}%</div>
            <div style='font-size: 0.9rem; color: #5A6A85; margin-top: 8px;'>Breach Probability</div>
            <div style='margin-top: 12px; padding: 8px 16px; border-radius: 20px; 
                 background: {color}22; color: {color}; font-weight: 600; font-size: 0.85rem;'>
                {status_text}
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        df_sim = pd.DataFrame(res['simulation_data'], columns=["Impact Score"])
        df_sim['Breached'] = df_sim['Impact Score'] > 80
        fig = px.histogram(df_sim, x="Impact Score", nbins=50, color="Breached",
                          color_discrete_map={False: '#E0E0E0', True: '#FF5E00'})
        fig.add_vline(x=80, line_dash="dash", line_color="#FFD700", annotation_text="TOLERANCE")
        fig.update_layout(
            height=300, 
            paper_bgcolor="rgba(0,0,0,0)", 
            plot_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(showgrid=False, showline=False, tickfont=dict(color='#666')),
            yaxis=dict(showgrid=False, showline=False, tickfont=dict(color='#666'))
        )
        st.plotly_chart(fig, use_container_width=True)

# Main Tabs
tab_triage, tab_archived, tab_audit = st.tabs([
    "🚀 TRIAGE QUEUE", 
    "📁 ARCHIVED (NOISE)", 
    "📜 AUDIT & REPORTS"
])

with tab_triage:
    # Classification overview (Stage 1)
    render_classification_explainer(result)
    
    st.markdown("---")
    
    # Cluster Cards (Stages 3-8)
    if result.cluster_analyses:
        st.markdown("### 📊 Signal Clusters")
        for analysis in result.cluster_analyses:
            render_cluster_card(analysis)
    else:
        st.info("No clusters formed from current signals.")

with tab_archived:
    render_noise_tab(result)

with tab_audit:
    render_audit_tab()

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 20px;'>
    <small>
        Mashreq Responsible AI System v1.0 | 
        Built with transparency, accountability, and human oversight | 
        Synthetic data only
    </small>
</div>
""", unsafe_allow_html=True)
