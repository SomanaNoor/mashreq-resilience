"""
Audit Logger - Stage 9: Comprehensive Audit Logging
====================================================
Logs all decisions with full context for governance review.

Logged Fields:
- Cluster ID and inputs
- Model outputs (probabilities, scores)
- Risk and confidence values
- Rationale text
- Human decision and timestamp

Responsible AI Mapping:
- Auditability: Complete decision trail
- Accountability: Immutable logging
"""

import csv
import json
import os
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional
from datetime import datetime
from pathlib import Path


@dataclass
class AuditRecord:
    """Complete audit record for a decision."""
    # Identifiers
    record_id: str
    cluster_id: str
    timestamp: str
    
    # Classification inputs
    signal_count: int
    signal_category: str
    top_keywords: List[str]
    
    # Model outputs
    classification_probabilities: Dict[str, float]
    risk_score: float
    risk_breakdown: Dict[str, float]
    confidence_percentage: float
    confidence_level: str
    
    # Rationale
    rationale_summary: str
    assumptions: List[str]
    
    # Escalation
    suggested_queue: str
    priority: str
    
    # Human decision
    human_decision: str  # APPROVED, DISMISSED, MORE_REVIEW
    human_user: str
    decision_reason: Optional[str]
    
    # Metadata
    processing_time_ms: int
    model_version: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary, handling nested structures."""
        result = asdict(self)
        # Stringify complex fields for CSV
        result['top_keywords'] = json.dumps(result['top_keywords'])
        result['classification_probabilities'] = json.dumps(result['classification_probabilities'])
        result['risk_breakdown'] = json.dumps(result['risk_breakdown'])
        result['assumptions'] = json.dumps(result['assumptions'])
        return result
    
    def to_flat_dict(self) -> Dict[str, str]:
        """Convert to flat dictionary with all strings."""
        d = self.to_dict()
        return {k: str(v) if v is not None else "" for k, v in d.items()}


class AuditLogger:
    """
    Comprehensive audit logging for governance compliance.
    Maintains immutable audit trail with export capabilities.
    """
    
    CSV_FILE = "data/audit_trail_full.csv"
    JSON_FILE = "data/audit_log.json"
    
    CSV_HEADERS = [
        "record_id", "cluster_id", "timestamp",
        "signal_count", "signal_category", "top_keywords",
        "classification_probabilities", "risk_score", "risk_breakdown",
        "confidence_percentage", "confidence_level",
        "rationale_summary", "assumptions",
        "suggested_queue", "priority",
        "human_decision", "human_user", "decision_reason",
        "processing_time_ms", "model_version"
    ]
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        self.csv_path = self.data_dir / "audit_trail_full.csv"
        self.json_path = self.data_dir / "audit_log.json"
        self._ensure_files()
    
    def _ensure_files(self):
        """Ensure audit files exist with headers."""
        if not self.csv_path.exists():
            with open(self.csv_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=self.CSV_HEADERS)
                writer.writeheader()
        
        if not self.json_path.exists():
            with open(self.json_path, 'w', encoding='utf-8') as f:
                json.dump([], f)
    
    def _generate_record_id(self) -> str:
        """Generate unique record ID."""
        now = datetime.now()
        return f"AUD-{now.strftime('%Y%m%d%H%M%S')}-{now.microsecond:06d}"
    
    def create_record(
        self,
        cluster: Any,
        classification_result: Any = None,
        risk_score: Any = None,
        confidence: Any = None,
        rationale: Any = None,
        escalation: Any = None,
        human_decision: str = "PENDING",
        human_user: str = "SYSTEM",
        decision_reason: str = None,
        processing_time_ms: int = 0
    ) -> AuditRecord:
        """
        Create an audit record from pipeline outputs.
        
        Args:
            cluster: SignalCluster object
            classification_result: BatchClassificationResult
            risk_score: RiskScore object
            confidence: ConfidenceScore object
            rationale: Rationale object
            escalation: EscalationSuggestion object
            human_decision: Decision made
            human_user: User ID
            decision_reason: Optional reason
            processing_time_ms: Processing time
            
        Returns:
            AuditRecord ready for logging
        """
        # Extract cluster info
        cluster_id = cluster.cluster_id if hasattr(cluster, 'cluster_id') else "UNK"
        signal_count = cluster.volume if hasattr(cluster, 'volume') else len(cluster.signals)
        category = cluster.category if hasattr(cluster, 'category') else "UNKNOWN"
        keywords = cluster.top_phrases if hasattr(cluster, 'top_phrases') else []
        
        # Extract classification probabilities
        class_probs = {}
        if classification_result and hasattr(classification_result, 'results'):
            for r in classification_result.results[:1]:  # Just first result for summary
                if hasattr(r, 'class_probabilities'):
                    class_probs = r.class_probabilities
                    break
        
        # Extract risk info
        risk_val = risk_score.total_score if risk_score else 0.0
        risk_bd = {}
        if risk_score and hasattr(risk_score, 'components'):
            risk_bd = {n: c.score for n, c in risk_score.components.items()}
        
        # Extract confidence info
        conf_pct = confidence.percentage if confidence else 0.0
        conf_lvl = confidence.level.value if confidence and hasattr(confidence, 'level') else "Unknown"
        
        # Extract rationale
        rat_summary = rationale.what_signal if rationale else ""
        assumptions = rationale.assumptions if rationale else []
        
        # Extract escalation
        queue = escalation.suggested_queue.value if escalation else "PENDING"
        priority = escalation.priority if escalation else "STANDARD"
        
        return AuditRecord(
            record_id=self._generate_record_id(),
            cluster_id=cluster_id,
            timestamp=datetime.now().isoformat(),
            signal_count=signal_count,
            signal_category=category,
            top_keywords=keywords[:5],
            classification_probabilities=class_probs,
            risk_score=risk_val,
            risk_breakdown=risk_bd,
            confidence_percentage=conf_pct,
            confidence_level=conf_lvl,
            rationale_summary=rat_summary[:200] if rat_summary else "",
            assumptions=assumptions[:3],
            suggested_queue=queue,
            priority=priority,
            human_decision=human_decision,
            human_user=human_user,
            decision_reason=decision_reason,
            processing_time_ms=processing_time_ms,
            model_version="1.0"
        )
    
    def log_decision(self, record: AuditRecord) -> str:
        """
        Log an audit record to both CSV and JSON.
        
        Args:
            record: AuditRecord to log
            
        Returns:
            Record ID
        """
        # Append to CSV
        with open(self.csv_path, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=self.CSV_HEADERS)
            writer.writerow(record.to_flat_dict())
        
        # Append to JSON
        try:
            with open(self.json_path, 'r', encoding='utf-8') as f:
                records = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            records = []
        
        records.append(record.to_dict())
        
        # Keep only last 1000 records in JSON (CSV keeps all)
        records = records[-1000:]
        
        with open(self.json_path, 'w', encoding='utf-8') as f:
            json.dump(records, f, indent=2)
        
        return record.record_id
    
    def update_decision(
        self, 
        cluster_id: str, 
        human_decision: str, 
        human_user: str, 
        decision_reason: str = None
    ) -> bool:
        """
        Update the human decision for a cluster.
        Note: This appends a new record rather than modifying (audit trail is immutable).
        
        Args:
            cluster_id: Cluster to update
            human_decision: New decision
            human_user: User making decision
            decision_reason: Optional reason
            
        Returns:
            True if logged successfully
        """
        # Create a minimal update record
        update_record = {
            "record_id": self._generate_record_id(),
            "cluster_id": cluster_id,
            "timestamp": datetime.now().isoformat(),
            "update_type": "DECISION_UPDATE",
            "human_decision": human_decision,
            "human_user": human_user,
            "decision_reason": decision_reason or ""
        }
        
        # Append to CSV as a lightweight update row
        # In practice, you'd want a separate updates table
        with open(self.csv_path, 'a', newline='', encoding='utf-8') as f:
            # Write minimal update (pad missing fields)
            row = {h: "" for h in self.CSV_HEADERS}
            row.update({
                "record_id": update_record["record_id"],
                "cluster_id": cluster_id,
                "timestamp": update_record["timestamp"],
                "human_decision": human_decision,
                "human_user": human_user,
                "decision_reason": decision_reason or ""
            })
            writer = csv.DictWriter(f, fieldnames=self.CSV_HEADERS)
            writer.writerow(row)
        
        return True
    
    def export_csv(self, start_date: str = None, end_date: str = None) -> bytes:
        """
        Export audit log as CSV bytes.
        
        Args:
            start_date: Optional start date filter (ISO format)
            end_date: Optional end date filter (ISO format)
            
        Returns:
            CSV file contents as bytes
        """
        with open(self.csv_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # TODO: Implement date filtering if needed
        
        return content.encode('utf-8')
    
    def get_recent_records(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get recent audit records for UI display.
        
        Args:
            limit: Maximum records to return
            
        Returns:
            List of record dictionaries
        """
        try:
            with open(self.json_path, 'r', encoding='utf-8') as f:
                records = json.load(f)
            return records[-limit:]
        except (json.JSONDecodeError, FileNotFoundError):
            return []
    
    def get_stats(self) -> Dict[str, Any]:
        """Get audit log statistics."""
        records = self.get_recent_records(1000)
        
        if not records:
            return {
                "total_records": 0,
                "decisions": {},
                "categories": {}
            }
        
        decisions = {}
        categories = {}
        
        for r in records:
            dec = r.get('human_decision', 'UNKNOWN')
            decisions[dec] = decisions.get(dec, 0) + 1
            
            cat = r.get('signal_category', 'UNKNOWN')
            categories[cat] = categories.get(cat, 0) + 1
        
        return {
            "total_records": len(records),
            "decisions": decisions,
            "categories": categories,
            "last_updated": records[-1].get('timestamp') if records else None
        }


# Singleton instance
_logger = None

def get_audit_logger() -> AuditLogger:
    """Get the singleton AuditLogger instance."""
    global _logger
    if _logger is None:
        _logger = AuditLogger()
    return _logger


# Convenience functions
def log_decision(record: AuditRecord) -> str:
    """Log an audit record."""
    return get_audit_logger().log_decision(record)

def update_decision(cluster_id: str, decision: str, user: str, reason: str = None) -> bool:
    """Update a decision."""
    return get_audit_logger().update_decision(cluster_id, decision, user, reason)


if __name__ == "__main__":
    # Demo
    from dataclasses import dataclass
    
    @dataclass
    class MockCluster:
        cluster_id: str
        category: str
        signals: list
        top_phrases: list
        
        @property
        def volume(self):
            return len(self.signals)
    
    logger = AuditLogger()
    
    cluster = MockCluster(
        cluster_id="FRD-01",
        category="FRAUD",
        signals=list(range(5)),
        top_phrases=["scam", "phishing", "unauthorized"]
    )
    
    record = logger.create_record(
        cluster=cluster,
        human_decision="APPROVED",
        human_user="analyst_01",
        decision_reason="Confirmed fraud pattern",
        processing_time_ms=150
    )
    
    record_id = logger.log_decision(record)
    
    print("=== Audit Logging Demo ===\n")
    print(f"Logged record: {record_id}")
    print(f"Cluster: {record.cluster_id}")
    print(f"Decision: {record.human_decision}")
    print()
    
    stats = logger.get_stats()
    print(f"Total records: {stats['total_records']}")
    print(f"Decisions: {stats['decisions']}")
