"""
Data Loader - Adapter for CSV Ingestion
=======================================
Reads synthetic CSV data and adapts it to the Pipeline Event Schema.

Responsible AI Mapping:
- Data Governance: Ensures metadata flags (synthetic=True) are applied.
- Traceability: Preserves original timestamps from source data.
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Any
import os
from datetime import datetime

class DataLoader:
    """Adapter for loading and standardizing CSV data."""

    REQUIRED_COLUMNS = ['event_id', 'content', 'source', 'timestamp']

    def load_csv_events(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Load events from a CSV file.
        
        Args:
            file_path: Path to the CSV file
            
        Returns:
            List of standardized event dictionaries
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"CSV file not found: {file_path}")
            
        try:
            df = pd.read_csv(file_path)
            
            # Validate columns
            missing = [col for col in self.REQUIRED_COLUMNS if col not in df.columns]
            if missing:
                # Try simple mapping if standard columns missing
                column_map = {
                    'text': 'content',
                    'post_id': 'event_id',
                    'platform': 'source',
                    'region': 'region'
                }
                df.rename(columns=column_map, inplace=True)
                
            # Fill missing IDs
            if 'event_id' not in df.columns:
                df['event_id'] = [f"csv-{i}" for i in range(len(df))]
                
            # Convert timestamps
            if 'timestamp' in df.columns:
                df['timestamp'] = pd.to_datetime(df['timestamp']).map(lambda x: x.isoformat())
            else:
                df['timestamp'] = datetime.now().isoformat()
            
            # Convert to list of dicts
            events = df.to_dict('records')
            
            # Enforce Schema & Metadata
            standardized_events = []
            for e in events:
                std_event = {
                    'event_id': str(e.get('event_id', f"unknown-{np.random.randint(99999)}")),
                    'content': str(e.get('content', '')),
                    'source': str(e.get('source', 'unknown')),
                    'timestamp': e.get('timestamp'),
                    'region': str(e.get('region', 'Global')),
                    'metadata': {
                        'synthetic': True,  # CRITICAL Governance Flag
                        'original_source_file': os.path.basename(file_path)
                    }
                }
                standardized_events.append(std_event)
                
            return standardized_events
            
        except Exception as e:
            print(f"Error loading CSV: {e}")
            return []

# Singleton
_loader = DataLoader()

def load_csv_events(file_path: str) -> List[Dict[str, Any]]:
    return _loader.load_csv_events(file_path)
