
import os
import sys
import json
import requests
import time

# Add src to path
sys.path.insert(0, os.path.join(os.getcwd(), 'src'))

from responsible_ai_pipeline import get_pipeline
from data_loader import load_csv_events
from guardrails import validate_input

def test_backend():
    print("=== BACKEND VERIFICATION ===")
    
    # 1. Test CSV Loading
    print("\n[1] Testing CSV Loading...")
    csv_path = "data/synthetic_social_signals_mashreq.csv"
    events = load_csv_events(csv_path)
    print(f"Loaded {len(events)} events from CSV.")
    if len(events) != 162:
         print("❌ ERROR: Expected 162 events.")
    else:
         print("✅ Count is correct.")
    
    # 2. Test Governance (PII Redaction)
    print("\n[2] Testing PII Redaction...")
    test_event = {
        "event_id": "test-pii",
        "content": "Call me at +971 50 123 4567 regarding account AE12345678901234567890",
        "source": "Synthetic Support",
        "metadata": {"synthetic": True},
        "timestamp": "2025-01-01T10:00:00"
    }
    res = validate_input(test_event)
    print(f"Original: Call me at +971 50 123 4567...")
    print(f"Redacted: {test_event['content']}")
    if "[PHONE_REDACTED]" in test_event['content'] and "[IBAN_REDACTED]" in test_event['content']:
        print("✅ Redaction successful.")
    else:
        print("❌ Redaction failed.")

    # 3. Test Full Pipeline Execution (No API)
    print("\n[3] Testing Pipeline Execution...")
    pipeline = get_pipeline()
    result = pipeline.process(events)
    
    print(f"Processed in {result.processing_time_ms}ms")
    print(f"Signals Surfaced: {result.gating_result.signal_count}")
    print(f"Clusters Formed: {result.clustering_result.cluster_count}")
    
    if result.clustering_result.cluster_count > 0:
        print("✅ Pipeline successfully clustered CSV data.")
        # Check timestamps
        c1 = result.cluster_analyses[0].cluster
        print(f"Cluster 1 Window: {c1.time_window_start} to {c1.time_window_end}")
        if "2025" in str(c1.time_window_start):
            print("✅ Timestamp-aware clustering confirmed (using 2025 data).")
        else:
            print("❌ Error: Clustering used current system time!")
    else:
        print("❌ Error: No clusters formed.")

    # 4. Test RBAC (Mocking API Logic)
    print("\n[4] Testing RBAC Logic...")
    from authz import validate_decision_authority
    
    # Analyst trying to Approve
    can_approve = validate_decision_authority("analyst", "APPROVED")
    print(f"Analyst trying to APPROVE: {'Allowed' if can_approve else 'Blocked'}")
    if not can_approve:
        print("✅ correctly blocked.")
    else:
        print("❌ Security Failure - Analyst should not approve.")

    # Reviewer trying to Approve
    can_approve_r = validate_decision_authority("reviewer", "APPROVED")
    print(f"Reviewer trying to APPROVE: {'Allowed' if can_approve_r else 'Blocked'}")
    if can_approve_r:
        print("✅ correctly allowed.")
    else:
        print("❌ Security Failure - Reviewer should be able to approve.")

    print("\n=== VERIFICATION COMPLETE ===")

if __name__ == "__main__":
    test_backend()
