#!/usr/bin/env python3
"""
Migration v002: Add schema versioning to all files.

This migration adds schema_version field to all data files and index files.
This is the bootstrap migration that introduces the versioning system itself.
"""

import logging
from typing import Dict, Any

migration_logger = logging.getLogger('schema_migrations')

def migrate(file_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Add schema version 2 to file data.
    
    Args:
        file_data: Current file data structure
        
    Returns:
        Dict[str, Any]: Updated file data with schema_version field
    """
    migration_logger.debug("🔧 Adding schema_version field")
    
    # Check if this looks like an old-style index file (has VIN-like keys but no structure)
    has_vin_keys = any(key for key in file_data.keys() if len(key) == 17 and key.isalnum())
    is_unstructured_index = has_vin_keys and 'vin_mappings' not in file_data and 'schema_version' not in file_data
    
    if is_unstructured_index:
        # This looks like an old-style index file - wrap the VIN mappings
        migration_logger.debug("🔧 Wrapping VIN mappings in index file")
        vin_mappings = {k: v for k, v in file_data.items() if k != 'schema_version'}
        file_data = {
            'schema_version': 2,
            'vin_mappings': vin_mappings
        }
    else:
        # Regular data file - just add schema version at top level
        file_data['schema_version'] = 2
    
    migration_logger.debug("✅ Schema versioning added successfully")
    return file_data