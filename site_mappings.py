#!/usr/bin/env python3
"""
Site-specific field mapping and processing for multi-site support.
Handles conversion from site-specific data to internal unified format.
"""

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# Define which internal fields are required for desirability calculations
DESIRABILITY_REQUIRED_FIELDS = ['price', 'year', 'mileage', 'distance']

# Define site capabilities - which internal fields each site can provide
SITE_CAPABILITIES = {
    'cargurus': [
        'site', 'url', 'title', 'price', 'year', 'mileage', 'vin', 'location', 'distance',
        'drivetrain', 'exterior_color', 'interior_color', 'mpg', 'engine', 'fuel_type',
        'transmission', 'trim_level', 'car_title', 'accidents', 'previous_owners', 'phone_number'
    ],
    'autotrader': [
        'site', 'url', 'title'
        # TODO: Add more capabilities as AutoTrader extraction is implemented
    ],
    'cars': [
        'site', 'url', 'title'
        # TODO: Add more capabilities as Cars.com extraction is implemented
    ]
}

# Define site-specific field mappings (site_field -> internal_field)
SITE_FIELD_MAPPINGS = {
    'cargurus': {
        # Direct mappings - most fields map directly
        'site': 'site',
        'url': 'url',
        'title': 'title',
        'price': 'price',
        'year': 'year',
        'mileage': 'mileage',
        'vin': 'vin',
        'location': 'location',
        'distance': 'distance',
        'drivetrain': 'drivetrain',
        'exterior_color': 'exterior_color',
        'interior_color': 'interior_color',
        'mpg': 'mpg',
        'engine': 'engine',
        'fuel_type': 'fuel_type',
        'transmission': 'transmission',
        'trim_level': 'trim_level',
        'car_title': 'car_title',
        'accidents': 'accidents',
        'previous_owners': 'previous_owners',
        'phone_number': 'phone_number'
    },
    'autotrader': {
        # TODO: Define AutoTrader mappings
        'site': 'site',
        'url': 'url',
        'title': 'title'
    },
    'cars': {
        # TODO: Define Cars.com mappings
        'site': 'site',
        'url': 'url',
        'title': 'title'
    }
}


def process_site_data(raw_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process raw site data into internal format.
    
    Args:
        raw_data: Raw data from site extractor
        
    Returns:
        dict: Processed data in internal format with site URLs properly handled
    """
    site_key = raw_data.get('site')
    if not site_key:
        logger.error("No site specified in raw data")
        return {}
    
    logger.info(f"📥 Processing data from site: {site_key}")
    
    # Get site mapping
    mapping = SITE_FIELD_MAPPINGS.get(site_key, {})
    capabilities = SITE_CAPABILITIES.get(site_key, [])
    
    processed_data = {}
    
    # Process each field from raw data
    for site_field, value in raw_data.items():
        if value is None or value == '':
            continue  # Skip empty values
        
        internal_field = None
        
        # Check for explicit mapping first
        if site_field in mapping:
            internal_field = mapping[site_field]
            logger.debug(f"📋 Explicit mapping: {site_field} -> {internal_field}")
        # Check for direct name match
        elif site_field in capabilities:
            internal_field = site_field
            logger.debug(f"🎯 Direct match: {site_field}")
        # Log and drop unknown fields
        else:
            logger.info(f"⚠️ Unknown field dropped: {site_field} = '{value}'")
            continue
        
        processed_data[internal_field] = value
        logger.debug(f"✅ Mapped: {site_field} = '{value}' -> {internal_field}")
    
    # Handle URL specially - convert to site-specific URLs structure
    if 'url' in processed_data and site_key:
        site_url = processed_data.pop('url')
        processed_data['urls'] = {site_key: site_url}
        processed_data['last_updated_site'] = site_key
        logger.info(f"🔗 Site URL stored: {site_key} -> {site_url}")
    
    logger.info(f"✅ Site data processing complete for {site_key}")
    return processed_data


def merge_site_data(existing_data: Dict[str, Any], new_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge new site data with existing listing data.
    
    Args:
        existing_data: Current listing data
        new_data: New data from site (already processed by process_site_data)
        
    Returns:
        dict: Merged data with URLs properly combined
    """
    site_key = new_data.get('last_updated_site')
    if not site_key:
        logger.error("No site specified in new data")
        return existing_data
    
    logger.info(f"🔄 Merging data from site: {site_key}")
    
    # Start with existing data
    merged_data = existing_data.copy()
    
    # Merge URLs specially
    if 'urls' in new_data:
        if 'urls' not in merged_data:
            merged_data['urls'] = {}
        merged_data['urls'].update(new_data['urls'])
        logger.info(f"🔗 Updated URLs: {merged_data['urls']}")
    
    # Track sites seen
    if 'sites_seen' not in merged_data:
        merged_data['sites_seen'] = []
    if site_key not in merged_data['sites_seen']:
        merged_data['sites_seen'].append(site_key)
        logger.info(f"🌐 Added site to seen list: {site_key}")
    
    # Merge other fields (last-updated-wins approach)
    fields_updated = []
    for field, value in new_data.items():
        if field in ['urls', 'sites_seen']:
            continue  # Already handled
        
        if field not in merged_data or merged_data[field] != value:
            old_value = merged_data.get(field, 'None')
            merged_data[field] = value
            fields_updated.append(f"{field}: '{old_value}' -> '{value}'")
    
    if fields_updated:
        logger.info(f"🔄 Fields updated from {site_key}: {', '.join(fields_updated)}")
    else:
        logger.info(f"ℹ️ No field changes from {site_key}")
    
    return merged_data


def check_desirability_completeness(data: Dict[str, Any]) -> tuple[bool, list[str]]:
    """
    Check if listing has all required fields for desirability calculation.
    
    Args:
        data: Listing data
        
    Returns:
        tuple: (is_complete, missing_fields)
    """
    missing_fields = []
    
    for field in DESIRABILITY_REQUIRED_FIELDS:
        if field not in data or not data[field]:
            missing_fields.append(field)
    
    is_complete = len(missing_fields) == 0
    
    if not is_complete:
        logger.warning(f"⚠️ Missing desirability fields: {missing_fields}")
    
    return is_complete, missing_fields


def get_site_capabilities(site_key: str) -> list[str]:
    """Get list of internal fields supported by a site."""
    return SITE_CAPABILITIES.get(site_key, [])


def site_supports_field(site_key: str, internal_field: str) -> bool:
    """Check if a site supports a specific internal field."""
    capabilities = SITE_CAPABILITIES.get(site_key, [])
    return internal_field in capabilities