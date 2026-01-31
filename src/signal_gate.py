"""
Signal Gate - Stage 2: Noise vs Signal Gating
==============================================
Gates signals based on confidence and volume thresholds.
Archived items remain reviewable - nothing is silently discarded.

Responsible AI Mapping:
- Reliability & Safety: Reduces false alarms with evidence thresholds
- Accountability: Archived items remain reviewable for audit
"""

from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Any
from enum import Enum
from datetime import datetime


class SignalStatus(Enum):
    """Status of a classified signal."""
    SURFACED = "surfaced"  # High confidence, sufficient evidence
    ARCHIVED = "archived"  # Low confidence or low volume (noise)


@dataclass
class ArchiveReason:
    """Reason for archiving a signal as noise."""
    code: str
    description: str
    threshold_value: float
    actual_value: float


@dataclass
class GatedSignal:
    """A signal after gating decision."""
    event_id: str
    predicted_class: str
    confidence: float
    status: SignalStatus
    archive_reason: ArchiveReason = None
    classification_result: Any = None  # Original ClassificationResult


@dataclass
class GatingResult:
    """Result of the signal gating process."""
    signals: List[GatedSignal]  # Surfaced signals
    noise: List[GatedSignal]    # Archived signals
    total_processed: int
    signal_count: int
    noise_count: int
    gating_summary: Dict[str, Any]


class SignalGate:
    """
    Gates classified signals into Signal vs Noise.
    Uses multiple thresholds to ensure reliability.
    """
    
    # Minimum confidence to be considered a signal (not noise)
    CONFIDENCE_THRESHOLD = 0.35
    
    # Higher threshold for sensitive categories
    SENSITIVE_CLASS_THRESHOLDS = {
        'FRAUD': 0.40,
        'MISINFORMATION': 0.45,
    }
    
    # Minimum volume for low-confidence signals to still be surfaced
    LOW_CONFIDENCE_VOLUME_THRESHOLD = 3
    
    # Archive reasons
    REASON_LOW_CONFIDENCE = "low_confidence"
    REASON_NOISE_CLASS = "noise_class"
    REASON_ISOLATED = "isolated_signal"
    
    def __init__(self):
        self.archive_counts: Dict[str, int] = {}
    
    def _get_confidence_threshold(self, predicted_class: str) -> float:
        """Get the confidence threshold for a class."""
        return self.SENSITIVE_CLASS_THRESHOLDS.get(
            predicted_class, 
            self.CONFIDENCE_THRESHOLD
        )
    
    def _should_archive(
        self, 
        result: Any,  # ClassificationResult
        cluster_volume: int = 1
    ) -> Tuple[bool, ArchiveReason]:
        """
        Determine if a result should be archived.
        
        Args:
            result: ClassificationResult from classifier
            cluster_volume: Number of similar signals (for volume check)
            
        Returns:
            Tuple of (should_archive, archive_reason)
        """
        # Rule 1: If classified as NOISE, archive it
        if result.predicted_class == 'NOISE':
            return True, ArchiveReason(
                code=self.REASON_NOISE_CLASS,
                description="Classified as routine noise (password reset, balance inquiry, etc.)",
                threshold_value=0.0,
                actual_value=result.confidence
            )
        
        # Rule 2: Low confidence check
        threshold = self._get_confidence_threshold(result.predicted_class)
        if result.confidence < threshold:
            # Exception: If volume is high enough, still surface it
            if cluster_volume >= self.LOW_CONFIDENCE_VOLUME_THRESHOLD:
                return False, None
            
            return True, ArchiveReason(
                code=self.REASON_LOW_CONFIDENCE,
                description=f"Confidence below threshold for {result.predicted_class}",
                threshold_value=threshold,
                actual_value=result.confidence
            )
        
        # Rule 3: Isolated signals with borderline confidence
        if result.confidence < (threshold + 0.10) and cluster_volume == 1:
            return True, ArchiveReason(
                code=self.REASON_ISOLATED,
                description="Single isolated signal with borderline confidence",
                threshold_value=threshold + 0.10,
                actual_value=result.confidence
            )
        
        return False, None
    
    def gate_signals(
        self, 
        classification_results: List[Any],  # List[ClassificationResult]
        volume_map: Dict[str, int] = None
    ) -> GatingResult:
        """
        Gate a batch of classification results into signals vs noise.
        
        Args:
            classification_results: List of ClassificationResult objects
            volume_map: Optional mapping of event_id to cluster volume
            
        Returns:
            GatingResult with separated signals and noise
        """
        if volume_map is None:
            volume_map = {}
        
        signals = []
        noise = []
        archive_reasons_summary = {}
        
        for result in classification_results:
            volume = volume_map.get(result.event_id, 1)
            should_archive, reason = self._should_archive(result, volume)
            
            gated = GatedSignal(
                event_id=result.event_id,
                predicted_class=result.predicted_class,
                confidence=result.confidence,
                status=SignalStatus.ARCHIVED if should_archive else SignalStatus.SURFACED,
                archive_reason=reason,
                classification_result=result
            )
            
            if should_archive:
                noise.append(gated)
                # Track reason counts
                reason_code = reason.code if reason else "unknown"
                archive_reasons_summary[reason_code] = archive_reasons_summary.get(reason_code, 0) + 1
            else:
                signals.append(gated)
        
        return GatingResult(
            signals=signals,
            noise=noise,
            total_processed=len(classification_results),
            signal_count=len(signals),
            noise_count=len(noise),
            gating_summary={
                "signal_rate": len(signals) / max(len(classification_results), 1),
                "noise_rate": len(noise) / max(len(classification_results), 1),
                "archive_reasons": archive_reasons_summary,
                "thresholds_used": {
                    "default": self.CONFIDENCE_THRESHOLD,
                    **self.SENSITIVE_CLASS_THRESHOLDS
                }
            }
        )
    
    def get_archive_summary(self, gating_result: GatingResult) -> str:
        """
        Generate a human-readable summary of archived signals.
        
        Args:
            gating_result: The result from gate_signals
            
        Returns:
            Formatted summary string
        """
        lines = [
            f"Archived (Noise): {gating_result.noise_count} items",
            ""
        ]
        
        if gating_result.noise_count == 0:
            lines.append("No items archived.")
            return "\n".join(lines)
        
        # Group by reason
        reason_groups = {}
        for item in gating_result.noise:
            reason = item.archive_reason.code if item.archive_reason else "unknown"
            if reason not in reason_groups:
                reason_groups[reason] = []
            reason_groups[reason].append(item)
        
        for reason, items in reason_groups.items():
            description = items[0].archive_reason.description if items[0].archive_reason else "Unknown reason"
            lines.append(f"• {description}: {len(items)} items")
        
        return "\n".join(lines)
    
    def get_noise_details(self, gating_result: GatingResult) -> List[Dict[str, Any]]:
        """
        Get detailed information about archived items for UI display.
        
        Args:
            gating_result: The result from gate_signals
            
        Returns:
            List of dictionaries with noise item details
        """
        details = []
        for item in gating_result.noise:
            details.append({
                "event_id": item.event_id,
                "predicted_class": item.predicted_class,
                "confidence": f"{item.confidence:.1%}",
                "reason_code": item.archive_reason.code if item.archive_reason else "unknown",
                "reason_description": item.archive_reason.description if item.archive_reason else "Unknown",
                "threshold": item.archive_reason.threshold_value if item.archive_reason else None,
                "actual": item.archive_reason.actual_value if item.archive_reason else None,
                "reviewable": True,  # All items remain reviewable
                "archived_at": datetime.now().isoformat()
            })
        return details


# Singleton instance
_gate = None

def get_signal_gate() -> SignalGate:
    """Get the singleton SignalGate instance."""
    global _gate
    if _gate is None:
        _gate = SignalGate()
    return _gate


# Convenience function
def gate_signals(
    classification_results: List[Any],
    volume_map: Dict[str, int] = None
) -> GatingResult:
    """Gate classification results into signals vs noise."""
    return get_signal_gate().gate_signals(classification_results, volume_map)


if __name__ == "__main__":
    # Demo with mock classification results
    from dataclasses import dataclass
    
    @dataclass
    class MockResult:
        event_id: str
        predicted_class: str
        confidence: float
        class_probabilities: dict = field(default_factory=dict)
        top_keywords: list = field(default_factory=list)
        raw_text: str = ""
    
    mock_results = [
        MockResult("e1", "SERVICE", 0.85),
        MockResult("e2", "FRAUD", 0.72),
        MockResult("e3", "NOISE", 0.90),
        MockResult("e4", "MISINFORMATION", 0.35),  # Below threshold
        MockResult("e5", "SENTIMENT", 0.45),
        MockResult("e6", "SERVICE", 0.25),  # Low confidence
    ]
    
    gate = SignalGate()
    result = gate.gate_signals(mock_results)
    
    print("=== Signal Gating Demo ===\n")
    print(f"Total processed: {result.total_processed}")
    print(f"Signals (surfaced): {result.signal_count}")
    print(f"Noise (archived): {result.noise_count}")
    print()
    print("Surfaced signals:")
    for s in result.signals:
        print(f"  • {s.event_id}: {s.predicted_class} ({s.confidence:.1%})")
    print()
    print(gate.get_archive_summary(result))
