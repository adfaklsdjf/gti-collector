#!/usr/bin/env python3
"""
Migration v001: Convert single 'url' field to multi-site 'urls' structure.

HISTORICAL MIGRATION - This migration was already applied to all data before
the schema versioning system was introduced. This code is preserved for posterity
but should never be executed as all data is already at v2 or higher.

Original migration:
- Converts single URL field to multi-site URLs object
- Adds last_updated_site and sites_seen tracking
- Detects site from URL pattern (CarGurus, AutoTrader, Cars.com)
"""

import logging
from typing import Dict, Any

migration_logger = logging.getLogger('schema_migrations')

def migrate(file_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert single 'url' field to multi-site 'urls' structure.
    
    NOTE: This is a historical migration preserved for posterity.
    All data should already be at v2 or higher, so this should never execute.
    
    Args:
        file_data: Current file data structure
        
    Returns:
        Dict[str, Any]: Updated file data with multi-site URL structure
    """
    migration_logger.warning("⚠️ Historical v001 migration executed - this should not happen!")
    
    # This is the original logic from the old migration system
    if 'data' not in file_data:
        return file_data
    
    data = file_data['data']
    
    # Check if already migrated (has 'urls' field)
    if 'urls' in data:
        migration_logger.debug("⏭️ Skipping already migrated listing")
        return file_data
    
    # Check if has old 'url' field
    if 'url' not in data:
        migration_logger.warning(f"⚠️ Listing has no URL field, skipping")
        return file_data
    
    old_url = data['url']
    
    # Detect site from URL
    site = 'unknown'
    if 'cargurus.com' in old_url.lower():
        site = 'cargurus'
    elif 'autotrader.com' in old_url.lower():
        site = 'autotrader'
    elif 'cars.com' in old_url.lower():
        site = 'cars'
    
    # Migrate to new structure
    data['urls'] = {site: old_url}
    data['last_updated_site'] = site
    data['sites_seen'] = [site]
    
    # Remove old url field
    del data['url']
    
    migration_logger.debug(f"✅ Migrated URL structure: {site} -> {old_url}")
    return file_data