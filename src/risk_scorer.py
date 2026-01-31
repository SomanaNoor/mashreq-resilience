"""
Risk Scorer - Stage 4: Risk Scoring with Visible Breakdown
==========================================================
Computes risk score (0-10) with 4 transparent components.

Components (each 0-2.5):
- Severity: Based on signal category weight
- Velocity: Rate of signal arrival
- Volume: Total count in cluster
- Trust Impact: Keyword-based trust impact estimation

Responsible AI Mapping:
- Transparency: Risk score is explainable and auditable
- Accountability: No hidden weighting
- Reliability: Conservative scoring when evidence is weak
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from datetime import datetime


@dataclass
class RiskComponent:
    """A single component of the risk score."""
    name: str
    score: float  # 0-2.5
    max_score: float  # Always 2.5
    description: str
    evidence: str


@dataclass
class RiskScore:
    """Complete risk score with breakdown."""
    total_score: float  # 0-10
    components: Dict[str, RiskComponent]
    risk_level: str  # LOW, MEDIUM, HIGH, CRITICAL
    is_conservative: bool  # True if score was reduced due to weak evidence
    conservative_reason: Optional[str]
    confidence_factor: float  # 0-1, how confident we are in this score
    
    def get_breakdown_dict(self) -> Dict[str, float]:
        """Get simple score breakdown dictionary."""
        return {name: comp.score for name, comp in self.components.items()}


class RiskScorer:
    """
    Calculates transparent risk scores with visible sub-components.
    Each sub-score maxes at 2.5, total max is 10.0.
    """
    
    # Category severity weights (base scores out of 2.5)
    CATEGORY_SEVERITY = {
        'FRAUD': 2.5,
        'MISINFORMATION': 2.3,
        'SERVICE': 2.0,
        'SENTIMENT': 1.0,
        'NOISE': 0.2,
    }
    
    # Trust impact keywords and their weights
    TRUST_IMPACT_KEYWORDS = {
        # High impact (affects customer trust directly)
        'money': 1.0, 'account': 0.8, 'savings': 1.0, 'stolen': 1.2,
        'hacked': 1.2, 'breach': 1.0, 'insolvent': 1.5, 'collapse': 1.5,
        'fraud': 1.0, 'scam': 1.0, 'safe': 0.8, 'trust': 0.9,
        # Medium impact
        'down': 0.5, 'outage': 0.6, 'error': 0.4, 'slow': 0.3,
        'complaint': 0.4, 'disappointed': 0.5, 'angry': 0.5,
    }
    
    # Risk level thresholds
    RISK_LEVELS = [
        (8.0, 'CRITICAL'),
        (6.0, 'HIGH'),
        (4.0, 'MEDIUM'),
        (0.0, 'LOW'),
    ]
    
    def __init__(self):
        pass
    
    def _calculate_severity(self, cluster: Any) -> RiskComponent:
        """Calculate severity component based on category."""
        category = cluster.category if hasattr(cluster, 'category') else 'NOISE'
        base_score = self.CATEGORY_SEVERITY.get(category, 1.0)
        
        # Adjust based on volume (more signals = more confident in severity)
        volume = cluster.volume if hasattr(cluster, 'volume') else len(cluster.signals)
        volume_multiplier = min(1.0, 0.5 + (volume / 10))
        
        final_score = min(2.5, base_score * volume_multiplier)
        
        return RiskComponent(
            name="Severity",
            score=round(final_score, 2),
            max_score=2.5,
            description=f"Based on {category} category classification",
            evidence=f"Category weight: {base_score}/2.5, Volume adjustment: {volume_multiplier:.2f}"
        )
    
    def _calculate_velocity(self, cluster: Any) -> RiskComponent:
        """Calculate velocity component based on rate of arrival."""
        volume = cluster.volume if hasattr(cluster, 'volume') else len(cluster.signals)
        
        # Get time window in minutes
        if hasattr(cluster, 'time_window_start') and hasattr(cluster, 'time_window_end'):
            delta = cluster.time_window_end - cluster.time_window_start
            window_minutes = max(1, delta.total_seconds() / 60)
        else:
            window_minutes = 30  # Default
        
        # Calculate rate (signals per minute)
        rate = volume / window_minutes
        
        # Score based on rate (>1/min is high, >0.5/min is medium)
        if rate >= 1.0:
            score = 2.5
            level = "Critical spike"
        elif rate >= 0.5:
            score = 2.0
            level = "High velocity"
        elif rate >= 0.2:
            score = 1.5
            level = "Elevated"
        elif rate >= 0.1:
            score = 1.0
            level = "Moderate"
        else:
            score = 0.5
            level = "Low"
        
        return RiskComponent(
            name="Velocity",
            score=round(score, 2),
            max_score=2.5,
            description=f"{level}: {rate:.2f} signals/minute",
            evidence=f"{volume} signals in {window_minutes:.0f} minute window"
        )
    
    def _calculate_volume(self, cluster: Any) -> RiskComponent:
        """Calculate volume component based on absolute count."""
        volume = cluster.volume if hasattr(cluster, 'volume') else len(cluster.signals)
        
        # Score based on volume thresholds
        if volume >= 20:
            score = 2.5
            level = "Very High"
        elif volume >= 10:
            score = 2.0
            level = "High"
        elif volume >= 5:
            score = 1.5
            level = "Moderate"
        elif volume >= 3:
            score = 1.0
            level = "Low"
        else:
            score = 0.5
            level = "Minimal"
        
        return RiskComponent(
            name="Volume",
            score=round(score, 2),
            max_score=2.5,
            description=f"{level} volume: {volume} signals",
            evidence=f"Cluster contains {volume} classified signals"
        )
    
    def _calculate_trust_impact(self, cluster: Any) -> RiskComponent:
        """Calculate trust impact based on keyword analysis."""
        # Collect all text from cluster
        all_text = ""
        signals = cluster.signals if hasattr(cluster, 'signals') else []
        
        for signal in signals:
            if hasattr(signal, 'classification_result'):
                all_text += " " + signal.classification_result.raw_text.lower()
            elif hasattr(signal, 'raw_text'):
                all_text += " " + signal.raw_text.lower()
            elif hasattr(signal, 'content'):
                all_text += " " + signal.content.lower()
        
        # Score keywords
        total_weight = 0.0
        found_keywords = []
        
        for keyword, weight in self.TRUST_IMPACT_KEYWORDS.items():
            if keyword in all_text:
                total_weight += weight
                found_keywords.append(keyword)
        
        # Normalize to 0-2.5 (cap at 5.0 weight = 2.5 score)
        score = min(2.5, total_weight / 2)
        
        if score >= 2.0:
            level = "Severe"
        elif score >= 1.5:
            level = "High"
        elif score >= 1.0:
            level = "Moderate"
        else:
            level = "Low"
        
        return RiskComponent(
            name="Trust Impact",
            score=round(score, 2),
            max_score=2.5,
            description=f"{level} trust impact detected",
            evidence=f"Keywords: {', '.join(found_keywords[:5]) if found_keywords else 'None detected'}"
        )
    
    def _get_risk_level(self, total_score: float) -> str:
        """Get risk level label for a score."""
        for threshold, level in self.RISK_LEVELS:
            if total_score >= threshold:
                return level
        return 'LOW'
    
    def _apply_conservative_adjustment(
        self, 
        score: float, 
        cluster: Any
    ) -> tuple[float, bool, Optional[str]]:
        """Apply conservative adjustment when evidence is weak."""
        is_conservative = False
        reason = None
        
        # Check for weak evidence indicators
        volume = cluster.volume if hasattr(cluster, 'volume') else len(cluster.signals)
        
        # Conservative if volume is very low for high score
        if volume < 3 and score >= 6.0:
            reduction = 0.2 * (6.0 - volume)
            score = max(score - reduction, 4.0)
            is_conservative = True
            reason = f"Score reduced due to limited evidence ({volume} signals)"
        
        # Conservative if only one signal type/source
        if hasattr(cluster, 'signals') and len(set(
            getattr(s, 'source', 'unknown') for s in cluster.signals 
            if hasattr(s, 'source')
        )) <= 1:
            if score >= 5.0:
                score = score * 0.9
                is_conservative = True
                reason = (reason or "") + "; Single source type"
        
        return score, is_conservative, reason
    
    def calculate_risk_score(self, cluster: Any) -> RiskScore:
        """
        Calculate complete risk score for a cluster.
        
        Args:
            cluster: SignalCluster object
            
        Returns:
            RiskScore with breakdown
        """
        # Calculate each component
        severity = self._calculate_severity(cluster)
        velocity = self._calculate_velocity(cluster)
        volume = self._calculate_volume(cluster)
        trust_impact = self._calculate_trust_impact(cluster)
        
        components = {
            "severity": severity,
            "velocity": velocity,
            "volume": volume,
            "trust_impact": trust_impact
        }
        
        # Sum total score
        total_score = sum(c.score for c in components.values())
        
        # Apply conservative adjustment if needed
        total_score, is_conservative, conservative_reason = \
            self._apply_conservative_adjustment(total_score, cluster)
        
        # Get risk level
        risk_level = self._get_risk_level(total_score)
        
        # Calculate confidence factor based on evidence strength
        avg_component = total_score / 4
        confidence = min(1.0, avg_component / 1.5)  # Full confidence at avg 1.5 per component
        
        return RiskScore(
            total_score=round(total_score, 1),
            components=components,
            risk_level=risk_level,
            is_conservative=is_conservative,
            conservative_reason=conservative_reason,
            confidence_factor=round(confidence, 2)
        )
    
    def get_score_breakdown_bar(self, risk_score: RiskScore) -> List[Dict[str, Any]]:
        """
        Get score breakdown formatted for UI bar visualization.
        
        Args:
            risk_score: RiskScore object
            
        Returns:
            List of bar segment data
        """
        colors = {
            "severity": "#FF6B6B",
            "velocity": "#4ECDC4",
            "volume": "#45B7D1",
            "trust_impact": "#96CEB4"
        }
        
        bars = []
        for name, component in risk_score.components.items():
            bars.append({
                "name": component.name,
                "score": component.score,
                "max_score": component.max_score,
                "percentage": (component.score / component.max_score) * 100,
                "color": colors.get(name, "#666666"),
                "description": component.description,
                "evidence": component.evidence
            })
        
        return bars


# Singleton instance
_scorer = None

def get_risk_scorer() -> RiskScorer:
    """Get the singleton RiskScorer instance."""
    global _scorer
    if _scorer is None:
        _scorer = RiskScorer()
    return _scorer


# Convenience function
def calculate_risk_score(cluster: Any) -> RiskScore:
    """Calculate risk score for a cluster."""
    return get_risk_scorer().calculate_risk_score(cluster)


if __name__ == "__main__":
    # Demo with mock cluster
    from dataclasses import dataclass
    from datetime import timedelta
    
    @dataclass
    class MockSignal:
        raw_text: str
    
    @dataclass
    class MockCluster:
        cluster_id: str
        category: str
        signals: list
        time_window_start: datetime
        time_window_end: datetime
        
        @property
        def volume(self):
            return len(self.signals)
    
    now = datetime.now()
    cluster = MockCluster(
        cluster_id="FRD-01",
        category="FRAUD",
        signals=[
            MockSignal("Got SMS saying my card is stolen, this is a scam"),
            MockSignal("Suspicious phishing email about account breach"),
            MockSignal("Unauthorized transaction on my account, money gone"),
            MockSignal("Someone hacked my account, please help"),
        ],
        time_window_start=now - timedelta(minutes=15),
        time_window_end=now
    )
    
    scorer = RiskScorer()
    risk = scorer.calculate_risk_score(cluster)
    
    print("=== Risk Score Demo ===\n")
    print(f"Cluster: {cluster.cluster_id}")
    print(f"Risk Score: {risk.total_score}/10.0 ({risk.risk_level})")
    print(f"Conservative: {risk.is_conservative}")
    if risk.conservative_reason:
        print(f"Reason: {risk.conservative_reason}")
    print()
    print("Breakdown:")
    for bar in scorer.get_score_breakdown_bar(risk):
        print(f"  {bar['name']:15} {bar['score']:.1f}/{bar['max_score']:.1f} - {bar['description']}")
