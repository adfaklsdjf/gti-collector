#!/usr/bin/env python3
"""
Migration v003: Add comprehensive date tracking to all listings.

This migration adds four date fields to track the lifecycle of each listing:
- created_date: When the listing was first added
- last_modified_date: When listing data (excluding last_seen_date) was last changed  
- last_seen_date: When the listing was last encountered from data sources
- deleted_date: When the listing was deleted (null for active listings)

Historical dates are back-filled by parsing app.log for relevant events.
"""

import logging
import re
import os
from datetime import datetime
from typing import Dict, Any, Optional

migration_logger = logging.getLogger('schema_migrations')

# Regex patterns for parsing app.log
LOG_PATTERNS = {
    'new_listing': re.compile(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}),\d+ - INFO - Saved new listing with ID ([a-f0-9-]+) and VIN ([A-Z0-9]+)'),
    'existing_listing': re.compile(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}),\d+ - INFO - Listing with VIN ([A-Z0-9]+) already exists with ID ([a-f0-9-]+)'),
    'updated_listing': re.compile(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}),\d+ - INFO - Updated listing ([a-f0-9-]+):')
}

def parse_app_log(data_dir: str) -> Dict[str, Dict[str, Optional[str]]]:
    """
    Parse app.log to extract historical date information for listings.
    
    Args:
        data_dir: Path to data directory
        
    Returns:
        Dict mapping listing IDs to their date information
    """
    migration_logger.info("📋 Parsing app.log for historical date information...")
    
    # Try multiple possible log file locations
    log_paths = [
        os.path.join(data_dir, '..', 'app.log'),  # Project root
        os.path.join(data_dir, 'app.log'),        # Data directory
        'app.log'                                 # Current directory
    ]
    
    log_file = None
    for path in log_paths:
        if os.path.exists(path):
            log_file = path
            break
    
    if not log_file:
        migration_logger.warning("⚠️ app.log not found, cannot back-fill historical dates")
        return {}
    
    migration_logger.info(f"📖 Reading log file: {log_file}")
    
    # Load existing VIN to ID mappings to resolve VINs to listing IDs
    vin_to_id = {}
    try:
        vin_index_path = os.path.join(data_dir, 'indices', 'vin_to_id.json')
        if os.path.exists(vin_index_path):
            import json
            with open(vin_index_path, 'r') as f:
                index_data = json.load(f)
                if 'vin_mappings' in index_data:
                    vin_to_id = index_data['vin_mappings']
                else:
                    # Old format
                    vin_to_id = {k: v for k, v in index_data.items() if k != 'schema_version'}
    except Exception as e:
        migration_logger.warning(f"⚠️ Could not load VIN index: {e}")
    
    # Track dates for each listing ID
    listing_dates = {}
    
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                
                # Check for new listing creation
                match = LOG_PATTERNS['new_listing'].search(line)
                if match:
                    timestamp_str, listing_id, vin = match.groups()
                    timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S').isoformat()
                    
                    if listing_id not in listing_dates:
                        listing_dates[listing_id] = {
                            'created_date': None,
                            'last_modified_date': None,
                            'last_seen_date': None,
                            'deleted_date': None
                        }
                    
                    # Set creation date (earliest wins)
                    if not listing_dates[listing_id]['created_date']:
                        listing_dates[listing_id]['created_date'] = timestamp
                    
                    # Update last seen date (latest wins)
                    listing_dates[listing_id]['last_seen_date'] = timestamp
                    continue
                
                # Check for existing listing (last seen update)
                match = LOG_PATTERNS['existing_listing'].search(line)
                if match:
                    timestamp_str, vin, listing_id = match.groups()
                    timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S').isoformat()
                    
                    if listing_id not in listing_dates:
                        listing_dates[listing_id] = {
                            'created_date': None,
                            'last_modified_date': None,
                            'last_seen_date': None,
                            'deleted_date': None
                        }
                    
                    # Update last seen date (latest wins)
                    listing_dates[listing_id]['last_seen_date'] = timestamp
                    continue
                
                # Check for listing updates (modified date)
                match = LOG_PATTERNS['updated_listing'].search(line)
                if match:
                    timestamp_str, listing_id = match.groups()
                    timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S').isoformat()
                    
                    if listing_id not in listing_dates:
                        listing_dates[listing_id] = {
                            'created_date': None,
                            'last_modified_date': None,
                            'last_seen_date': None,
                            'deleted_date': None
                        }
                    
                    # Update last modified date (latest wins)
                    listing_dates[listing_id]['last_modified_date'] = timestamp
                    # Also update last seen date
                    listing_dates[listing_id]['last_seen_date'] = timestamp
                    continue
    
    except Exception as e:
        migration_logger.error(f"❌ Error parsing app.log: {e}")
        return {}
    
    migration_logger.info(f"📊 Extracted date information for {len(listing_dates)} listings")
    return listing_dates

def migrate(file_data: Dict[str, Any], migration_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Add date tracking fields to listing data.
    
    Args:
        file_data: Current file data structure
        migration_context: Context including data_dir for log parsing
        
    Returns:
        Dict[str, Any]: Updated file data with date tracking fields
    """
    migration_logger.debug("🔧 Adding date tracking fields")
    
    # Skip if this doesn't look like a listing file
    if 'data' not in file_data or 'id' not in file_data:
        migration_logger.debug("⏭️ Skipping non-listing file")
        return file_data
    
    listing_id = file_data['id']
    
    # Get historical dates from log parsing (cached in migration context)
    historical_dates = {}
    if migration_context and 'historical_dates' in migration_context:
        historical_dates = migration_context['historical_dates']
    elif migration_context and 'data_dir' in migration_context:
        # Parse log file if not already cached
        historical_dates = parse_app_log(migration_context['data_dir'])
        # Cache for future files in this migration run
        migration_context['historical_dates'] = historical_dates
    
    # Get dates for this specific listing
    listing_dates = historical_dates.get(listing_id, {})
    
    # For listings without historical data, use a reasonable fallback date
    # We'll use the earliest reasonable date for this project (when development started)
    fallback_date = "2025-07-13T12:00:00"  # Reasonable project start date
    
    # Add date fields to the listing data (only if they don't already exist)
    if 'created_date' not in file_data:
        file_data['created_date'] = listing_dates.get('created_date') or fallback_date
    if 'last_modified_date' not in file_data:
        file_data['last_modified_date'] = listing_dates.get('last_modified_date') or fallback_date
    if 'last_seen_date' not in file_data:
        file_data['last_seen_date'] = listing_dates.get('last_seen_date') or fallback_date
    if 'deleted_date' not in file_data:
        file_data['deleted_date'] = listing_dates.get('deleted_date')  # None for active listings
    
    migration_logger.debug(f"✅ Added date tracking for listing {listing_id}")
    return file_data