
import os
import sys
import pandas as pd
import numpy as np
import json
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.getcwd(), 'src'))

from responsible_ai_pipeline import get_pipeline

def debug_pipeline():
    print("=== PIPELINE DEBUG START ===")
    
    # 1. Load Data
    csv_path = "data/synthetic_data.csv"
    if not os.path.exists(csv_path):
        print(f"❌ ERROR: {csv_path} not found!")
        return
        
    print(f"✅ Loading {csv_path}...")
    df = pd.read_csv(csv_path)
    events = df.to_dict('records')
    print(f"Loaded {len(events)} raw events.")
    
    # 2. Fix Timestamps (Copying logic from dashboard.py)
    now = datetime.now()
    for i, e in enumerate(events):
        if 'event_id' not in e:
            e['event_id'] = f"csv-{np.random.randint(1000,9999)}"
        
        # Distribution: spread events over the last 60 minutes
        offset_minutes = (i % 60) 
        # Make them RECENT so they fall in the 30m window?
        # WAIT: The clustering engine has a 30m window. 
        # If we spread over 60m, half might be lost.
        # Let's squash them into the last 20m for this test.
        offset_minutes = (i % 20) 
        event_time = now - pd.Timedelta(minutes=(20 - offset_minutes))
        e['timestamp'] = event_time.isoformat()
        
    print("✅ Timestamps updated to recent time (last 20m).")
    
    # 3. Run Pipeline
    print("Running pipeline.process()...")
    pipeline = get_pipeline()
    result = pipeline.process(events)
    
    # 4. Inspect Results
    print("\n--- RESULTS ---")
    print(f"Processing Time: {result.processing_time_ms}ms")
    
    # Stage 1: Classification
    print(f"\nStage 1: Classification")
    print(f"Total Classified: {len(result.classification_result.results)}")
    dist = result.classification_result.class_distribution
    print(f"Distribution: {dist}")
    
    # Stage 2: Gating
    print(f"\nStage 2: Gating")
    print(f"Surfaced Signals: {result.gating_result.signal_count}")
    print(f"Noise Archived: {result.gating_result.noise_count}")
    print(f"Noise Summary:\n{result.gating_result.gating_summary.get('archive_reasons')}")
    
    if result.gating_result.signal_count == 0:
        print("❌ CRITICAL: No signals surfaced! Check Signal Gate thresholds.")
        # Inspect a few noise items
        print("First 3 Noise Items:")
        for n in result.gating_result.noise[:3]:
            print(f"  - {n.predicted_class} (Conf: {n.confidence:.2f}): {n.archive_reason}")
    else:
        print("✅ Signals passed gating.")

    # Stage 3: Clustering
    print(f"\nStage 3: Clustering")
    print(f"Clusters Formed: {result.clustering_result.cluster_count}")
    
    if result.clustering_result.cluster_count == 0:
        print("❌ CRITICAL: No clusters formed! Check Clustering Engine params.")
        if result.gating_result.signal_count > 0:
             print("Potential Issues: Time window or Similarity mismatch.")
             # Check timestamp parsing in engine
             # (Hard to check directly without modifying engine, but we ensured ISO format above)
    else:
        print("✅ Clusters formed.")
        for analysis in result.cluster_analyses:
            print(f"\n  Cluster: {analysis.cluster.cluster_id}")
            print(f"  Title: {analysis.to_analyst_card()['title']}")
            print(f"  Risk: {analysis.risk_score.total_score}")
            print(f"  Confidence: {analysis.confidence.percentage}%")
            print(f"  Escalation: {analysis.escalation.suggested_queue}")

    print("\n=== DEBUG END ===")

if __name__ == "__main__":
    debug_pipeline()
