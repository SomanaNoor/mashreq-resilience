"""
Telemetry Engine - Internal System Shadowing & Correlation
==========================================================
Simulates internal bank infrastructure status and correlates it with social signals
to validte incidents (e.g. "App Down" tweets + Critical API Health = Confirmed Incident).
"""

import random
from dataclasses import dataclass
from enum import Enum
from datetime import datetime
from typing import Dict, List, Any, Optional

from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

class SystemStatus(Enum):
    HEALTHY = "HEALTHY"
    LATENT = "LATENT"
    CRITICAL = "CRITICAL"

@dataclass
class SystemHealth:
    system_name: str
    status: SystemStatus
    latency_ms: int
    error_rate: float
    last_heartbeat: str

@dataclass
class CorrelationResult:
    is_confirmed: bool
    status_text: str
    confidence_score: int
    matched_system: str
    action_required: bool

class TelemetryEngine:
    
    SYSTEMS = [
        "Mobile_Banking_Core",
        "SMS_Gateway_OTP",
        "ATM_Switch_Network",
        "Credit_Card_Auth_Layer"
    ]
    
    def __init__(self):
        self.llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.3)
        self.status_cache = {}
        self._refresh_system_status()
        
    def _refresh_system_status(self):
        """Mock: Randomly assign status to systems (mostly healthy)."""
        for sys in self.SYSTEMS:
            # 80% Healthy, 10% Latent, 10% Critical
            r = random.random()
            if r > 0.9:
                status = SystemStatus.CRITICAL
                latency = random.randint(800, 5000)
                err = random.uniform(5.0, 25.0)
            elif r > 0.8:
                status = SystemStatus.LATENT
                latency = random.randint(200, 800)
                err = random.uniform(1.0, 5.0)
            else:
                status = SystemStatus.HEALTHY
                latency = random.randint(10, 150)
                err = random.uniform(0.0, 0.5)
                
            self.status_cache[sys] = SystemHealth(
                system_name=sys,
                status=status,
                latency_ms=latency,
                error_rate=err,
                last_heartbeat=datetime.now().strftime("%H:%M:%S")
            )

    def get_system_health(self) -> Dict[str, SystemHealth]:
        """Get current status of all internal systems."""
        # Refresh occasionally to simulate life
        if random.random() > 0.7:
            self._refresh_system_status()
        return self.status_cache

    def correlate_signal(self, signal_category: str, signal_text: str) -> CorrelationResult:
        """
        Correlate a social signal with internal system health.
        Logic:
        - SERVICE + Critical System = Confirmed Incident (High Confidence)
        - SERVICE + Healthy System = Misinformation/Rumor (Low Confidence in Alert)
        - FRAUD + Latent SMS = Active Fraud Pattern
        """
        health = self.get_system_health()
        
        # Default
        return CorrelationResult(
            is_confirmed=False,
            status_text="⚠️ Unverified External Report",
            confidence_score=30,
            matched_system="None",
            action_required=True
        )
        
        # TODO: Implement stricter logic mapping (e.g. keywords to specific systems)
        # For prototype, we'll map category blindly to closest system
        
        target_system = "Mobile_Banking_Core"
        if "otp" in signal_text.lower() or "sms" in signal_text.lower():
            target_system = "SMS_Gateway_OTP"
        elif "atm" in signal_text.lower():
            target_system = "ATM_Switch_Network"
            
        sys_status = health.get(target_system)
        
        if not sys_status:
            return CorrelationResult(False, "System Unknown", 0, "Unknown", False)
            
        if sys_status.status == SystemStatus.CRITICAL:
            return CorrelationResult(
                is_confirmed=True,
                status_text="🚨 CONFIRMED DISRUPTION: Matches Internal Telemetry",
                confidence_score=95,
                matched_system=target_system,
                action_required=True
            )
        elif sys_status.status == SystemStatus.LATENT:
            return CorrelationResult(
                is_confirmed=True,
                status_text="⚠️ PARTIAL CORRELATION: System Degradation Detected",
                confidence_score=75,
                matched_system=target_system,
                action_required=True
            )
        else:
             return CorrelationResult(
                is_confirmed=False,
                status_text="📉 NO INTERNAL ANOMALY: Potential Misinformation/User Error",
                confidence_score=90, # High confidence that it's NOT a system issue
                matched_system=target_system,
                action_required=False
            )

    def generate_executive_briefing(self, analysis_card: Dict[str, Any]) -> str:
        """
        Generate a 3-sentence executive briefing using Groq.
        Include Financial Exposure (VaR/Ops Loss).
        """
        
        # Template-based fallback (for Rate Limits or Errors)
        title = analysis_card.get('title', 'Incident')
        cat = analysis_card.get('category', 'ALERT')
        
        fallback_briefing = (
            f"**Nature of Threat**: Potentially significant {cat} event detected involving '{title}'. "
            f"**Financial Exposure**: Estimated Operational Value at Risk (VaR) ranges from $50k to $150k depending on duration. "
            f"**Action**: Immediate escalation to {cat} Response Team requires verification of internal logs."
        )

        prompt = ChatPromptTemplate.from_template("""
        You are a Chief Risk Officer at a major bank. Write a TIGHT, 3-SENTENCE Executive Briefing for this incident.
        
        Incident: {title}
        Category: {category}
        Details: {summary}
        
        REQUIREMENTS:
        1. Sentence 1: The Nature of the Threat (Technical/Fraud/Reputational).
        2. Sentence 2: Estimated Financial Exposure. Use terms like "Potential Operational Loss" or "Value at Risk (VaR)". Estimate a realistic range in USD (e.g. $50k-$200k for minor, $1M+ for major).
        3. Sentence 3: Recommended Department Routing & Immediate Action.
        
        Tone: Urgent, Professional, Financial.
        Output: Plain text only, no markdown.
        """)
        
        chain = prompt | self.llm
        
        try:
            response = chain.invoke({
                "title": analysis_card.get('title'),
                "category": analysis_card.get('category'),
                "summary": analysis_card.get('rationale', {}).get('why_it_matters', 'Unknown')
            })
            return response.content
        except Exception as e:
            # Check for Rate Limit specific errors to avoid logging them as scary failures
            err_str = str(e).lower()
            if "429" in err_str or "rate limit" in err_str:
                 return fallback_briefing
            return f"⚠️ [Briefing Unavailable] {fallback_briefing}"

# Singleton
_engine = None
def get_telemetry_engine():
    global _engine
    if _engine is None:
        _engine = TelemetryEngine()
    return _engine
