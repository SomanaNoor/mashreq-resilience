"""
Guardrails Module - Stage 0: Governance Setup
==============================================
Defines allowed inputs, non-action boundaries, and system use policy.
Implements hard constraints in design, not just policy.

Responsible AI Mapping:
- Privacy & Security: Hard constraints on data types
- Accountability: Enforced boundaries
- Transparency: Published System Use Policy
"""

from dataclasses import dataclass
from typing import List, Dict, Any
from enum import Enum
import re


class DataSource(Enum):
    """Allowed data sources for the system."""
    SYNTHETIC_TWEET = "synthetic_tweet"
    SYNTHETIC_SUPPORT_TICKET = "synthetic_support_ticket"
    SYNTHETIC_APP_LOG = "synthetic_app_log"
    SYNTHETIC_NEWS = "synthetic_news"


class ActionBoundary(Enum):
    """Actions that are explicitly NOT allowed."""
    PUBLIC_RESPONSE = "no_public_responses"
    CUSTOMER_ACTION = "no_customer_actions"
    INDIVIDUAL_PROFILING = "no_individual_profiling"
    AUTOMATED_ESCALATION = "no_automated_escalation"
    PII_STORAGE = "no_pii_storage"


@dataclass
class InputValidationResult:
    """Result of input validation."""
    is_valid: bool
    violations: List[str]
    warnings: List[str]


class Guardrails:
    """
    Governance guardrails for the Responsible AI system.
    Enforces hard constraints on inputs and actions.
    """
    
    # Patterns that indicate live/real data (not allowed)
    LIVE_DATA_PATTERNS = [
        r'\b\d{16}\b',  # Credit card numbers
        r'\b\d{3}-\d{2}-\d{4}\b',  # SSN format
        r'\bIBAN\s*[A-Z]{2}\d{2}[A-Z0-9]{1,30}\b',  # IBAN
        r'\blive\s*feed\b',
        r'\breal\s*time\s*api\b',
        r'\bproduction\s*data\b',
    ]
    
    # Sensitive demographic proxies (excluded from classification)
    DEMOGRAPHIC_PROXIES = [
        'nationality', 'religion', 'ethnicity', 'gender', 'age_group',
        'marital_status', 'disability', 'political_affiliation'
    ]
    
    # Allowed source types
    ALLOWED_SOURCES = {
        'Tweet', 'Support Ticket', 'App Log', 'News Feed',
        'Synthetic Tweet', 'Synthetic Support', 'Synthetic Log'
    }
    
    def __init__(self):
        self.system_use_policy = self._build_policy()
        self.data_boundaries = self._build_boundaries()
    
    def _build_policy(self) -> Dict[str, Any]:
        """Build the System Use Policy document."""
        return {
            "title": "Mashreq Resilience AI - System Use Policy",
            "version": "1.0",
            "last_updated": "2026-01-31",
            "purpose": (
                "This AI system provides decision SUPPORT for operational risk monitoring. "
                "It analyzes synthetic social signals to detect potential service issues, "
                "fraud patterns, and misinformation. All outputs require human review."
            ),
            "allowed_uses": [
                "Identifying patterns in synthetic operational signals",
                "Prioritizing signals for human analyst review",
                "Providing risk and confidence scores with explanations",
                "Suggesting team routing for escalation (not individuals)",
                "Generating audit trails for governance review"
            ],
            "prohibited_uses": [
                "Automated responses to customers",
                "Individual customer profiling or scoring",
                "Decisions without human approval",
                "Processing of real customer data or live feeds",
                "Demographic-based classification or filtering"
            ],
            "human_oversight": (
                "Every escalation decision requires explicit human approval. "
                "The system provides recommendations only. No automated actions are taken."
            ),
            "data_handling": (
                "Only synthetic data is processed. PII is automatically redacted. "
                "No data is shared externally. Audit logs are retained for governance."
            ),
            "accountability": (
                "All decisions are logged with model outputs, human decisions, and timestamps. "
                "The audit trail is immutable and available for compliance review."
            )
        }
    
    def _build_boundaries(self) -> Dict[str, Any]:
        """Build the data boundaries specification."""
        return {
            "input_boundaries": {
                "allowed": [
                    "Synthetic social media posts",
                    "Synthetic support tickets",
                    "Synthetic application logs",
                    "Synthetic news feeds"
                ],
                "prohibited": [
                    "Real customer identifiers",
                    "Live API feeds",
                    "Production database exports",
                    "Unmasked PII"
                ]
            },
            "action_boundaries": {
                "allowed": [
                    "Classification with probability scores",
                    "Risk and confidence scoring",
                    "Queue routing suggestions",
                    "Rationale generation",
                    "Audit logging"
                ],
                "prohibited": [
                    "Public responses (social media, email)",
                    "Account modifications",
                    "Individual customer actions",
                    "Automated escalations without approval",
                    "Demographic-based decisions"
                ]
            },
            "output_boundaries": {
                "always_included": [
                    "Confidence percentage with uncertainty wording",
                    "Evidence used for classification",
                    "Assumptions and limitations",
                    "Human approval requirement notice"
                ],
                "never_included": [
                    "Individual customer names",
                    "Specific account numbers",
                    "Demographic information",
                    "Automated action confirmations"
                ]
            }
        }
    
    def validate_input(self, event: Dict[str, Any]) -> InputValidationResult:
        """
        Validate an input event against governance constraints.
        
        Args:
            event: The input event to validate
            
        Returns:
            InputValidationResult with validation status and any violations
        """
        violations = []
        warnings = []
        source = event.get('source', '')

        # 1. Enforce Synthetic Flag
        if not event.get('metadata', {}).get('synthetic', False):
             # Exception: If source explicitly says "Synthetic"
             if "Synthetic" not in source:
                 violations.append("Governance Violation: Non-synthetic data rejected.")
        
        # 2. PII Redaction (Transformation, not just rejection)
        content = str(event.get('content', ''))
        redacted_content = content
        
        # Redact Phone Numbers (UAE & Intl - flexible spacing)
        redacted_content = re.sub(r'(\+971|05\d)(\s?-?\d){7,11}', '[PHONE_REDACTED]', redacted_content)
        # Redact Emails
        redacted_content = re.sub(r'[\w\.-]+@[\w\.-]+\.\w+', '[EMAIL_REDACTED]', redacted_content)
        # Redact IBANs (AE followed by 21 digits/chars)
        redacted_content = re.sub(r'\b[A-Z]{2}\d{2}[A-Z0-9]{15,30}\b', '[IBAN_REDACTED]', redacted_content)
        # Redact Social Handles (@username)
        redacted_content = re.sub(r'@[\w_]{1,15}', '[HANDLE_REDACTED]', redacted_content)
        
        # Modify the event in place (Governance Transformation)
        if redacted_content != content:
            event['content'] = redacted_content
            warnings.append("PII detected and redacted automatically.")

        return InputValidationResult(
            is_valid=len(violations) == 0,
            violations=violations,
            warnings=warnings
        )
    
    def _is_anonymized_id(self, user_id: str) -> bool:
        """Check if a user ID appears to be properly anonymized."""
        # Anonymized IDs should be short hashes or UUIDs
        if len(user_id) <= 12 and re.match(r'^[a-f0-9]+$', user_id.lower()):
            return True
        if re.match(r'^[a-f0-9-]{36}$', user_id.lower()):
            return True
        if user_id.startswith(('SYS_', 'INFL_', 'NEWS_')):
            return True
        return False
    
    def get_policy_text(self) -> str:
        """Get formatted policy text for UI display."""
        policy = self.system_use_policy
        lines = [
            f"# {policy['title']}",
            f"Version {policy['version']} | Updated {policy['last_updated']}",
            "",
            "## Purpose",
            policy['purpose'],
            "",
            "## Allowed Uses",
            *[f"• {use}" for use in policy['allowed_uses']],
            "",
            "## Prohibited Uses",
            *[f"• {use}" for use in policy['prohibited_uses']],
            "",
            "## Human Oversight",
            policy['human_oversight'],
            "",
            "## Accountability",
            policy['accountability']
        ]
        return "\n".join(lines)
    
    def get_boundaries(self) -> Dict[str, Any]:
        """Get the data boundaries specification."""
        return self.data_boundaries
    
    def get_governance_footer(self) -> str:
        """Get the standard governance footer for UI cards."""
        return "No automated action. No personal data. Synthetic signals only."
    
    def get_decision_banner(self) -> str:
        """Get the decision support banner text."""
        return "Decision support only — no automated action."
    
    def check_action_allowed(self, action: str) -> bool:
        """Check if a proposed action is allowed by governance boundaries."""
        prohibited_keywords = [
            'auto_respond', 'send_email', 'send_sms', 'modify_account',
            'block_user', 'freeze_account', 'auto_escalate'
        ]
        return not any(kw in action.lower() for kw in prohibited_keywords)


# Singleton instance
_guardrails = None

def get_guardrails() -> Guardrails:
    """Get the singleton Guardrails instance."""
    global _guardrails
    if _guardrails is None:
        _guardrails = Guardrails()
    return _guardrails


# Convenience functions
def validate_input(event: Dict[str, Any]) -> InputValidationResult:
    """Validate an input event."""
    return get_guardrails().validate_input(event)

def get_policy_text() -> str:
    """Get the system use policy text."""
    return get_guardrails().get_policy_text()

def get_boundaries() -> Dict[str, Any]:
    """Get the data boundaries."""
    return get_guardrails().get_boundaries()

def get_governance_footer() -> str:
    """Get the governance footer."""
    return get_guardrails().get_governance_footer()

def get_decision_banner() -> str:
    """Get the decision banner."""
    return get_guardrails().get_decision_banner()


if __name__ == "__main__":
    # Demo
    guardrails = Guardrails()
    
    print("=== System Use Policy ===")
    print(guardrails.get_policy_text())
    print()
    
    # Test validation
    test_event = {
        "event_id": "test-001",
        "source": "Tweet",
        "content": "Testing the system with synthetic data",
        "user_id": "abc123de",
        "metadata": {"latency_ms": 50}
    }
    result = guardrails.validate_input(test_event)
    print(f"Validation: {'PASS' if result.is_valid else 'FAIL'}")
    print(f"Violations: {result.violations}")
    print(f"Warnings: {result.warnings}")
