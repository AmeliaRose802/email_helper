"""Data persistence utilities"""

import os
import pandas as pd
from .date_utils import format_datetime_for_storage


def save_to_csv(data, file_path):
    """Consolidate CSV saving logic"""
    new_df = pd.DataFrame(data)
    if os.path.exists(file_path):
        existing_df = pd.read_csv(file_path)
        combined_df = pd.concat([existing_df, new_df], ignore_index=True)
    else:
        combined_df = new_df
    combined_df.to_csv(file_path, index=False)


def normalize_data_for_storage(data):
    """Convert objects to strings for CSV storage"""
    processed_entries = []
    for entry in data:
        processed_entry = entry.copy()
        # Convert datetime objects to strings
        for key, value in processed_entry.items():
            if hasattr(value, 'strftime'):
                processed_entry[key] = format_datetime_for_storage(value)
            elif value is not None and not isinstance(value, (str, int, float, bool)):
                processed_entry[key] = str(value)
        processed_entries.append(processed_entry)
    return processed_entries


def load_csv_or_empty(file_path, dtype=str):
    """Load CSV file or return empty DataFrame"""
    if os.path.exists(file_path):
        return pd.read_csv(file_path, dtype=dtype)
    return pd.DataFrame()
