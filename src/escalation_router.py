"""
Escalation Router - Stage 7: Suggested Escalation
==================================================
Recommends team queue routing without individual assignment.

Team Queues:
- Operations: Service/technical issues
- Fraud: Fraud indicators and suspicious activity
- Communications: Misinformation and reputational threats
- Risk & Governance: High-risk items requiring oversight

Responsible AI Mapping:
- Accountability: AI recommends only; humans decide
- Human Oversight: Explicit approval requirement
"""

from dataclasses import dataclass
from typing import Any, Optional
from enum import Enum


class TeamQueue(Enum):
    """Available team queues for escalation."""
    OPERATIONS = "Operations"
    FRAUD = "Fraud Review"
    COMMUNICATIONS = "Communications"
    RISK_GOVERNANCE = "Risk & Governance"
    GENERAL = "General Review"


@dataclass
class EscalationSuggestion:
    """Escalation routing suggestion."""
    suggested_queue: TeamQueue
    reason: str
    priority: str  # URGENT, HIGH, STANDARD, LOW
    requires_human_approval: bool  # Always True
    approval_notice: str
    alternative_queues: list  # Other relevant queues
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "suggested_queue": self.suggested_queue.value,
            "reason": self.reason,
            "priority": self.priority,
            "requires_human_approval": self.requires_human_approval,
            "approval_notice": self.approval_notice,
            "alternative_queues": [q.value for q in self.alternative_queues]
        }


class EscalationRouter:
    """
    Routes clusters to appropriate team queues.
    Never assigns to individuals - only queue recommendations.
    """
    
    # Primary routing based on category
    CATEGORY_ROUTING = {
        'SERVICE': TeamQueue.OPERATIONS,
        'FRAUD': TeamQueue.FRAUD,
        'MISINFORMATION': TeamQueue.COMMUNICATIONS,
        'SENTIMENT': TeamQueue.COMMUNICATIONS,
        'NOISE': TeamQueue.GENERAL,
    }
    
    # Alternative queues per category
    ALTERNATIVE_QUEUES = {
        'SERVICE': [TeamQueue.RISK_GOVERNANCE],
        'FRAUD': [TeamQueue.RISK_GOVERNANCE, TeamQueue.OPERATIONS],
        'MISINFORMATION': [TeamQueue.RISK_GOVERNANCE],
        'SENTIMENT': [TeamQueue.OPERATIONS],
        'NOISE': [],
    }
    
    # Priority based on risk level
    RISK_PRIORITY = {
        'CRITICAL': 'URGENT',
        'HIGH': 'HIGH',
        'MEDIUM': 'STANDARD',
        'LOW': 'LOW',
    }
    
    # Routing reasons per category
    ROUTING_REASONS = {
        'SERVICE': "Technical service signals require Operations team review",
        'FRAUD': "Fraud indicators require specialized Fraud Review team assessment",
        'MISINFORMATION': "Reputational signals require Communications team response planning",
        'SENTIMENT': "Customer sentiment patterns for Communications awareness",
        'NOISE': "Routine signals for general review and archival",
    }
    
    # Standard approval notice
    APPROVAL_NOTICE = "Suggested queue: {queue} (human approval required)"
    
    def __init__(self):
        pass
    
    def _determine_priority(self, risk_score: Any, confidence: Any) -> str:
        """Determine priority level based on risk and confidence."""
        if risk_score is None:
            return 'STANDARD'
        
        risk_level = risk_score.risk_level if hasattr(risk_score, 'risk_level') else 'MEDIUM'
        base_priority = self.RISK_PRIORITY.get(risk_level, 'STANDARD')
        
        # Downgrade if confidence is low
        if confidence:
            conf_pct = confidence.percentage if hasattr(confidence, 'percentage') else 50
            if conf_pct < 50 and base_priority == 'URGENT':
                return 'HIGH'
            elif conf_pct < 40 and base_priority == 'HIGH':
                return 'STANDARD'
        
        return base_priority
    
    def _should_route_to_governance(self, risk_score: Any, cluster: Any) -> bool:
        """Check if item should be routed to Risk & Governance."""
        # High risk items always need governance visibility
        if risk_score:
            if risk_score.total_score >= 8.0:
                return True
            if risk_score.is_conservative:
                return True
        
        # Large clusters might need governance review
        volume = cluster.volume if hasattr(cluster, 'volume') else len(cluster.signals)
        if volume >= 15:
            return True
        
        return False
    
    def suggest_queue(
        self, 
        cluster: Any, 
        risk_score: Any = None, 
        confidence: Any = None
    ) -> EscalationSuggestion:
        """
        Suggest escalation queue for a cluster.
        
        Args:
            cluster: SignalCluster object
            risk_score: Optional RiskScore object
            confidence: Optional ConfidenceScore object
            
        Returns:
            EscalationSuggestion with queue and reasoning
        """
        category = cluster.category if hasattr(cluster, 'category') else 'NOISE'
        
        # Get primary queue
        primary_queue = self.CATEGORY_ROUTING.get(category, TeamQueue.GENERAL)
        
        # Override to Risk & Governance if needed
        if self._should_route_to_governance(risk_score, cluster):
            primary_queue = TeamQueue.RISK_GOVERNANCE
        
        # Get alternatives
        alternatives = list(self.ALTERNATIVE_QUEUES.get(category, []))
        if primary_queue in alternatives:
            alternatives.remove(primary_queue)
        
        # Determine priority
        priority = self._determine_priority(risk_score, confidence)
        
        # Build reason
        base_reason = self.ROUTING_REASONS.get(category, "Requires review")
        if risk_score and risk_score.total_score >= 7.0:
            base_reason += f" (Risk Score: {risk_score.total_score}/10)"
        
        # Build approval notice
        approval_notice = self.APPROVAL_NOTICE.format(queue=primary_queue.value)
        
        return EscalationSuggestion(
            suggested_queue=primary_queue,
            reason=base_reason,
            priority=priority,
            requires_human_approval=True,  # Always True
            approval_notice=approval_notice,
            alternative_queues=alternatives
        )
    
    def get_queue_display(self, suggestion: EscalationSuggestion) -> dict:
        """
        Get queue suggestion formatted for UI display.
        
        Args:
            suggestion: EscalationSuggestion object
            
        Returns:
            Dictionary with UI-ready data
        """
        priority_colors = {
            'URGENT': {'bg': '#FCE8E6', 'text': '#D93025'},
            'HIGH': {'bg': '#FEF7E0', 'text': '#EA8600'},
            'STANDARD': {'bg': '#E8F0FE', 'text': '#1967D2'},
            'LOW': {'bg': '#E6F4EA', 'text': '#1E8E3E'},
        }
        
        colors = priority_colors.get(suggestion.priority, priority_colors['STANDARD'])
        
        return {
            "queue_name": suggestion.suggested_queue.value,
            "priority": suggestion.priority,
            "priority_color": colors,
            "reason": suggestion.reason,
            "approval_required": True,
            "approval_notice": suggestion.approval_notice,
            "alternatives": [q.value for q in suggestion.alternative_queues],
            "banner_text": "⚠️ Human approval required before escalation"
        }


# Singleton instance
_router = None

def get_escalation_router() -> EscalationRouter:
    """Get the singleton EscalationRouter instance."""
    global _router
    if _router is None:
        _router = EscalationRouter()
    return _router


# Convenience function
def suggest_queue(cluster: Any, risk_score: Any = None, confidence: Any = None) -> EscalationSuggestion:
    """Suggest escalation queue for a cluster."""
    return get_escalation_router().suggest_queue(cluster, risk_score, confidence)


if __name__ == "__main__":
    # Demo
    from dataclasses import dataclass
    
    @dataclass
    class MockCluster:
        category: str
        signals: list
        
        @property
        def volume(self):
            return len(self.signals)
    
    @dataclass
    class MockRisk:
        total_score: float
        risk_level: str
        is_conservative: bool = False
    
    router = EscalationRouter()
    
    print("=== Escalation Routing Demo ===\n")
    
    # Test cases
    test_cases = [
        (MockCluster("FRAUD", list(range(5))), MockRisk(7.5, "HIGH")),
        (MockCluster("SERVICE", list(range(10))), MockRisk(5.0, "MEDIUM")),
        (MockCluster("MISINFORMATION", list(range(3))), MockRisk(8.5, "CRITICAL")),
    ]
    
    for cluster, risk in test_cases:
        suggestion = router.suggest_queue(cluster, risk)
        display = router.get_queue_display(suggestion)
        
        print(f"Category: {cluster.category}")
        print(f"  Queue: {display['queue_name']}")
        print(f"  Priority: {display['priority']}")
        print(f"  Reason: {display['reason']}")
        print(f"  Notice: {display['approval_notice']}")
        print()
