#!/usr/bin/env python3
"""
Utility functions for listing operations.
Handles data comparison, validation, and transformations.
"""

import logging

logger = logging.getLogger(__name__)


def compare_listing_data(existing_data, new_data):
    """
    Compare two listing data objects and identify changes.
    
    Args:
        existing_data (dict): Current listing data
        new_data (dict): New listing data to compare
    
    Returns:
        dict: {
            'has_changes': bool,
            'changes': dict,  # field -> {'old': value, 'new': value}
            'updated_data': dict  # merged data with new values
        }
    """
    changes = {}
    updated_data = existing_data.copy()
    
    # Fields to compare (excluding metadata)
    comparable_fields = ['url', 'price', 'year', 'mileage', 'distance', 'vin', 'title', 'location']
    
    for field in comparable_fields:
        existing_value = existing_data.get(field)
        new_value = new_data.get(field)
        
        # Only update if new value exists and is different
        if new_value is not None and existing_value != new_value:
            changes[field] = {
                'old': existing_value,
                'new': new_value
            }
            updated_data[field] = new_value
            logger.debug(f"Field '{field}' changed: '{existing_value}' -> '{new_value}'")
    
    has_changes = len(changes) > 0
    
    return {
        'has_changes': has_changes,
        'changes': changes,
        'updated_data': updated_data
    }


def merge_listing_data(existing_data, new_data):
    """
    Merge new listing data into existing data, preserving existing values
    when new values are None or missing.
    
    Args:
        existing_data (dict): Current listing data  
        new_data (dict): New listing data
    
    Returns:
        dict: Merged listing data
    """
    merged = existing_data.copy()
    
    for key, value in new_data.items():
        if value is not None and value != "":
            merged[key] = value
    
    return merged


def format_change_summary(changes):
    """
    Format changes into a human-readable summary.
    
    Args:
        changes (dict): Changes dict from compare_listing_data
    
    Returns:
        str: Human-readable summary of changes
    """
    if not changes:
        return "No changes detected"
    
    change_descriptions = []
    for field, change in changes.items():
        old_val = change['old'] or 'None'
        new_val = change['new']
        change_descriptions.append(f"{field}: {old_val} → {new_val}")
    
    return f"Updated {len(changes)} field(s): {', '.join(change_descriptions)}"