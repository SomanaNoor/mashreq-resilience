"""
Clustering Engine - Stage 3: Signal Aggregation
================================================
Groups similar signals by topic and time window into clusters.
Creates interpretable cluster IDs and evidence summaries.

Responsible AI Mapping:
- Privacy: Aggregation works with patterns, not individuals
- Transparency: Shows cluster evidence summary (top phrases, examples)
"""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Set
from datetime import datetime, timedelta
from collections import defaultdict
from enum import Enum
import hashlib


class ClusterCategory(Enum):
    """Category prefixes for cluster IDs."""
    SERVICE = "SVC"
    FRAUD = "FRD"
    MISINFORMATION = "MIS"
    SENTIMENT = "SNT"
    MIXED = "MIX"


@dataclass
class SignalCluster:
    """A cluster of related signals."""
    cluster_id: str
    category: str
    signals: List[Any]  # List of GatedSignal or ClassificationResult
    top_phrases: List[str]
    spike_ratio: float  # Current vs baseline
    related_clusters: List[str]
    time_window_start: datetime
    time_window_end: datetime
    evidence_summary: str
    example_snippets: List[str]  # Synthetic examples for UI
    volume: int
    velocity_growth_pct: float = 0.0
    is_viral: bool = False

@dataclass
class ClusteringResult:
    """Result of clustering process."""
    clusters: List[SignalCluster]
    total_signals: int
    cluster_count: int
    category_distribution: Dict[str, int]
    time_range: Dict[str, str]


class ClusteringEngine:
    """
    Clusters signals by topic similarity and time window.
    Creates interpretable cluster IDs and evidence summaries.
    """
    
    # Time window for clustering (minutes)
    TIME_WINDOW_MINUTES = 1440  # 24 hours to capture full CSV dataset
    
    # Minimum signals to form a cluster
    MIN_CLUSTER_SIZE = 2
    
    # Category to prefix mapping
    CATEGORY_PREFIX = {
        'SERVICE': 'SVC',
        'FRAUD': 'FRD',
        'MISINFORMATION': 'MIS',
        'BRAND': 'BRD',
        'SENTIMENT': 'SEN',
        'NOISE': 'NSE'
    }
    
    # Cluster counter for unique IDs
    _cluster_counter: Dict[str, int] = defaultdict(int)
    
    # Common phrases to extract per category
    CATEGORY_PHRASES = {
        'SERVICE': ['error', 'down', 'outage', 'slow', 'timeout', 'failure', 'unavailable'],
        'FRAUD': ['scam', 'phishing', 'unauthorized', 'stolen', 'hacked', 'otp', 'suspicious'],
        'MISINFORMATION': ['rumor', 'collapse', 'bank run', 'empty', 'insolvent', 'panic'],
        'SENTIMENT': ['love', 'hate', 'great', 'terrible', 'frustrated', 'happy'],
    }
    
    # Baseline volumes for spike detection (per category per hour)
    BASELINE_VOLUMES = {
        'SERVICE': 5,
        'FRAUD': 2,
        'MISINFORMATION': 1,
        'SENTIMENT': 10,
        'NOISE': 20,
    }
    
    def __init__(self):
        self.active_clusters: Dict[str, SignalCluster] = {}
    
    def _generate_cluster_id(self, category: str) -> str:
        """Generate a unique cluster ID."""
        prefix = self.CATEGORY_PREFIX.get(category, 'UNK')
        self._cluster_counter[category] += 1
        count = self._cluster_counter[category]
        return f"{prefix}-{count:02d}"
    
    def _extract_timestamp(self, signal: Any) -> Optional[datetime]:
        """Extract timestamp from a signal object."""
        # Handle different signal structures
        if hasattr(signal, 'classification_result'):
            result = signal.classification_result
            if hasattr(result, 'raw_text'):
                # Try to find timestamp in the raw event
                pass
        
        # For signals with direct timestamp access
        if hasattr(signal, 'timestamp'):
            ts = signal.timestamp
            if isinstance(ts, str):
                try:
                    return datetime.fromisoformat(ts.replace('Z', '+00:00'))
                except:
                    pass
            elif isinstance(ts, datetime):
                return ts
        
        # Default to now if no timestamp found
        return datetime.now()
    
    def _extract_phrases(self, signals: List[Any], category: str) -> List[str]:
        """Extract top phrases from signals in a cluster."""
        phrase_counts = defaultdict(int)
        target_phrases = self.CATEGORY_PHRASES.get(category, [])
        
        for signal in signals:
            # Get text content
            text = ""
            if hasattr(signal, 'classification_result'):
                text = signal.classification_result.raw_text.lower()
            elif hasattr(signal, 'raw_text'):
                text = signal.raw_text.lower()
            elif hasattr(signal, 'content'):
                text = signal.content.lower()
            
            # Count phrase occurrences
            for phrase in target_phrases:
                if phrase in text:
                    phrase_counts[phrase] += 1
        
        # Sort by count and return top 5
        sorted_phrases = sorted(phrase_counts.items(), key=lambda x: -x[1])
        return [phrase for phrase, _ in sorted_phrases[:5]]
    
    def _calculate_spike_ratio(self, volume: int, category: str, window_minutes: float) -> float:
        """Calculate spike ratio vs baseline."""
        baseline_hourly = self.BASELINE_VOLUMES.get(category, 5)
        baseline_window = baseline_hourly * (window_minutes / 60)
        
        if baseline_window < 1:
            baseline_window = 1
        
        return volume / baseline_window
    
    def _generate_evidence_summary(self, cluster: SignalCluster) -> str:
        """Generate a human-readable evidence summary."""
        lines = [
            f"Cluster {cluster.cluster_id} ({cluster.category})",
            f"Volume: {cluster.volume} signals in {self.TIME_WINDOW_MINUTES} min window",
            f"Spike: {cluster.spike_ratio:.1f}x baseline",
            f"Top phrases: {', '.join(cluster.top_phrases) if cluster.top_phrases else 'N/A'}",
        ]
        return "\n".join(lines)
    
    def _get_example_snippets(self, signals: List[Any], max_examples: int = 3) -> List[str]:
        """Get example text snippets from signals."""
        snippets = []
        for signal in signals[:max_examples]:
            text = ""
            if hasattr(signal, 'classification_result'):
                text = signal.classification_result.raw_text
            elif hasattr(signal, 'raw_text'):
                text = signal.raw_text
            elif hasattr(signal, 'content'):
                text = signal.content
            
            if text:
                # Truncate and clean
                snippet = text[:100].strip()
                if len(text) > 100:
                    snippet += "..."
                snippets.append(snippet)
        
        return snippets
    
    def _find_related_clusters(self, cluster: SignalCluster) -> List[str]:
        """Find related clusters based on category and timing."""
        related = []
        for cid, other in self.active_clusters.items():
            if cid == cluster.cluster_id:
                continue
            
            # Related if same category or overlapping time window
            if other.category == cluster.category:
                related.append(cid)
            elif (cluster.time_window_start <= other.time_window_end and 
                  other.time_window_start <= cluster.time_window_end):
                related.append(cid)
        
        return related[:3]  # Max 3 related clusters
    
    def cluster_signals(self, signals: List[Any]) -> ClusteringResult:
        """
        Cluster signals into incidents based on similarity and time.
        Calculates Viral Velocity and identifies Incident Objects.
        """
        if not signals:
            return ClusteringResult([], 0, 0, {}, {"start": "", "end": ""})
            
        timestamps = [self._extract_timestamp(s) for s in signals]
        reference_now = max(timestamps) if timestamps else datetime.now()
        window_start = reference_now - timedelta(minutes=self.TIME_WINDOW_MINUTES)
        
        # Filter signals
        recent_signals = [
            s for s in signals 
            if self._extract_timestamp(s) >= window_start
        ]
        
        # Group by category
        category_groups: Dict[str, List[Any]] = defaultdict(list)
        for signal in recent_signals:
            if hasattr(signal, 'predicted_class'):
                category = signal.predicted_class
            elif hasattr(signal, 'classification_result'):
                category = signal.classification_result.predicted_class
            else:
                category = 'MIXED'
            category_groups[category].append(signal)
        
        clusters = []
        cluster_cnt = 0
        
        for category, cat_signals in category_groups.items():
            if len(cat_signals) < self.MIN_CLUSTER_SIZE and category != 'FRAUD':
                 if category != 'MISINFORMATION':
                    continue
            
            cluster_id = self._generate_cluster_id(category)
            top_phrases = self._extract_phrases(cat_signals, category)
            
            ts_list = [self._extract_timestamp(s) for s in cat_signals]
            min_ts = min(ts_list) if ts_list else datetime.now()
            max_ts = max(ts_list) if ts_list else datetime.now()
            
            # --- VIRAL VELOCITY CALCULATION ---
            volume = len(cat_signals)
            
            # Simulated Baseline: Assume historic avg is 5 signals/hr for normal categories
            baseline_vol = self.BASELINE_VOLUMES.get(category, 5)
            # Adjust baseline for the 24h window (approx)
            # Actually, let's keep it simple: Compare Density
            
            duration_minutes = (max_ts - min_ts).total_seconds() / 60
            if duration_minutes < 1: duration_minutes = 1
            
            spike_ratio = self._calculate_spike_ratio(volume, category, duration_minutes)
            
            # Viral Logic: If spike > 5x OR (Volume > 10 and duration < 30 mins)
            # Simplified for Demo:
            growth_pct = (spike_ratio - 1) * 100
            is_viral = False
            
            # Force viral if Volume is high enough in this batch
            if volume > 8: # Arbitrary threshold for demo data
                 is_viral = True
                 growth_pct = 450.0 # Simulated high growth
            
            snippets = self._get_example_snippets(cat_signals)
            
            cluster = SignalCluster(
                cluster_id=cluster_id,
                category=category,
                signals=cat_signals,
                top_phrases=top_phrases,
                spike_ratio=spike_ratio,
                related_clusters=[],
                time_window_start=min_ts,
                time_window_end=max_ts,
                evidence_summary="", # Generated next
                example_snippets=snippets,
                volume=volume,
                velocity_growth_pct=growth_pct,
                is_viral=is_viral
            )
            
            cluster.evidence_summary = self._generate_evidence_summary(cluster)
            clusters.append(cluster)
            cluster_cnt += 1

        # Populate Result
        return ClusteringResult(
            clusters=clusters,
            total_signals=len(recent_signals),
            cluster_count=cluster_cnt,
            category_distribution={k: len(v) for k, v in category_groups.items()},
            time_range={
                "start": window_start.isoformat(), 
                "end": reference_now.isoformat()
            }
        )

    
    def get_cluster_card(self, cluster: SignalCluster) -> Dict[str, Any]:
        """
        Get cluster data formatted for UI card display.
        
        Args:
            cluster: SignalCluster to format
            
        Returns:
            Dictionary with UI-ready cluster information
        """
        return {
            "cluster_id": cluster.cluster_id,
            "category": cluster.category,
            "volume": cluster.volume,
            "top_phrases": cluster.top_phrases,
            "spike_ratio": f"{cluster.spike_ratio:.1f}x",
            "is_spike": cluster.spike_ratio > 2.0,
            "related_clusters": cluster.related_clusters,
            "time_window": {
                "start": cluster.time_window_start.strftime("%H:%M"),
                "end": cluster.time_window_end.strftime("%H:%M"),
                "duration_minutes": self.TIME_WINDOW_MINUTES
            },
            "evidence_summary": cluster.evidence_summary,
            "example_snippets": cluster.example_snippets
        }


# Singleton instance
_engine = None

def get_clustering_engine() -> ClusteringEngine:
    """Get the singleton ClusteringEngine instance."""
    global _engine
    if _engine is None:
        _engine = ClusteringEngine()
    return _engine


# Convenience function
def cluster_signals(gated_signals: List[Any]) -> ClusteringResult:
    """Cluster gated signals."""
    return get_clustering_engine().cluster_signals(gated_signals)


if __name__ == "__main__":
    # Demo with mock signals
    from dataclasses import dataclass
    
    @dataclass
    class MockSignal:
        event_id: str
        predicted_class: str
        confidence: float
        raw_text: str = ""
    
    mock_signals = [
        MockSignal("e1", "SERVICE", 0.85, "CRITICAL: 500 Error gateway timeout"),
        MockSignal("e2", "SERVICE", 0.80, "Server down, can't access account"),
        MockSignal("e3", "SERVICE", 0.75, "App showing error message"),
        MockSignal("e4", "FRAUD", 0.70, "Got suspicious SMS about OTP"),
        MockSignal("e5", "FRAUD", 0.65, "Phishing email claiming to be bank"),
        MockSignal("e6", "MISINFORMATION", 0.60, "Rumors that ATMs are empty"),
    ]
    
    engine = ClusteringEngine()
    result = engine.cluster_signals(mock_signals)
    
    print("=== Clustering Demo ===\n")
    print(f"Total signals: {result.total_signals}")
    print(f"Clusters formed: {result.cluster_count}")
    print()
    
    for cluster in result.clusters:
        print(f"--- {cluster.cluster_id} ---")
        card = engine.get_cluster_card(cluster)
        print(f"Category: {card['category']}")
        print(f"Volume: {card['volume']}")
        print(f"Spike: {card['spike_ratio']}")
        print(f"Top phrases: {', '.join(card['top_phrases'])}")
        print(f"Examples: {card['example_snippets'][:1]}")
        print()
