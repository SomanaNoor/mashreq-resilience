"""
Confidence Scorer - Stage 5: Confidence Scoring with Uncertainty
=================================================================
Derives confidence percentage with uncertainty wording.

Inputs:
- Naïve Bayes probability margin
- Cluster size
- Signal consistency

Output:
- Confidence percentage
- Label (High/Medium/Low)
- Uncertainty reason

Responsible AI Mapping:
- Reliability & Safety: Explicit uncertainty handling prevents overreaction
"""

from dataclasses import dataclass
from typing import Any, List, Optional
from enum import Enum


class ConfidenceLevel(Enum):
    """Confidence level labels."""
    HIGH = "High"
    MEDIUM_HIGH = "Medium-High"
    MEDIUM = "Medium"
    LOW = "Low"


@dataclass
class ConfidenceScore:
    """Complete confidence score with uncertainty wording."""
    percentage: float  # 0-100
    level: ConfidenceLevel
    reason: str
    uncertainty_wording: str
    components: dict  # Breakdown of confidence factors
    
    def get_display_text(self) -> str:
        """Get formatted display text."""
        return f"Confidence {self.percentage:.0f}% ({self.level.value}): {self.reason}"


class ConfidenceScorer:
    """
    Calculates confidence scores with explicit uncertainty handling.
    """
    
    # Weights for confidence components
    WEIGHT_NB_MARGIN = 0.4  # Naïve Bayes probability margin
    WEIGHT_CLUSTER_SIZE = 0.3  # Volume/size factor
    WEIGHT_CONSISTENCY = 0.3  # Signal consistency
    
    # Thresholds for confidence levels
    LEVEL_THRESHOLDS = [
        (80, ConfidenceLevel.HIGH),
        (65, ConfidenceLevel.MEDIUM_HIGH),
        (45, ConfidenceLevel.MEDIUM),
        (0, ConfidenceLevel.LOW),
    ]
    
    # Uncertainty wording templates
    UNCERTAINTY_TEMPLATES = {
        ConfidenceLevel.HIGH: "Strong evidence supports this classification",
        ConfidenceLevel.MEDIUM_HIGH: "Good evidence with some uncertainty",
        ConfidenceLevel.MEDIUM: "Mixed signals; recommend additional review",
        ConfidenceLevel.LOW: "Limited evidence; treat as preliminary",
    }
    
    def __init__(self):
        pass
    
    def _calculate_nb_margin(self, cluster: Any) -> tuple[float, str]:
        """
        Calculate confidence factor from Naïve Bayes probability margins.
        Returns score (0-100) and description.
        """
        margins = []
        
        signals = cluster.signals if hasattr(cluster, 'signals') else []
        for signal in signals:
            # Get class probabilities
            probs = None
            if hasattr(signal, 'classification_result'):
                result = signal.classification_result
                if hasattr(result, 'class_probabilities'):
                    probs = result.class_probabilities
                elif hasattr(result, 'confidence'):
                    margins.append(result.confidence)
                    continue
            elif hasattr(signal, 'class_probabilities'):
                probs = signal.class_probabilities
            elif hasattr(signal, 'confidence'):
                margins.append(signal.confidence)
                continue
            
            if probs:
                # Margin = top probability - second probability
                sorted_probs = sorted(probs.values(), reverse=True)
                if len(sorted_probs) >= 2:
                    margin = sorted_probs[0] - sorted_probs[1]
                    margins.append(margin)
                elif sorted_probs:
                    margins.append(sorted_probs[0])
        
        if not margins:
            return 50.0, "No probability data available"
        
        avg_margin = sum(margins) / len(margins)
        
        # Convert margin to 0-100 score (margin of 0.5 = 100%)
        score = min(100, (avg_margin / 0.5) * 100)
        
        if avg_margin >= 0.4:
            desc = "Strong probability margins"
        elif avg_margin >= 0.25:
            desc = "Moderate probability margins"
        elif avg_margin >= 0.1:
            desc = "Narrow probability margins"
        else:
            desc = "Very narrow margins (ambiguous)"
        
        return score, desc
    
    def _calculate_cluster_size_factor(self, cluster: Any) -> tuple[float, str]:
        """
        Calculate confidence factor from cluster size.
        Returns score (0-100) and description.
        """
        volume = cluster.volume if hasattr(cluster, 'volume') else len(cluster.signals)
        
        # Larger clusters = more confidence
        if volume >= 10:
            score = 100
            desc = f"Large cluster ({volume} signals)"
        elif volume >= 5:
            score = 80
            desc = f"Medium cluster ({volume} signals)"
        elif volume >= 3:
            score = 60
            desc = f"Small cluster ({volume} signals)"
        elif volume >= 2:
            score = 40
            desc = f"Minimal cluster ({volume} signals)"
        else:
            score = 20
            desc = "Single signal (isolated)"
        
        return score, desc
    
    def _calculate_consistency_factor(self, cluster: Any) -> tuple[float, str]:
        """
        Calculate confidence factor from signal consistency.
        Returns score (0-100) and description.
        """
        signals = cluster.signals if hasattr(cluster, 'signals') else []
        
        if not signals:
            return 50.0, "No signals to analyze"
        
        # Check classification consistency
        classifications = []
        for signal in signals:
            if hasattr(signal, 'predicted_class'):
                classifications.append(signal.predicted_class)
            elif hasattr(signal, 'classification_result'):
                classifications.append(signal.classification_result.predicted_class)
        
        if not classifications:
            return 50.0, "No classification data"
        
        # Calculate consistency as percentage of most common class
        from collections import Counter
        counts = Counter(classifications)
        most_common_count = counts.most_common(1)[0][1]
        consistency = most_common_count / len(classifications)
        
        score = consistency * 100
        
        if consistency >= 0.9:
            desc = "Highly consistent signals"
        elif consistency >= 0.7:
            desc = "Mostly consistent signals"
        elif consistency >= 0.5:
            desc = "Mixed signal types"
        else:
            desc = "Inconsistent signals"
        
        return score, desc
    
    def _get_confidence_level(self, percentage: float) -> ConfidenceLevel:
        """Get confidence level for a percentage."""
        for threshold, level in self.LEVEL_THRESHOLDS:
            if percentage >= threshold:
                return level
        return ConfidenceLevel.LOW
    
    def _generate_reason(self, components: dict, level: ConfidenceLevel) -> str:
        """Generate human-readable reason for confidence level."""
        reasons = []
        
        # Add component-specific reasons
        nb_score = components['nb_margin']['score']
        size_score = components['cluster_size']['score']
        consistency_score = components['consistency']['score']
        
        if nb_score < 50:
            reasons.append("ambiguous classification")
        if size_score < 50:
            reasons.append("limited volume")
        if consistency_score < 60:
            reasons.append("mixed signals")
        
        if not reasons:
            if level == ConfidenceLevel.HIGH:
                return "Strong evidence across all factors"
            return "Balanced evidence"
        
        return " + ".join(reasons)
    
    def calculate_confidence(self, cluster: Any) -> ConfidenceScore:
        """
        Calculate confidence score for a cluster.
        
        Args:
            cluster: SignalCluster object
            
        Returns:
            ConfidenceScore with percentage, level, and uncertainty wording
        """
        # Calculate each component
        nb_score, nb_desc = self._calculate_nb_margin(cluster)
        size_score, size_desc = self._calculate_cluster_size_factor(cluster)
        consistency_score, consistency_desc = self._calculate_consistency_factor(cluster)
        
        components = {
            'nb_margin': {'score': nb_score, 'description': nb_desc, 'weight': self.WEIGHT_NB_MARGIN},
            'cluster_size': {'score': size_score, 'description': size_desc, 'weight': self.WEIGHT_CLUSTER_SIZE},
            'consistency': {'score': consistency_score, 'description': consistency_desc, 'weight': self.WEIGHT_CONSISTENCY},
        }
        
        # Calculate weighted average
        weighted_sum = (
            nb_score * self.WEIGHT_NB_MARGIN +
            size_score * self.WEIGHT_CLUSTER_SIZE +
            consistency_score * self.WEIGHT_CONSISTENCY
        )
        
        percentage = round(weighted_sum, 1)
        level = self._get_confidence_level(percentage)
        reason = self._generate_reason(components, level)
        uncertainty = self.UNCERTAINTY_TEMPLATES[level]
        
        return ConfidenceScore(
            percentage=percentage,
            level=level,
            reason=reason,
            uncertainty_wording=uncertainty,
            components=components
        )
    
    def get_uncertainty_badge(self, confidence: ConfidenceScore) -> dict:
        """
        Get badge data for UI display.
        
        Args:
            confidence: ConfidenceScore object
            
        Returns:
            Dictionary with badge styling info
        """
        colors = {
            ConfidenceLevel.HIGH: {'bg': '#E6F4EA', 'text': '#1E8E3E', 'icon': '✓'},
            ConfidenceLevel.MEDIUM_HIGH: {'bg': '#E8F0FE', 'text': '#1967D2', 'icon': '◐'},
            ConfidenceLevel.MEDIUM: {'bg': '#FEF7E0', 'text': '#EA8600', 'icon': '◑'},
            ConfidenceLevel.LOW: {'bg': '#FCE8E6', 'text': '#D93025', 'icon': '?'},
        }
        
        style = colors.get(confidence.level, colors[ConfidenceLevel.MEDIUM])
        
        return {
            "text": f"{confidence.percentage:.0f}% ({confidence.level.value})",
            "background_color": style['bg'],
            "text_color": style['text'],
            "icon": style['icon'],
            "tooltip": confidence.uncertainty_wording
        }


# Singleton instance
_scorer = None

def get_confidence_scorer() -> ConfidenceScorer:
    """Get the singleton ConfidenceScorer instance."""
    global _scorer
    if _scorer is None:
        _scorer = ConfidenceScorer()
    return _scorer


# Convenience function
def calculate_confidence(cluster: Any) -> ConfidenceScore:
    """Calculate confidence score for a cluster."""
    return get_confidence_scorer().calculate_confidence(cluster)


if __name__ == "__main__":
    # Demo with mock cluster
    from dataclasses import dataclass
    
    @dataclass
    class MockSignal:
        predicted_class: str
        confidence: float
        class_probabilities: dict
    
    @dataclass
    class MockCluster:
        signals: list
        
        @property
        def volume(self):
            return len(self.signals)
    
    # High confidence example
    high_conf_cluster = MockCluster(
        signals=[
            MockSignal("FRAUD", 0.85, {"FRAUD": 0.85, "SERVICE": 0.10, "NOISE": 0.05}),
            MockSignal("FRAUD", 0.82, {"FRAUD": 0.82, "SERVICE": 0.12, "NOISE": 0.06}),
            MockSignal("FRAUD", 0.78, {"FRAUD": 0.78, "SERVICE": 0.15, "NOISE": 0.07}),
            MockSignal("FRAUD", 0.80, {"FRAUD": 0.80, "SERVICE": 0.13, "NOISE": 0.07}),
            MockSignal("FRAUD", 0.75, {"FRAUD": 0.75, "SERVICE": 0.18, "NOISE": 0.07}),
        ]
    )
    
    # Low confidence example
    low_conf_cluster = MockCluster(
        signals=[
            MockSignal("SERVICE", 0.45, {"SERVICE": 0.45, "NOISE": 0.40, "SENTIMENT": 0.15}),
        ]
    )
    
    scorer = ConfidenceScorer()
    
    print("=== Confidence Scoring Demo ===\n")
    
    print("High Confidence Cluster:")
    conf = scorer.calculate_confidence(high_conf_cluster)
    print(f"  {conf.get_display_text()}")
    print(f"  Uncertainty: {conf.uncertainty_wording}")
    badge = scorer.get_uncertainty_badge(conf)
    print(f"  Badge: {badge['icon']} {badge['text']}")
    print()
    
    print("Low Confidence Cluster:")
    conf = scorer.calculate_confidence(low_conf_cluster)
    print(f"  {conf.get_display_text()}")
    print(f"  Uncertainty: {conf.uncertainty_wording}")
    badge = scorer.get_uncertainty_badge(conf)
    print(f"  Badge: {badge['icon']} {badge['text']}")
