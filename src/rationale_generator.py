"""
Rationale Generator - Stage 6: Model Rationale
===============================================
Generates structured explanations for analyst review.

Output sections:
- What signal is this?
- What changed?
- Why it matters to the bank?
- What we don't know yet (uncertainty)
- Assumptions

Responsible AI Mapping:
- Transparency: Interpretable reasoning aligned to evidence
- Accountability: Includes explicit assumptions
"""

from dataclasses import dataclass, field
from typing import Any, List, Dict, Optional
from datetime import datetime


@dataclass
class Rationale:
    """Complete model rationale for a cluster."""
    cluster_id: str
    what_signal: str
    what_changed: str
    why_it_matters: str
    what_we_dont_know: str
    assumptions: List[str]
    evidence_used: List[str]
    generated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "cluster_id": self.cluster_id,
            "what_signal": self.what_signal,
            "what_changed": self.what_changed,
            "why_it_matters": self.why_it_matters,
            "what_we_dont_know": self.what_we_dont_know,
            "assumptions": self.assumptions,
            "evidence_used": self.evidence_used,
            "generated_at": self.generated_at.isoformat()
        }


class RationaleGenerator:
    """
    Generates structured rationales for signal clusters.
    Uses deterministic rules (not LLM) for consistency and auditability.
    """
    
    # Category-specific impact descriptions
    CATEGORY_IMPACTS = {
        'SERVICE': {
            'impact': "Service disruption affects customer trust and operational metrics",
            'matters': "Downtime directly impacts revenue, customer satisfaction, and regulatory standing"
        },
        'FRAUD': {
            'impact': "Fraud indicators suggest active threats to customer assets",
            'matters': "Fraud losses, regulatory fines, and reputational damage require immediate attention"
        },
        'MISINFORMATION': {
            'impact': "False information spreading could trigger customer panic",
            'matters': "Reputational crisis and potential bank run scenarios require proactive response"
        },
        'SENTIMENT': {
            'impact': "Customer sentiment patterns indicate experience quality",
            'matters': "Sustained negative sentiment affects brand perception and customer retention"
        },
    }
    
    # Standard assumptions per category
    STANDARD_ASSUMPTIONS = {
        'SERVICE': [
            "Signals reflect genuine technical issues (not user error)",
            "Correlation between signals indicates related incidents",
        ],
        'FRAUD': [
            "Reported patterns represent actual fraud attempts",
            "Classification accuracy is sufficient for prioritization",
        ],
        'MISINFORMATION': [
            "Social signals reflect broader public perception",
            "Identified keywords correctly indicate panic-inducing content",
        ],
        'SENTIMENT': [
            "Sample is representative of overall customer sentiment",
            "Sentiment classification captures true customer intent",
        ],
    }
    
    def __init__(self):
        pass
    
    def _generate_what_signal(self, cluster: Any, risk_score: Any) -> str:
        """Generate 'What signal is this?' section."""
        category = cluster.category if hasattr(cluster, 'category') else "Unknown"
        volume = cluster.volume if hasattr(cluster, 'volume') else len(cluster.signals)
        
        # Get top phrases if available
        phrases = cluster.top_phrases if hasattr(cluster, 'top_phrases') else []
        phrase_text = f" with keywords: {', '.join(phrases[:3])}" if phrases else ""
        
        risk_level = risk_score.risk_level if risk_score else "UNKNOWN"
        
        templates = {
            'SERVICE': f"Service incident cluster ({volume} signals){phrase_text}. Risk level: {risk_level}.",
            'FRAUD': f"Potential fraud pattern ({volume} reports){phrase_text}. Risk level: {risk_level}.",
            'MISINFORMATION': f"Misinformation/rumor cluster ({volume} signals){phrase_text}. Risk level: {risk_level}.",
            'SENTIMENT': f"Customer sentiment cluster ({volume} signals){phrase_text}. Risk level: {risk_level}.",
        }
        
        return templates.get(category, f"{category} signal cluster ({volume} signals). Risk level: {risk_level}.")
    
    def _generate_what_changed(self, cluster: Any) -> str:
        """Generate 'What changed?' section."""
        spike_ratio = cluster.spike_ratio if hasattr(cluster, 'spike_ratio') else 1.0
        
        if spike_ratio >= 5.0:
            change = f"Significant spike detected: {spike_ratio:.1f}x above baseline volume"
        elif spike_ratio >= 2.0:
            change = f"Elevated activity: {spike_ratio:.1f}x above normal baseline"
        elif spike_ratio >= 1.5:
            change = f"Moderate increase: {spike_ratio:.1f}x typical volume"
        else:
            change = "Volume within normal range but pattern detected"
        
        # Add time context
        if hasattr(cluster, 'time_window_start') and hasattr(cluster, 'time_window_end'):
            delta = cluster.time_window_end - cluster.time_window_start
            minutes = int(delta.total_seconds() / 60)
            change += f" (observed over {minutes} minute window)"
        
        return change
    
    def _generate_why_matters(self, cluster: Any, risk_score: Any) -> str:
        """Generate 'Why it matters to the bank?' section."""
        category = cluster.category if hasattr(cluster, 'category') else "Unknown"
        
        base_impact = self.CATEGORY_IMPACTS.get(category, {})
        matters = base_impact.get('matters', "Requires analyst review")
        
        # Add risk-specific context
        if risk_score:
            score = risk_score.total_score
            if score >= 8.0:
                urgency = "CRITICAL: Immediate escalation recommended."
            elif score >= 6.0:
                urgency = "HIGH PRIORITY: Prompt review required."
            elif score >= 4.0:
                urgency = "MODERATE: Standard review timeline."
            else:
                urgency = "LOW: Monitor for changes."
            
            matters = f"{matters}. {urgency}"
        
        return matters
    
    def _generate_uncertainty(self, cluster: Any, confidence: Any) -> str:
        """Generate 'What we don't know yet' section."""
        uncertainties = []
        
        # Add confidence-based uncertainty
        if confidence:
            if confidence.percentage < 60:
                uncertainties.append("Classification confidence is limited")
            
            # Check component-level issues
            components = confidence.components if hasattr(confidence, 'components') else {}
            if components.get('consistency', {}).get('score', 100) < 60:
                uncertainties.append("Signals show mixed patterns")
            if components.get('cluster_size', {}).get('score', 100) < 50:
                uncertainties.append("Limited sample size")
        
        # Add volume-based uncertainty
        volume = cluster.volume if hasattr(cluster, 'volume') else len(cluster.signals)
        if volume < 5:
            uncertainties.append("Small cluster; pattern may not be representative")
        
        # Add category-specific uncertainties
        category = cluster.category if hasattr(cluster, 'category') else ""
        if category == 'MISINFORMATION':
            uncertainties.append("Cannot confirm if misinformation is coordinated")
        elif category == 'FRAUD':
            uncertainties.append("Cannot confirm actual fraud occurrence (reports only)")
        elif category == 'SERVICE':
            uncertainties.append("Root cause not determined from signals alone")
        
        if not uncertainties:
            return "No significant uncertainties identified"
        
        return "; ".join(uncertainties)
    
    def _generate_assumptions(self, cluster: Any) -> List[str]:
        """Generate assumptions list."""
        category = cluster.category if hasattr(cluster, 'category') else "Unknown"
        
        assumptions = self.STANDARD_ASSUMPTIONS.get(category, [
            "Signals represent genuine patterns",
            "Classification is accurate for prioritization purposes"
        ])
        
        # Add universal assumptions
        assumptions = list(assumptions)  # Copy
        assumptions.append("Synthetic data patterns approximate real-world scenarios")
        
        return assumptions
    
    def _collect_evidence(self, cluster: Any, risk_score: Any, confidence: Any) -> List[str]:
        """Collect evidence used for rationale."""
        evidence = []
        
        # Cluster evidence
        volume = cluster.volume if hasattr(cluster, 'volume') else len(cluster.signals)
        evidence.append(f"Cluster volume: {volume} signals")
        
        if hasattr(cluster, 'top_phrases') and cluster.top_phrases:
            evidence.append(f"Key phrases: {', '.join(cluster.top_phrases[:3])}")
        
        if hasattr(cluster, 'spike_ratio'):
            evidence.append(f"Spike ratio: {cluster.spike_ratio:.1f}x baseline")
        
        # Risk score evidence
        if risk_score:
            evidence.append(f"Risk score: {risk_score.total_score}/10")
            for name, comp in risk_score.components.items():
                evidence.append(f"  - {comp.name}: {comp.score}/{comp.max_score}")
        
        # Confidence evidence
        if confidence:
            evidence.append(f"Confidence: {confidence.percentage:.0f}% ({confidence.level.value})")
        
        return evidence
    
    def generate_rationale(
        self, 
        cluster: Any, 
        risk_score: Any = None, 
        confidence: Any = None
    ) -> Rationale:
        """
        Generate complete rationale for a cluster.
        
        Args:
            cluster: SignalCluster object
            risk_score: Optional RiskScore object
            confidence: Optional ConfidenceScore object
            
        Returns:
            Rationale with all sections
        """
        cluster_id = cluster.cluster_id if hasattr(cluster, 'cluster_id') else "UNK-00"
        
        return Rationale(
            cluster_id=cluster_id,
            what_signal=self._generate_what_signal(cluster, risk_score),
            what_changed=self._generate_what_changed(cluster),
            why_it_matters=self._generate_why_matters(cluster, risk_score),
            what_we_dont_know=self._generate_uncertainty(cluster, confidence),
            assumptions=self._generate_assumptions(cluster),
            evidence_used=self._collect_evidence(cluster, risk_score, confidence)
        )
    
    def format_for_ui(self, rationale: Rationale) -> Dict[str, Any]:
        """
        Format rationale for UI display.
        
        Args:
            rationale: Rationale object
            
        Returns:
            Dictionary formatted for UI rendering
        """
        return {
            "sections": [
                {"title": "What Signal Is This?", "content": rationale.what_signal, "icon": "🔍"},
                {"title": "What Changed?", "content": rationale.what_changed, "icon": "📈"},
                {"title": "Why It Matters", "content": rationale.why_it_matters, "icon": "⚠️"},
                {"title": "What We Don't Know", "content": rationale.what_we_dont_know, "icon": "❓"},
            ],
            "assumptions": rationale.assumptions,
            "evidence": rationale.evidence_used,
            "generated_at": rationale.generated_at.strftime("%Y-%m-%d %H:%M:%S")
        }


# Singleton instance
_generator = None

def get_rationale_generator() -> RationaleGenerator:
    """Get the singleton RationaleGenerator instance."""
    global _generator
    if _generator is None:
        _generator = RationaleGenerator()
    return _generator


# Convenience function
def generate_rationale(cluster: Any, risk_score: Any = None, confidence: Any = None) -> Rationale:
    """Generate rationale for a cluster."""
    return get_rationale_generator().generate_rationale(cluster, risk_score, confidence)


if __name__ == "__main__":
    # Demo
    from dataclasses import dataclass
    from datetime import timedelta
    
    @dataclass
    class MockCluster:
        cluster_id: str
        category: str
        signals: list
        top_phrases: list
        spike_ratio: float
        time_window_start: datetime
        time_window_end: datetime
        
        @property
        def volume(self):
            return len(self.signals)
    
    @dataclass
    class MockRiskScore:
        total_score: float
        risk_level: str
        components: dict
    
    @dataclass
    class MockConfidence:
        percentage: float
        level: any
        components: dict
    
    now = datetime.now()
    cluster = MockCluster(
        cluster_id="FRD-01",
        category="FRAUD",
        signals=[{}, {}, {}, {}],
        top_phrases=["scam", "otp", "unauthorized"],
        spike_ratio=3.2,
        time_window_start=now - timedelta(minutes=20),
        time_window_end=now
    )
    
    risk = MockRiskScore(
        total_score=7.5,
        risk_level="HIGH",
        components={
            "severity": type('obj', (object,), {'name': 'Severity', 'score': 2.2, 'max_score': 2.5})(),
            "velocity": type('obj', (object,), {'name': 'Velocity', 'score': 1.8, 'max_score': 2.5})(),
            "volume": type('obj', (object,), {'name': 'Volume', 'score': 1.5, 'max_score': 2.5})(),
            "trust_impact": type('obj', (object,), {'name': 'Trust Impact', 'score': 2.0, 'max_score': 2.5})(),
        }
    )
    
    generator = RationaleGenerator()
    rationale = generator.generate_rationale(cluster, risk, None)
    
    print("=== Rationale Generation Demo ===\n")
    ui_data = generator.format_for_ui(rationale)
    
    for section in ui_data['sections']:
        print(f"{section['icon']} {section['title']}")
        print(f"   {section['content']}")
        print()
    
    print("Assumptions:")
    for a in rationale.assumptions:
        print(f"   • {a}")
    print()
    
    print("Evidence Used:")
    for e in rationale.evidence_used[:5]:
        print(f"   • {e}")
