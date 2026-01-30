import re
import json

class GovernanceShield:
    """
    The Governance Shield acts as a middleware between the raw data/AI output
    and the human operator, ensuring safety, privacy, and professional standards.
    """
    
    def __init__(self):
        # Professional Banking Tone Dictionary
        self.panic_terms = {
            "bank is failing": "potential solvency indicators detected",
            "all money is gone": "significant liquidity outflow pattern",
            "collapse": "structural integrity risk",
            "panic": "heightened customer anxiety",
            "run on the bank": "abnormal withdrawal volume concentration"
        }

    def mask_pii(self, text: str) -> str:
        """
        Redacts PII from text before AI processing.
        Target: Emails, Account Numbers (8-12 digits).
        """
        # Mask Emails
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        masked_text = re.sub(email_pattern, '[EMAIL_REDACTED]', text)
        
        # Mask Account Numbers (assuming 8-16 digits for generic bank numbers)
        account_pattern = r'\b\d{8,16}\b'
        masked_text = re.sub(account_pattern, '[ACCOUNT_REDACTED]', masked_text)
        
        return masked_text

    def check_grounding(self, reasoning: str, source_data: list) -> dict:
        """
        Verifies if facts in reasoning are present in source data.
        Returns a 'Grounding Score' (0-100) and list of hallucinations.
        """
        # Convert source data to a single searchable string
        source_text = json.dumps(source_data).lower()
        reasoning_lower = reasoning.lower()
        
        # Simple heuristic: Check if quoted numbers or specific IDs in reasoning exist in source
        # Extract potential IDs (e.g. UUIDs or huge numbers) from reasoning
        potential_ids = re.findall(r'\b[a-f0-9-]{36}\b', reasoning_lower)
        
        hallucinations = []
        for pid in potential_ids:
            if pid not in source_text:
                hallucinations.append(f"Referenced ID {pid} not found in source.")
        
        score = 100 - (len(hallucinations) * 20)
        return {
            "passed": len(hallucinations) == 0,
            "score": max(0, score),
            "hallucinations": hallucinations
        }

    def ethical_filter(self, text: str) -> str:
        """
        Rewrites panic-inducing language into professional banking terminology.
        """
        text_lower = text.lower()
        rewritten_text = text
        
        for panic_term, professional_term in self.panic_terms.items():
            # Cas-insensitive replacement while trying to preserve case of original if possible (simple substitution here)
            # Using regex for case-insensitive match
            pattern = re.compile(re.escape(panic_term), re.IGNORECASE)
            rewritten_text = pattern.sub(f"[{professional_term}]", rewritten_text)
            
        return rewritten_text

# Example Usage Test
if __name__ == "__main__":
    shield = GovernanceShield()
    
    # Test PII
    raw_log = "User contact: john.doe@example.com, Account: 123456789012 complained about lag."
    print(f"PII Masked: {shield.mask_pii(raw_log)}")
    
    # Test Ethical Filter
    ai_output = "URGENT: The bank is failing and there is a panic in Dubai!"
    print(f"Ethical Filter: {shield.ethical_filter(ai_output)}")
    
    # Test Grounding
    res = shield.check_grounding("User 550e8400-e29b-41d4-a716-446655440000 reported error.", [{"id": "other-id"}])
    print(f"Grounding Check: {res}")
