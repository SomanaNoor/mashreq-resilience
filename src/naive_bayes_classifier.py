"""
Naïve Bayes Classifier - Stage 1: Keyword Feature Extraction + Classification
==============================================================================
Implements interpretable classification with visible token contributions.

Classes:
- SERVICE: Service issues, outages, technical problems
- FRAUD: Fraud indicators, scams, suspicious activity
- MISINFORMATION: Rumors, false information, panic-inducing content
- SENTIMENT: General sentiment (complaints, praise, feedback)
- NOISE: Routine inquiries, background noise

Responsible AI Mapping:
- Transparency: Shows top contributing keywords + class probabilities
- Fairness: Excludes sensitive proxies (names, demographics, locations)
"""

import re
import json
import pickle
import numpy as np
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional, Any
from collections import defaultdict


@dataclass
class ClassificationResult:
    """Result of classifying a single event."""
    event_id: str
    predicted_class: str
    confidence: float
    class_probabilities: Dict[str, float]
    top_keywords: List[Tuple[str, float]]  # (keyword, contribution)
    raw_text: str


@dataclass
class BatchClassificationResult:
    """Result of classifying a batch of events."""
    results: List[ClassificationResult]
    class_distribution: Dict[str, int]
    average_confidence: float


class NaiveBayesClassifier:
    """
    Multinomial Naïve Bayes classifier for banking operational signals.
    Provides interpretable predictions with keyword contributions.
    """
    
    # Signal categories
    CLASSES = ['SERVICE', 'FRAUD', 'MISINFORMATION', 'SENTIMENT', 'NOISE']
    
    # Domain-specific keyword dictionaries for each class
    CLASS_KEYWORDS = {
        'SERVICE': {
            # Technical issues
            'error': 3.0, '500': 3.5, 'timeout': 3.0, 'down': 2.5, 'outage': 3.5,
            'failure': 3.0, 'crashed': 3.0, 'unavailable': 2.5, 'slow': 2.0,
            'latency': 2.5, 'connection': 2.0, 'server': 2.0, 'database': 2.5,
            'api': 2.0, 'gateway': 2.5, 'critical': 2.5, 'warning': 2.0,
            'not working': 3.0, "can't login": 2.5, 'broken': 2.5, 'issue': 2.0,
            'maintenance': 1.5, 'downtime': 3.0, 'atm': 2.0, 'stuck': 2.0,
            'frozen': 2.5, 'hang': 2.0, 'unresponsive': 2.5
        },
        'FRAUD': {
            # Fraud indicators
            'scam': 3.5, 'fraud': 3.5, 'suspicious': 3.0, 'phishing': 3.5,
            'unauthorized': 3.0, 'stolen': 3.0, 'hacked': 3.0, 'breach': 3.0,
            'otp': 2.5, 'sms': 2.0, 'impersonation': 3.0, 'fake': 2.5,
            'cybercrime': 3.5, 'identity theft': 3.5, 'compromised': 3.0,
            'malware': 3.0, 'ransomware': 3.5, 'trojan': 3.0, 'keylogger': 3.0,
            'unknown transaction': 3.0, 'didn\'t authorize': 3.0, 'not mine': 2.5,
            'card cloned': 3.5, 'skimmed': 3.5
        },
        'MISINFORMATION': {
            # Rumors and false info
            'rumor': 3.5, 'rumour': 3.5, 'heard that': 2.5, 'people saying': 2.5,
            'bank run': 3.5, 'collapse': 3.0, 'insolvent': 3.5, 'bankrupt': 3.5,
            'failing': 2.5, 'run out of money': 3.5, 'no cash': 3.0,
            'breaking': 2.0, 'alert': 1.5, 'urgent': 2.0, 'warning': 1.5,
            'atm empty': 3.0, 'withdrawal limit': 2.0, 'money safe': 2.5,
            'close account': 2.5, 'move money': 2.5, 'panic': 3.0,
            'crisis': 2.5, 'emergency': 2.0
        },
        'SENTIMENT': {
            # Customer sentiment
            'love': 2.0, 'hate': 2.5, 'best': 2.0, 'worst': 2.5, 'great': 2.0,
            'terrible': 2.5, 'amazing': 2.0, 'awful': 2.5, 'happy': 2.0,
            'angry': 2.5, 'frustrated': 2.5, 'satisfied': 2.0, 'disappointed': 2.5,
            'recommend': 2.0, 'avoid': 2.5, 'complaint': 2.5, 'feedback': 2.0,
            'experience': 1.5, 'service': 1.5, 'staff': 1.5, 'branch': 1.5,
            'thank': 2.0, 'thanks': 2.0, 'helpful': 2.0, 'rude': 2.5,
            'unprofessional': 2.5, 'excellent': 2.0
        },
        'NOISE': {
            # Routine/background
            'password': 2.5, 'forgot': 2.0, 'reset': 2.0, 'login': 1.5,
            'balance': 2.0, 'check': 1.5, 'hours': 2.0, 'branch': 1.5,
            'location': 2.0, 'atm location': 2.5, 'card': 1.5, 'new card': 2.0,
            'activate': 2.0, 'statement': 2.0, 'transfer': 1.5, 'how to': 2.0,
            'what is': 2.0, 'where': 1.5, 'when': 1.5, 'fee': 1.5,
            'information': 1.5, 'inquiry': 2.0, 'question': 2.0
        }
    }
    
    # Sensitive proxies to exclude
    EXCLUDED_PATTERNS = [
        r'\b(mr|mrs|ms|dr)\.\s*[a-z]+\b',  # Names with titles
        r'\b[a-z]+\s+(street|road|avenue|blvd)\b',  # Addresses
        r'\b(male|female|man|woman)\b',  # Gender
        r'\b\d{1,2}[-/]\d{1,2}[-/]\d{2,4}\b',  # Dates of birth
        r'\bnationality\b', r'\bethnic\b', r'\breligion\b'  # Demographics
    ]
    
    def __init__(self):
        """Initialize the classifier with pre-built vocabulary."""
        self.class_priors = {cls: 1.0 / len(self.CLASSES) for cls in self.CLASSES}
        self._build_vocabulary()
    
    def _build_vocabulary(self):
        """Build the vocabulary from class keywords."""
        self.vocabulary = set()
        for keywords in self.CLASS_KEYWORDS.values():
            self.vocabulary.update(keywords.keys())
    
    def _preprocess(self, text: str) -> str:
        """Preprocess text: lowercase, remove sensitive patterns."""
        text = text.lower()
        
        # Remove sensitive demographic proxies
        for pattern in self.EXCLUDED_PATTERNS:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
        
        # Remove URLs
        text = re.sub(r'https?://\S+', '', text)
        
        # Remove mentions and hashtags (keep the word)
        text = re.sub(r'[@#](\w+)', r'\1', text)
        
        # Remove special characters but keep spaces
        text = re.sub(r'[^\w\s]', ' ', text)
        
        # Normalize whitespace
        text = ' '.join(text.split())
        
        return text
    
    def _extract_keywords(self, text: str) -> Dict[str, int]:
        """Extract keywords from preprocessed text."""
        keywords = defaultdict(int)
        words = text.split()
        
        # Single words
        for word in words:
            if word in self.vocabulary:
                keywords[word] += 1
        
        # Bigrams (for multi-word keywords)
        for i in range(len(words) - 1):
            bigram = f"{words[i]} {words[i+1]}"
            if bigram in self.vocabulary:
                keywords[bigram] += 1
        
        return dict(keywords)
    
    def _calculate_class_scores(self, keywords: Dict[str, int]) -> Dict[str, float]:
        """Calculate log-probability scores for each class."""
        scores = {}
        
        for cls in self.CLASSES:
            # Start with log prior
            score = np.log(self.class_priors[cls])
            
            # Add keyword contributions
            class_keywords = self.CLASS_KEYWORDS[cls]
            for keyword, count in keywords.items():
                if keyword in class_keywords:
                    # Log-likelihood contribution
                    score += count * np.log(1 + class_keywords[keyword])
            
            scores[cls] = score
        
        return scores
    
    def _scores_to_probabilities(self, scores: Dict[str, float]) -> Dict[str, float]:
        """Convert log-scores to probabilities using softmax."""
        max_score = max(scores.values())
        exp_scores = {cls: np.exp(score - max_score) for cls, score in scores.items()}
        total = sum(exp_scores.values())
        return {cls: exp_score / total for cls, exp_score in exp_scores.items()}
    
    def _get_keyword_contributions(
        self, 
        keywords: Dict[str, int], 
        predicted_class: str,
        top_n: int = 5
    ) -> List[Tuple[str, float]]:
        """Get top contributing keywords for the predicted class."""
        contributions = []
        class_keywords = self.CLASS_KEYWORDS[predicted_class]
        
        for keyword, count in keywords.items():
            if keyword in class_keywords:
                contribution = count * class_keywords[keyword]
                contributions.append((keyword, contribution))
        
        # Sort by contribution (descending)
        contributions.sort(key=lambda x: x[1], reverse=True)
        
        return contributions[:top_n]
    
    def classify(self, event: Dict[str, Any]) -> ClassificationResult:
        """
        Classify a single event.
        
        Args:
            event: Event dictionary with 'event_id' and 'content' fields
            
        Returns:
            ClassificationResult with prediction and explanations
        """
        event_id = event.get('event_id', 'unknown')
        content = event.get('content', '')
        
        # Preprocess and extract keywords
        processed_text = self._preprocess(content)
        keywords = self._extract_keywords(processed_text)
        
        # Calculate class scores and probabilities
        scores = self._calculate_class_scores(keywords)
        probabilities = self._scores_to_probabilities(scores)
        
        # Get predicted class and confidence
        predicted_class = max(probabilities, key=probabilities.get)
        confidence = probabilities[predicted_class]
        
        # Get contributing keywords
        top_keywords = self._get_keyword_contributions(keywords, predicted_class)
        
        return ClassificationResult(
            event_id=event_id,
            predicted_class=predicted_class,
            confidence=confidence,
            class_probabilities=probabilities,
            top_keywords=top_keywords,
            raw_text=content
        )
    
    def classify_batch(self, events: List[Dict[str, Any]]) -> BatchClassificationResult:
        """
        Classify a batch of events.
        
        Args:
            events: List of event dictionaries
            
        Returns:
            BatchClassificationResult with all results and summary statistics
        """
        results = [self.classify(event) for event in events]
        
        # Calculate class distribution
        class_distribution = defaultdict(int)
        for result in results:
            class_distribution[result.predicted_class] += 1
        
        # Calculate average confidence
        avg_confidence = np.mean([r.confidence for r in results]) if results else 0.0
        
        return BatchClassificationResult(
            results=results,
            class_distribution=dict(class_distribution),
            average_confidence=avg_confidence
        )
    
    def explain_classification(self, result: ClassificationResult) -> str:
        """
        Generate a human-readable explanation of a classification.
        
        Args:
            result: ClassificationResult to explain
            
        Returns:
            Formatted explanation string
        """
        lines = [
            f"Classification: {result.predicted_class}",
            f"Confidence: {result.confidence:.1%}",
            "",
            "Why this classification?",
        ]
        
        if result.top_keywords:
            lines.append("Top contributing keywords:")
            for keyword, contribution in result.top_keywords:
                lines.append(f"  • '{keyword}' (weight: {contribution:.2f})")
        else:
            lines.append("  No strong keyword matches found (default classification)")
        
        lines.append("")
        lines.append("Class probabilities:")
        for cls, prob in sorted(result.class_probabilities.items(), key=lambda x: -x[1]):
            bar = "█" * int(prob * 20)
            lines.append(f"  {cls:15} {prob:5.1%} {bar}")
        
        return "\n".join(lines)
    
    def get_probability_bars(self, result: ClassificationResult) -> List[Dict[str, Any]]:
        """
        Get probability data formatted for UI bar charts.
        
        Args:
            result: ClassificationResult
            
        Returns:
            List of dictionaries with class, probability, and color
        """
        colors = {
            'SERVICE': '#FF6B6B',
            'FRAUD': '#FF8C42',
            'MISINFORMATION': '#FFEB3B',
            'SENTIMENT': '#4ECDC4',
            'NOISE': '#95A5A6'
        }
        
        bars = []
        for cls in self.CLASSES:
            prob = result.class_probabilities.get(cls, 0)
            bars.append({
                'class': cls,
                'probability': prob,
                'percentage': f"{prob:.1%}",
                'color': colors.get(cls, '#666666'),
                'is_predicted': cls == result.predicted_class
            })
        
        # Sort by probability descending
        bars.sort(key=lambda x: x['probability'], reverse=True)
        
        return bars


# Singleton instance
_classifier = None

def get_classifier() -> NaiveBayesClassifier:
    """Get the singleton classifier instance."""
    global _classifier
    if _classifier is None:
        _classifier = NaiveBayesClassifier()
    return _classifier


# Convenience functions
def classify(event: Dict[str, Any]) -> ClassificationResult:
    """Classify a single event."""
    return get_classifier().classify(event)

def classify_batch(events: List[Dict[str, Any]]) -> BatchClassificationResult:
    """Classify a batch of events."""
    return get_classifier().classify_batch(events)

def explain_classification(result: ClassificationResult) -> str:
    """Explain a classification result."""
    return get_classifier().explain_classification(result)


if __name__ == "__main__":
    # Demo
    classifier = NaiveBayesClassifier()
    
    test_events = [
        {"event_id": "test-001", "content": "CRITICAL: 500 Internal Server Error - Gateway Timeout upstream"},
        {"event_id": "test-002", "content": "Got an SMS saying my card is cloned, this is a scam!"},
        {"event_id": "test-003", "content": "Hearing rumors that Mashreq ATMs are running empty across Dubai"},
        {"event_id": "test-004", "content": "I love the new mobile app, great experience!"},
        {"event_id": "test-005", "content": "What are the branch hours for Dubai Mall location?"},
    ]
    
    print("=== Naïve Bayes Classification Demo ===\n")
    
    for event in test_events:
        result = classifier.classify(event)
        print(f"Event: {event['content'][:60]}...")
        print(classifier.explain_classification(result))
        print("-" * 60)
