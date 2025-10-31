"""Data persistence utilities for backend.

Migrated from src/utils/data_utils.py for consolidation.
"""

import os
import pandas as pd
from typing import Any, Dict, List


def save_to_csv(data: List[Dict[str, Any]], file_path: str) -> None:
    """Consolidate CSV saving logic.
    
    Args:
        data: List of dictionaries to save
        file_path: Path to CSV file
    """
    new_df = pd.DataFrame(data)
    if os.path.exists(file_path):
        existing_df = pd.read_csv(file_path)
        combined_df = pd.concat([existing_df, new_df], ignore_index=True)
    else:
        combined_df = new_df
    combined_df.to_csv(file_path, index=False)


def normalize_data_for_storage(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Convert objects to strings for CSV storage.
    
    Args:
        data: List of dictionaries with data to normalize
        
    Returns:
        List of normalized dictionaries
    """
    processed_entries = []
    for entry in data:
        processed_entry = entry.copy()
        # Convert datetime objects to strings
        for key, value in processed_entry.items():
            if hasattr(value, 'strftime'):
                processed_entry[key] = value.isoformat()
            elif value is not None and not isinstance(value, (str, int, float, bool)):
                processed_entry[key] = str(value)
        processed_entries.append(processed_entry)
    return processed_entries


def load_csv_or_empty(file_path: str, dtype: Any = str) -> pd.DataFrame:
    """Load CSV file or return empty DataFrame.
    
    Args:
        file_path: Path to CSV file
        dtype: Data type for columns
        
    Returns:
        DataFrame with CSV data or empty DataFrame
    """
    if os.path.exists(file_path):
        return pd.read_csv(file_path, dtype=dtype)
    return pd.DataFrame()
