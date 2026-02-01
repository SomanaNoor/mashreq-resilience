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
from consensus_engine import get_consensus_engine, ConsensusResult
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
        # Extract consensus flags from signals in cluster
        has_sarcasm = False
        has_ambiguity = False
        consensus_notes = []
        
        for signal in self.cluster.signals:
            # Check if signal has classification_result with consensus fields
            if hasattr(signal, 'classification_result'):
                cr = signal.classification_result
            else:
                cr = signal  # Direct ClassificationResult
            
            if hasattr(cr, 'potential_sarcasm') and cr.potential_sarcasm:
                has_sarcasm = True
            if hasattr(cr, 'is_ambiguous') and cr.is_ambiguous:
                has_ambiguity = True
            if hasattr(cr, 'consensus_note') and cr.consensus_note:
                consensus_notes.append(cr.consensus_note)
        
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
            "example_snippets": self.cluster.example_snippets,
            
            # Consensus Engine Flags (Stage 1b)
            "has_sarcasm": has_sarcasm,
            "has_ambiguity": has_ambiguity,
            "consensus_notes": consensus_notes[:3],  # Top 3 notes
            
            # Incident Management / Virality
            "is_viral": getattr(self.cluster, 'is_viral', False),
            "velocity_growth_pct": getattr(self.cluster, 'velocity_growth_pct', 0.0),
            
            # Strategic Ambiguity Gauge Logic
            "ambiguity_status": self._get_ambiguity_status(self.confidence.percentage)
        }
        
    def _get_ambiguity_status(self, confidence_score: float) -> dict:
        """
        Transform abstract confidence into Strategic Ambiguity Gauge.
        0-40%: Red (Low Confidence)
        41-75%: Orange (Ambiguous - Human Intervention Required)
        76-100%: Green (High Confidence)
        """
        if confidence_score <= 40:
            return {"level": "LOW", "color": "red", "text": "Low Confidence Analysis"}
        elif confidence_score <= 75:
            return {"level": "AMBIGUOUS", "color": "orange", "text": "⚠️ Ambiguous Intent: Senior Review Req."}
        else:
            return {"level": "HIGH", "color": "green", "text": "High Confidence"}
    
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
        
        # Stage 1b: Hybrid Consensus Check (NB + Groq Semantic)
        # Run semantic analysis on high-risk or ambiguous classifications
        try:
            consensus_engine = get_consensus_engine()
            consensus_results = consensus_engine.validate_batch(
                events, 
                classification_result.results
            )
            
            # Update classification results with consensus flags
            for nb_result, consensus in zip(classification_result.results, consensus_results):
                nb_result.is_ambiguous = consensus.is_ambiguous
                nb_result.potential_sarcasm = consensus.potential_sarcasm
                nb_result.consensus_note = consensus.consensus_note
                if consensus.potential_sarcasm or consensus.is_ambiguous:
                    nb_result.semantic_override = consensus.final_class
        except Exception as e:
            # Fallback: continue without consensus if Groq fails
            print(f"⚠️ Consensus engine skipped: {e}")
        
        # Calculate signal volume map for Gating Override
        # (Allows low-confidence signals to pass if volume is high)
        from collections import Counter
        event_ids = [r.event_id for r in classification_result.results]
        # Since event_ids are unique, we need to group by SIMILARITY or CONTENT hash
        # For this pipeline, we'll use a simplified content-based volume for Stage 2
        content_hashes = [hash(r.raw_text[:50]) for r in classification_result.results]
        content_counts = Counter(content_hashes)
        
        volume_map = {}
        for r, h in zip(classification_result.results, content_hashes):
             volume_map[r.event_id] = content_counts[h]

        # Stage 2: Noise vs Signal Gating
        gating_result = self.signal_gate.gate_signals(
            classification_result.results, 
            volume_map=volume_map  # NEW: Pass volume for override logic
        )
        
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
