"""
Migration v004: Add performance_package boolean field

Adds a performance_package field to track whether a GTI has a performance package.
This is a user-editable boolean field (Yes/No).
"""

def migrate_listing(listing_data):
    """
    Add performance_package field to listing data.
    
    Args:
        listing_data (dict): The listing data to migrate
        
    Returns:
        dict: The migrated listing data
    """
    # Initialize performance_package as None (unknown/not set)
    if 'performance_package' not in listing_data['data']:
        listing_data['data']['performance_package'] = None
    
    return listing_data

def migrate(data):
    """
    Main migration function for compatibility with migration system.
    Handles both listing data and index data.
    
    Args:
        data (dict): The data to migrate (listing or index)
        
    Returns:
        dict: The migrated data
    """
    # Check if this is listing data (has 'data' key) or index data (has 'vin_mappings' key)
    if 'data' in data:
        # This is listing data - use the listing migration
        return migrate_listing(data)
    else:
        # This is index data or other data - no changes needed for v004
        return data

def get_migration_info():
    """Return information about this migration"""
    return {
        'version': 4,
        'description': 'Add performance_package boolean field',
        'adds_fields': ['performance_package'],
        'removes_fields': [],
        'modifies_fields': []
    }