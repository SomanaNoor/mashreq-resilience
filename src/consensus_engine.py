"""
Consensus Engine - Hybrid Multi-Headed Architecture
====================================================
Combines Naive Bayes keyword classification with Groq LLM semantic analysis
to detect sarcasm, irony, and complex sentiment patterns.

The engine compares:
1. Naive Bayes (keyword-based, fast, deterministic)
2. Groq Llama 3.3 (semantic understanding, context-aware)

Disagreements between the two are flagged as potential sarcasm or ambiguity.

Author: Antigravity
"""

import os
import json
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum
from dotenv import load_dotenv

load_dotenv()

from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser


class ConsensusStatus(Enum):
    """Result of consensus check between NB and semantic analysis."""
    AGREEMENT = "agreement"
    SARCASM_DETECTED = "sarcasm_detected"
    HIDDEN_CONCERN = "hidden_concern"
    AMBIGUOUS = "ambiguous"
    REVIEW_NEEDED = "review_needed"


@dataclass
class SemanticAnalysis:
    """Result from Groq semantic analysis."""
    semantic_sentiment: str  # CRISIS, POSITIVE, NEUTRAL, NEGATIVE
    semantic_category: str   # SERVICE, FRAUD, MISINFORMATION, SENTIMENT, NOISE
    is_sarcastic: bool
    hidden_meaning: str
    confidence: float


@dataclass
class ConsensusResult:
    """Complete result from consensus engine."""
    event_id: str
    original_text: str
    
    # Naive Bayes results
    nb_class: str
    nb_confidence: float
    
    # Semantic analysis results
    semantic_analysis: SemanticAnalysis
    
    # Consensus decision
    consensus_status: ConsensusStatus
    final_class: str
    final_confidence: float
    
    # Flags for UI
    is_ambiguous: bool = False
    potential_sarcasm: bool = False
    consensus_note: str = ""


# Prompt for semantic sarcasm detection
SEMANTIC_ANALYSIS_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are an expert at detecting sarcasm, irony, and hidden meaning in banking customer communications.

Analyze this text for its TRUE SEMANTIC MEANING. Ignore literal word choice. Focus on context and intent.

CRITICAL: Banking customers often use SARCASM when frustrated:
- "Great job losing my money!" = CRISIS (not positive)
- "Nice work crashing the system" = SERVICE issue (not praise)
- "Wonderful that I can't access my account" = PROBLEM (not satisfaction)

Categories:
- SERVICE: Technical issues, outages, errors
- FRAUD: Scams, suspicious activity, security
- MISINFORMATION: Rumors, panic, false claims
- SENTIMENT: Customer feedback (positive or negative)
- NOISE: Routine inquiries, general questions

Return ONLY valid JSON:
{{
    "semantic_sentiment": "CRISIS|POSITIVE|NEUTRAL|NEGATIVE",
    "semantic_category": "SERVICE|FRAUD|MISINFORMATION|SENTIMENT|NOISE",
    "is_sarcastic": true/false,
    "hidden_meaning": "explanation if sarcasm/irony detected, empty string otherwise",
    "confidence": 0.0 to 1.0
}}"""),
    ("human", "Text: \"{text}\"")
])


class ConsensusEngine:
    """
    Hybrid multi-headed classification engine.
    Compares Naive Bayes keyword classification with Groq semantic analysis.
    """
    
    # Map NB classes to expected sentiment
    CLASS_SENTIMENT_MAP = {
        'SERVICE': 'CRISIS',
        'FRAUD': 'CRISIS', 
        'MISINFORMATION': 'CRISIS',
        'SENTIMENT': 'NEUTRAL',  # Can be positive or negative
        'NOISE': 'NEUTRAL'
    }
    
    # Risk hierarchy for comparison
    RISK_HIERARCHY = {
        'FRAUD': 4,
        'MISINFORMATION': 3,
        'SERVICE': 2,
        'SENTIMENT': 1,
        'NOISE': 0
    }
    
    # Scenario-specific routing configuration
    SCENARIO_ROUTING = {
        'DIGITAL_DIRHAM_PANIC': {
            'keywords': ['digital dirham', 'cbdc', 'bridge', 'ledger', 'central bank digital'],
            'category': 'MISINFORMATION',
            'target_dept': 'Executive_Command_Center',
            'bypass_human': True,  # Emergency Executive Briefing bypass
            'escalation_level': 'CRITICAL'
        },
        'TRUSTED_DEVICE_LOOP': {
            'keywords': ['trusted device', 'neo app', 'locked out', 'chatbot', 'mashreq neo', 'device not recognized'],
            'category': 'SERVICE',
            'target_dept': 'IT_Operations',
            'requires_sarcasm_check': True,
            'escalation_level': 'HIGH'
        },
        'PHISHING_WAVE': {
            'keywords': ['mashreq legal', 'verification call', 'asked for otp', 'security department', 'fake call', 'scam call'],
            'category': 'FRAUD',
            'target_dept': 'Fraud_Response',
            'telemetry_required': True,  # Cross-check with healthy systems
            'escalation_level': 'CRITICAL'
        }
    }
    
    @staticmethod
    def detect_scenario(text: str, category: str) -> Optional[str]:
        """Detect which special scenario a signal belongs to based on keywords."""
        text_lower = text.lower()
        for scenario_name, config in ConsensusEngine.SCENARIO_ROUTING.items():
            if config['category'] == category:
                matching_keywords = [kw for kw in config['keywords'] if kw in text_lower]
                if len(matching_keywords) >= 2:  # Require at least 2 keyword matches
                    return scenario_name
        return None
    
    @staticmethod
    def get_routing_info(scenario: str) -> Dict[str, Any]:
        """Get routing information for a detected scenario."""
        if scenario and scenario in ConsensusEngine.SCENARIO_ROUTING:
            return ConsensusEngine.SCENARIO_ROUTING[scenario]
        return {}

    
    def __init__(self):
        """Initialize with Groq LLM."""
        self.llm = ChatGroq(
            model="llama-3.3-70b-versatile",
            temperature=0
        )
        self.parser = JsonOutputParser()
        self.chain = SEMANTIC_ANALYSIS_PROMPT | self.llm | self.parser
    
    def _analyze_semantic(self, text: str) -> SemanticAnalysis:
        """Run Groq semantic analysis on text."""
        try:
            result = self.chain.invoke({"text": text})
            return SemanticAnalysis(
                semantic_sentiment=result.get("semantic_sentiment", "NEUTRAL"),
                semantic_category=result.get("semantic_category", "NOISE"),
                is_sarcastic=result.get("is_sarcastic", False),
                hidden_meaning=result.get("hidden_meaning", ""),
                confidence=float(result.get("confidence", 0.5))
            )
        except Exception as e:
            # Fallback on error
            print(f"⚠️ Semantic analysis failed: {e}")
            return SemanticAnalysis(
                semantic_sentiment="NEUTRAL",
                semantic_category="NOISE",
                is_sarcastic=False,
                hidden_meaning="",
                confidence=0.0
            )
    
    def _determine_consensus(
        self,
        nb_class: str,
        nb_confidence: float,
        semantic: SemanticAnalysis
    ) -> Tuple[ConsensusStatus, str, float, str]:
        """
        Compare NB and semantic results to determine consensus.
        
        Returns:
            (status, final_class, final_confidence, note)
        """
        # Direct sarcasm detection from LLM
        if semantic.is_sarcastic:
            # LLM detected sarcasm - trust semantic analysis
            return (
                ConsensusStatus.SARCASM_DETECTED,
                semantic.semantic_category,
                max(nb_confidence, semantic.confidence),
                f"🎭 Sarcasm detected: {semantic.hidden_meaning}"
            )
        
        # Check for category disagreement
        nb_risk = self.RISK_HIERARCHY.get(nb_class, 0)
        semantic_risk = self.RISK_HIERARCHY.get(semantic.semantic_category, 0)
        
        # NB says low risk, semantic says high risk = Hidden concern
        if nb_risk <= 1 and semantic_risk >= 2:
            return (
                ConsensusStatus.HIDDEN_CONCERN,
                semantic.semantic_category,  # Trust semantic for hidden concerns
                semantic.confidence,
                f"⚠️ Hidden concern detected: NB saw '{nb_class}' but semantic analysis found '{semantic.semantic_category}'"
            )
        
        # NB says high risk, semantic says low risk = Review needed
        if nb_risk >= 2 and semantic_risk <= 1:
            return (
                ConsensusStatus.REVIEW_NEEDED,
                nb_class,  # Keep NB classification for caution
                min(nb_confidence, semantic.confidence),  # Lower confidence
                f"🔍 Review needed: NB flagged as '{nb_class}' but semantic analysis suggests lower risk"
            )
        
        # Check for same category but different sentiment
        if nb_class == semantic.semantic_category:
            # Full agreement
            return (
                ConsensusStatus.AGREEMENT,
                nb_class,
                (nb_confidence + semantic.confidence) / 2,
                "✅ NB and semantic analysis agree"
            )
        
        # Partial disagreement - ambiguous
        if abs(nb_risk - semantic_risk) <= 1:
            return (
                ConsensusStatus.AMBIGUOUS,
                nb_class if nb_confidence > semantic.confidence else semantic.semantic_category,
                min(nb_confidence, semantic.confidence),
                f"⚠️ Ambiguous: NB says '{nb_class}', semantic says '{semantic.semantic_category}'"
            )
        
        # Default to agreement with averaged confidence
        return (
            ConsensusStatus.AGREEMENT,
            nb_class,
            nb_confidence,
            ""
        )
    
    def validate(
        self,
        event_id: str,
        text: str,
        nb_class: str,
        nb_confidence: float
    ) -> ConsensusResult:
        """
        Validate a Naive Bayes classification with semantic analysis.
        
        Args:
            event_id: Unique event identifier
            text: Original text content
            nb_class: Naive Bayes predicted class
            nb_confidence: Naive Bayes confidence score
            
        Returns:
            ConsensusResult with final classification and flags
        """
        # Run semantic analysis
        semantic = self._analyze_semantic(text)
        
        # Determine consensus
        status, final_class, final_conf, note = self._determine_consensus(
            nb_class, nb_confidence, semantic
        )
        
        return ConsensusResult(
            event_id=event_id,
            original_text=text,
            nb_class=nb_class,
            nb_confidence=nb_confidence,
            semantic_analysis=semantic,
            consensus_status=status,
            final_class=final_class,
            final_confidence=final_conf,
            is_ambiguous=status in [ConsensusStatus.AMBIGUOUS, ConsensusStatus.REVIEW_NEEDED],
            potential_sarcasm=status == ConsensusStatus.SARCASM_DETECTED,
            consensus_note=note
        )
    
    def validate_batch(
        self,
        events: List[Dict[str, Any]],
        nb_results: List[Any]  # List of ClassificationResult
    ) -> List[ConsensusResult]:
        """
        Validate a batch of Naive Bayes classifications.
        
        Args:
            events: Original event dictionaries
            nb_results: Naive Bayes ClassificationResult objects
            
        Returns:
            List of ConsensusResult objects
        """
        results = []
        
        for event, nb_result in zip(events, nb_results):
            result = self.validate(
                event_id=event.get('event_id', 'unknown'),
                text=event.get('content', ''),
                nb_class=nb_result.predicted_class,
                nb_confidence=nb_result.confidence
            )
            results.append(result)
        
        return results


# Singleton instance
_consensus_engine = None

def get_consensus_engine() -> ConsensusEngine:
    """Get the singleton consensus engine instance."""
    global _consensus_engine
    if _consensus_engine is None:
        _consensus_engine = ConsensusEngine()
    return _consensus_engine


def test_consensus():
    """Test the consensus engine with sarcasm examples."""
    print("=" * 60)
    print("🧪 CONSENSUS ENGINE TEST")
    print("=" * 60)
    
    engine = ConsensusEngine()
    
    test_cases = [
        # (text, mock_nb_class, mock_nb_confidence)
        ("Great job losing my money!", "SENTIMENT", 0.75),
        ("Nice work crashing the system", "SENTIMENT", 0.70),
        ("Service is wonderful, can't access anything", "SENTIMENT", 0.65),
        ("Excellent service thank you", "SENTIMENT", 0.80),
        ("System is down critical failure", "SERVICE", 0.90),
        ("I heard the bank is running out of cash", "MISINFORMATION", 0.85),
        ("What are the branch hours?", "NOISE", 0.95),
    ]
    
    for text, nb_class, nb_conf in test_cases:
        print(f"\n📝 Text: \"{text}\"")
        print(f"   NB Classification: {nb_class} ({nb_conf:.0%})")
        
        result = engine.validate("test", text, nb_class, nb_conf)
        
        print(f"   Semantic: {result.semantic_analysis.semantic_category}")
        print(f"   Sarcastic: {result.semantic_analysis.is_sarcastic}")
        print(f"   Status: {result.consensus_status.value}")
        print(f"   Final: {result.final_class} ({result.final_confidence:.0%})")
        if result.consensus_note:
            print(f"   Note: {result.consensus_note}")
        print("-" * 60)


if __name__ == "__main__":
    test_consensus()
