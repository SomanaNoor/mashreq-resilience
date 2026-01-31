"""
Responsible AI Pipeline - Unified 10-Stage Pipeline
====================================================
Integrates all pipeline stages into a single coherent workflow.

Stages:
0. Governance Setup (guardrails)
1. Naïve Bayes Classification
2. Noise vs Signal Gating
3. Clustering + Aggregation
4. Risk Scoring (0-10)
5. Confidence Scoring (%)
6. Model Rationale Generation
7. Suggested Escalation
8. Human-in-the-Loop Decision (UI)
9. Audit Logging

Author: Antigravity
"""

import time
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime

# Import all pipeline components
from guardrails import get_guardrails, validate_input
from naive_bayes_classifier import get_classifier, ClassificationResult, BatchClassificationResult
from signal_gate import get_signal_gate, GatingResult, GatedSignal
from clustering_engine import get_clustering_engine, ClusteringResult, SignalCluster
from risk_scorer import get_risk_scorer, RiskScore
from confidence_scorer import get_confidence_scorer, ConfidenceScore
from rationale_generator import get_rationale_generator, Rationale
from escalation_router import get_escalation_router, EscalationSuggestion
from audit_logger import get_audit_logger, AuditRecord


@dataclass
class PipelineOutput:
    """Complete output from the responsible AI pipeline."""
    # Stage 0: Governance
    governance_validated: bool
    validation_issues: List[str]
    
    # Stage 1: Classification
    classification_result: BatchClassificationResult
    
    # Stage 2: Gating
    gating_result: GatingResult
    
    # Stage 3: Clustering
    clustering_result: ClusteringResult
    
    # Per-cluster outputs (Stages 4-7)
    cluster_analyses: List['ClusterAnalysis']
    
    # Metadata
    processing_time_ms: int
    timestamp: str


@dataclass
class ClusterAnalysis:
    """Complete analysis for a single cluster."""
    cluster: SignalCluster
    risk_score: RiskScore
    confidence: ConfidenceScore
    rationale: Rationale
    escalation: EscalationSuggestion
    
    def to_analyst_card(self) -> Dict[str, Any]:
        """Convert to analyst card format for UI."""
        return {
            "cluster_id": self.cluster.cluster_id,
            "title": self._generate_title(),
            "category": self.cluster.category,
            "volume": self.cluster.volume,
            
            # Risk (Stage 4)
            "risk_score": self.risk_score.total_score,
            "risk_level": self.risk_score.risk_level,
            "risk_breakdown": {
                name: {
                    "score": comp.score,
                    "max": comp.max_score,
                    "description": comp.description
                }
                for name, comp in self.risk_score.components.items()
            },
            
            # Confidence (Stage 5)
            "confidence_percentage": self.confidence.percentage,
            "confidence_level": self.confidence.level.value,
            "uncertainty_wording": self.confidence.uncertainty_wording,
            
            # Rationale (Stage 6)
            "rationale": {
                "what_signal": self.rationale.what_signal,
                "what_changed": self.rationale.what_changed,
                "why_it_matters": self.rationale.why_it_matters,
                "what_we_dont_know": self.rationale.what_we_dont_know,
                "assumptions": self.rationale.assumptions,
                "evidence_used": self.rationale.evidence_used
            },
            
            # Escalation (Stage 7)
            "suggested_queue": self.escalation.suggested_queue.value,
            "priority": self.escalation.priority,
            "escalation_reason": self.escalation.reason,
            "approval_required": True,
            
            # UI helpers
            "is_critical": self.risk_score.risk_level == "CRITICAL",
            "top_phrases": self.cluster.top_phrases,
            "example_snippets": self.cluster.example_snippets
        }
    
    def _generate_title(self) -> str:
        """Generate a descriptive title."""
        titles = {
            'SERVICE': "Service Incident",
            'FRAUD': "Fraud Alert",
            'MISINFORMATION': "Misinformation Cluster",
            'SENTIMENT': "Sentiment Pattern",
        }
        base = titles.get(self.cluster.category, "Signal Cluster")
        
        if self.cluster.top_phrases:
            keyword = self.cluster.top_phrases[0].replace("_", " ").title()
            return f"{base}: {keyword}"
        
        return f"{base} ({self.cluster.cluster_id})"


class ResponsibleAIPipeline:
    """
    Unified 10-stage Responsible AI pipeline.
    Orchestrates all components with governance controls.
    """
    
    def __init__(self):
        self.guardrails = get_guardrails()
        self.classifier = get_classifier()
        self.signal_gate = get_signal_gate()
        self.clustering = get_clustering_engine()
        self.risk_scorer = get_risk_scorer()
        self.confidence_scorer = get_confidence_scorer()
        self.rationale_gen = get_rationale_generator()
        self.escalation_router = get_escalation_router()
        self.audit_logger = get_audit_logger()
    
    def process(self, events: List[Dict[str, Any]]) -> PipelineOutput:
        """
        Process a batch of events through the full pipeline.
        
        Args:
            events: List of event dictionaries with 'event_id', 'content', etc.
            
        Returns:
            PipelineOutput with all stage results
        """
        start_time = time.time()
        
        # Stage 0: Governance Validation
        validation_issues = []
        for event in events:
            result = validate_input(event)
            if not result.is_valid:
                validation_issues.extend(result.violations)
        
        governance_validated = len(validation_issues) == 0
        
        # Stage 1: Naïve Bayes Classification
        classification_result = self.classifier.classify_batch(events)
        
        # Stage 2: Noise vs Signal Gating
        gating_result = self.signal_gate.gate_signals(classification_result.results)
        
        # Stage 3: Clustering
        surfaced_signals = gating_result.signals
        clustering_result = self.clustering.cluster_signals(surfaced_signals)
        
        # Stages 4-7: Per-cluster analysis
        cluster_analyses = []
        for cluster in clustering_result.clusters:
            analysis = self._analyze_cluster(cluster)
            cluster_analyses.append(analysis)
            
            # Stage 9: Log to audit trail
            record = self.audit_logger.create_record(
                cluster=cluster,
                classification_result=classification_result,
                risk_score=analysis.risk_score,
                confidence=analysis.confidence,
                rationale=analysis.rationale,
                escalation=analysis.escalation,
                human_decision="PENDING",
                human_user="SYSTEM",
                processing_time_ms=int((time.time() - start_time) * 1000)
            )
            self.audit_logger.log_decision(record)
        
        processing_time = int((time.time() - start_time) * 1000)
        
        return PipelineOutput(
            governance_validated=governance_validated,
            validation_issues=validation_issues,
            classification_result=classification_result,
            gating_result=gating_result,
            clustering_result=clustering_result,
            cluster_analyses=cluster_analyses,
            processing_time_ms=processing_time,
            timestamp=datetime.now().isoformat()
        )
    
    def _analyze_cluster(self, cluster: SignalCluster) -> ClusterAnalysis:
        """Analyze a single cluster through Stages 4-7."""
        # Stage 4: Risk Scoring
        risk_score = self.risk_scorer.calculate_risk_score(cluster)
        
        # Stage 5: Confidence Scoring
        confidence = self.confidence_scorer.calculate_confidence(cluster)
        
        # Stage 6: Rationale Generation
        rationale = self.rationale_gen.generate_rationale(cluster, risk_score, confidence)
        
        # Stage 7: Escalation Routing
        escalation = self.escalation_router.suggest_queue(cluster, risk_score, confidence)
        
        return ClusterAnalysis(
            cluster=cluster,
            risk_score=risk_score,
            confidence=confidence,
            rationale=rationale,
            escalation=escalation
        )
    
    def log_human_decision(
        self, 
        cluster_id: str, 
        decision: str, 
        user: str, 
        reason: str = None
    ) -> bool:
        """
        Log a human decision (Stage 8 completion).
        
        Args:
            cluster_id: Cluster ID
            decision: APPROVED, DISMISSED, or MORE_REVIEW
            user: User identifier
            reason: Optional reason for decision
            
        Returns:
            True if logged successfully
        """
        return self.audit_logger.update_decision(cluster_id, decision, user, reason)
    
    def get_governance_display(self) -> Dict[str, Any]:
        """Get governance information for UI display."""
        return {
            "policy": self.guardrails.get_policy_text(),
            "boundaries": self.guardrails.get_boundaries(),
            "footer": self.guardrails.get_governance_footer(),
            "decision_banner": self.guardrails.get_decision_banner()
        }


# Singleton instance
_pipeline = None

def get_pipeline() -> ResponsibleAIPipeline:
    """Get the singleton pipeline instance."""
    global _pipeline
    if _pipeline is None:
        _pipeline = ResponsibleAIPipeline()
    return _pipeline


# Convenience function
def process_events(events: List[Dict[str, Any]]) -> PipelineOutput:
    """Process events through the full pipeline."""
    return get_pipeline().process(events)


if __name__ == "__main__":
    # Demo
    import json
    
    test_events = [
        {"event_id": "t1", "content": "CRITICAL: 500 Internal Server Error - Gateway Timeout", "source": "App Log"},
        {"event_id": "t2", "content": "Server is down, can't access my account", "source": "Support Ticket"},
        {"event_id": "t3", "content": "Error message when trying to transfer", "source": "Support Ticket"},
        {"event_id": "t4", "content": "Got suspicious SMS about OTP, this is a scam!", "source": "Tweet"},
        {"event_id": "t5", "content": "Phishing email claiming to be from the bank", "source": "Support Ticket"},
        {"event_id": "t6", "content": "What are the branch hours?", "source": "Support Ticket"},
        {"event_id": "t7", "content": "Forgot my password, please help", "source": "Support Ticket"},
    ]
    
    pipeline = ResponsibleAIPipeline()
    result = pipeline.process(test_events)
    
    print("=== Responsible AI Pipeline Demo ===\n")
    print(f"Processed {len(test_events)} events in {result.processing_time_ms}ms")
    print(f"Governance validated: {result.governance_validated}")
    print(f"Signals surfaced: {result.gating_result.signal_count}")
    print(f"Noise archived: {result.gating_result.noise_count}")
    print(f"Clusters formed: {result.clustering_result.cluster_count}")
    print()
    
    for analysis in result.cluster_analyses:
        card = analysis.to_analyst_card()
        print(f"--- {card['title']} ---")
        print(f"Risk: {card['risk_score']}/10 ({card['risk_level']})")
        print(f"Confidence: {card['confidence_percentage']:.0f}% ({card['confidence_level']})")
        print(f"Queue: {card['suggested_queue']} ({card['priority']})")
        print(f"Rationale: {card['rationale']['what_signal']}")
        print()
