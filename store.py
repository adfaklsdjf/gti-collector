#!/usr/bin/env python3
"""
Storage module for GTI listings.
Handles persistence and deduplication based on VIN.
"""

import json
import os
import uuid
import shutil
from pathlib import Path
import logging
from datetime import datetime
from listing_utils import compare_listing_data, format_change_summary
from site_mappings import merge_site_data
from schema_migrations import SchemaMigrator

logger = logging.getLogger(__name__)

class Store:
    """Simple file-based storage with VIN deduplication."""
    
    def __init__(self, data_dir='data'):
        """Initialize store with data directory."""
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Create indices directory for tracking VINs
        self.indices_dir = self.data_dir / 'indices'
        self.indices_dir.mkdir(parents=True, exist_ok=True)
        
        self.vin_index_file = self.indices_dir / 'vin_to_id.json'
        self.migrator = SchemaMigrator(str(self.data_dir))
        self.vin_index = self._load_vin_index()
    
    def _load_vin_index(self):
        """Load VIN to file ID mapping."""
        if self.vin_index_file.exists():
            try:
                # Check if JIT migration is needed
                if not self.migrator.migrate_file_jit(self.vin_index_file):
                    logger.error("JIT migration failed for VIN index")
                
                with open(self.vin_index_file, 'r') as f:
                    index_data = json.load(f)
                
                # Handle schema-versioned structure
                if 'vin_mappings' in index_data:
                    return index_data['vin_mappings']
                else:
                    # Fallback for old structure
                    return {k: v for k, v in index_data.items() if k != 'schema_version'}
            except Exception as e:
                logger.error(f"Error loading VIN index: {e}")
                return {}
        return {}
    
    def _save_vin_index(self):
        """Save VIN to file ID mapping."""
        try:
            # Ensure directories exist before saving
            self.indices_dir.mkdir(parents=True, exist_ok=True)
            
            # Save in schema-versioned format
            current_version = self.migrator.get_current_schema_version()
            index_data = {
                'schema_version': current_version,
                'vin_mappings': self.vin_index
            }
            
            with open(self.vin_index_file, 'w') as f:
                json.dump(index_data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving VIN index: {e}")
    
    def add_listing(self, listing_data):
        """
        Add or update a listing in storage (upsert operation).
        
        Returns dict with:
        - 'success': True for new listing, False for no changes
        - 'updated': True if existing listing was updated
        - 'id': listing ID
        - 'changes': dict of changes made (if any)
        - 'change_summary': human-readable summary
        """
        vin = listing_data.get('vin')
        
        if not vin:
            raise ValueError("VIN is required for storage")
        
        # Check if VIN already exists
        if vin in self.vin_index:
            existing_id = self.vin_index[vin]
            logger.info(f"Listing with VIN {vin} already exists with ID {existing_id}")
            return self._update_existing_listing(existing_id, listing_data)
        else:
            return self._create_new_listing(listing_data)
    
    def _create_new_listing(self, listing_data):
        """Create a new listing."""
        listing_id = str(uuid.uuid4())
        vin = listing_data['vin']
        current_time = datetime.now().isoformat()
        
        # Add metadata, initialize comments field, and set date tracking
        listing_with_metadata = {
            'id': listing_id,
            'data': listing_data,
            'comments': '',  # Initialize with empty comments
            'created_date': current_time,
            'last_modified_date': current_time,
            'last_seen_date': current_time,
            'deleted_date': None  # None for active listings
        }
        
        # Save listing to file
        listing_file = self.data_dir / f"{listing_id}.json"
        try:
            # Ensure data directory exists before saving
            self.data_dir.mkdir(parents=True, exist_ok=True)
            with open(listing_file, 'w', encoding='utf-8') as f:
                json.dump(listing_with_metadata, f, indent=2, ensure_ascii=False)
            
            # Update VIN index
            self.vin_index[vin] = listing_id
            self._save_vin_index()
            
            logger.info(f"Saved new listing with ID {listing_id} and VIN {vin}")
            return {
                'success': True,
                'updated': False,
                'id': listing_id,
                'changes': {},
                'change_summary': 'New listing created'
            }
        
        except Exception as e:
            logger.error(f"Error saving listing: {e}")
            raise
    
    def _update_existing_listing(self, listing_id, new_data):
        """Update an existing listing with new data."""
        listing_file = self.data_dir / f"{listing_id}.json"
        current_time = datetime.now().isoformat()
        
        try:
            # Load existing listing
            with open(listing_file, 'r', encoding='utf-8') as f:
                existing_listing = json.load(f)
            
            existing_data = existing_listing['data']
            
            # Merge multi-site data (handles URLs and site tracking)
            merged_data = merge_site_data(existing_data, new_data)
            
            # Compare and merge data for change detection
            comparison = compare_listing_data(existing_data, merged_data)
            
            # Always update last_seen_date when data is submitted
            # Preserve existing date fields (JIT migration should have added them if missing)
            created_date = existing_listing.get('created_date')
            last_modified_date = existing_listing.get('last_modified_date')
            deleted_date = existing_listing.get('deleted_date')
            
            # Determine if this is a meaningful modification (not just last_seen_date update)
            has_meaningful_changes = comparison['has_changes']
            
            # Always update last_seen_date
            last_seen_date = current_time
            
            # Only update last_modified_date if there are meaningful changes
            if has_meaningful_changes:
                last_modified_date = current_time
            
            # Update the listing (preserve comments field and date tracking)
            updated_listing = {
                'id': listing_id,
                'data': merged_data,
                'comments': existing_listing.get('comments', ''),  # Preserve existing comments
                'created_date': created_date,
                'last_modified_date': last_modified_date,
                'last_seen_date': last_seen_date,
                'deleted_date': deleted_date
            }
            
            # Save updated listing
            with open(listing_file, 'w', encoding='utf-8') as f:
                json.dump(updated_listing, f, indent=2, ensure_ascii=False)
            
            if has_meaningful_changes:
                change_summary = format_change_summary(comparison['changes'])
                logger.info(f"Updated listing {listing_id}: {change_summary}")
                
                return {
                    'success': False,  # Not a new listing
                    'updated': True,
                    'id': listing_id,
                    'changes': comparison['changes'],
                    'change_summary': change_summary
                }
            else:
                logger.info(f"Updated last_seen_date for listing {listing_id} (no other changes)")
                
                return {
                    'success': False,  # Not a new listing
                    'updated': True,   # File was updated (last_seen_date)
                    'id': listing_id,
                    'changes': {},  # No meaningful changes, only date tracking
                    'change_summary': 'Updated last seen date only'
                }
        
        except Exception as e:
            logger.error(f"Error updating listing {listing_id}: {e}")
            raise
    
    def get_all_listings(self):
        """Retrieve all listings."""
        listings = []
        
        for listing_file in self.data_dir.glob("*.json"):
            try:
                # Check if JIT migration is needed
                if not self.migrator.migrate_file_jit(listing_file):
                    logger.warning(f"JIT migration failed for {listing_file}")
                
                with open(listing_file, 'r', encoding='utf-8') as f:
                    listing_data = json.load(f)
                    # Ensure comments field exists for backward compatibility
                    if 'comments' not in listing_data:
                        listing_data['comments'] = ''
                    listings.append(listing_data)
            except Exception as e:
                logger.error(f"Error reading listing file {listing_file}: {e}")
                continue
        
        return listings
    
    def get_listing_count(self):
        """Get total number of stored listings."""
        return len(list(self.data_dir.glob("*.json")))
    
    def get_listing_by_id(self, listing_id):
        """Retrieve a single listing by ID."""
        listing_file = self.data_dir / f"{listing_id}.json"
        
        if not listing_file.exists():
            return None
        
        try:
            # Check if JIT migration is needed
            if not self.migrator.migrate_file_jit(listing_file):
                logger.warning(f"JIT migration failed for {listing_file}")
            
            with open(listing_file, 'r', encoding='utf-8') as f:
                listing_data = json.load(f)
                # Ensure comments field exists for backward compatibility
                if 'comments' not in listing_data:
                    listing_data['comments'] = ''
                return listing_data
        except Exception as e:
            logger.error(f"Error reading listing file {listing_file}: {e}")
            return None
    
    def delete_listing(self, listing_id):
        """
        Soft delete a listing by moving it to deleted folder and removing from index.
        
        Returns dict with:
        - 'success': True if deletion successful, False otherwise
        - 'message': Description of what happened
        - 'vin': VIN of deleted listing (if successful)
        """
        listing_file = self.data_dir / f"{listing_id}.json"
        
        if not listing_file.exists():
            logger.warning(f"Attempted to delete non-existent listing: {listing_id}")
            return {
                'success': False,
                'message': f'Listing {listing_id} not found'
            }
        
        try:
            # Load listing data to get VIN and other info
            with open(listing_file, 'r', encoding='utf-8') as f:
                listing_data = json.load(f)
            
            vin = listing_data.get('data', {}).get('vin')
            current_time = datetime.now().isoformat()
            
            # Create deleted directory if it doesn't exist
            deleted_dir = self.data_dir / 'deleted'
            deleted_dir.mkdir(parents=True, exist_ok=True)
            
            # Set deleted_date in the new date tracking system
            listing_data['deleted_date'] = current_time
            # Also preserve the old deleted_at field for backwards compatibility
            listing_data['deleted_at'] = current_time
            
            # Move file to deleted directory
            deleted_file = deleted_dir / f"{listing_id}.json"
            with open(deleted_file, 'w', encoding='utf-8') as f:
                json.dump(listing_data, f, indent=2, ensure_ascii=False)
            
            # Remove original file
            listing_file.unlink()
            
            # Remove from VIN index if VIN exists
            if vin and vin in self.vin_index:
                del self.vin_index[vin]
                self._save_vin_index()
            
            logger.info(f"Deleted listing {listing_id} with VIN: {vin}")
            
            return {
                'success': True,
                'message': f'Listing {listing_id} deleted successfully',
                'vin': vin
            }
        
        except Exception as e:
            logger.error(f"Error deleting listing {listing_id}: {e}")
            return {
                'success': False,
                'message': f'Error deleting listing: {str(e)}'
            }
    
    def update_comments(self, listing_id, comments):
        """
        Update the comments field for a listing.
        
        Args:
            listing_id: The ID of the listing to update
            comments: The new comments text (UTF-8 string with newlines preserved)
        
        Returns:
            dict with success status and message
        """
        listing_file = self.data_dir / f"{listing_id}.json"
        
        if not listing_file.exists():
            logger.warning(f"Attempted to update comments for non-existent listing: {listing_id}")
            return {
                'success': False,
                'message': f'Listing {listing_id} not found'
            }
        
        try:
            # Load existing listing
            with open(listing_file, 'r', encoding='utf-8') as f:
                listing_data = json.load(f)
            
            # Update comments field
            listing_data['comments'] = comments
            
            # Save back to file
            with open(listing_file, 'w', encoding='utf-8') as f:
                json.dump(listing_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Updated comments for listing {listing_id}")
            
            return {
                'success': True,
                'message': f'Comments updated for listing {listing_id}'
            }
        
        except Exception as e:
            logger.error(f"Error updating comments for listing {listing_id}: {e}")
            return {
                'success': False,
                'message': f'Error updating comments: {str(e)}'
            }
    
    def update_editable_fields(self, listing_id, fields):
        """
        Update editable fields for a listing.
        
        Args:
            listing_id: The ID of the listing to update
            fields: Dictionary of field names to values to update
        
        Returns:
            dict with success status and message
        """
        listing_file = self.data_dir / f"{listing_id}.json"
        
        if not listing_file.exists():
            logger.warning(f"Attempted to update editable fields for non-existent listing: {listing_id}")
            return {
                'success': False,
                'message': f'Listing {listing_id} not found'
            }
        
        try:
            # Check if JIT migration is needed
            if not self.migrator.migrate_file_jit(listing_file):
                logger.error(f"JIT migration failed for listing file: {listing_file}")
                return {
                    'success': False,
                    'message': 'Failed to migrate listing file'
                }
            
            # Load existing listing
            with open(listing_file, 'r', encoding='utf-8') as f:
                listing_data = json.load(f)
            
            # Update editable fields in the data section
            changes_made = []
            for field_name, field_value in fields.items():
                if field_name in ['performance_package']:  # Only allow specific editable fields
                    old_value = listing_data.get('data', {}).get(field_name)
                    if old_value != field_value:
                        listing_data['data'][field_name] = field_value
                        changes_made.append(f"{field_name}: {old_value} -> {field_value}")
            
            # Update modification timestamp if changes were made
            if changes_made:
                listing_data['last_modified_date'] = datetime.now().isoformat()
                
                # Save back to file
                with open(listing_file, 'w', encoding='utf-8') as f:
                    json.dump(listing_data, f, indent=2, ensure_ascii=False)
                
                logger.info(f"Updated editable fields for listing {listing_id}: {', '.join(changes_made)}")
                
                return {
                    'success': True,
                    'message': f'Fields updated for listing {listing_id}: {", ".join(changes_made)}'
                }
            else:
                logger.info(f"No changes made to editable fields for listing {listing_id}")
                return {
                    'success': True,
                    'message': f'No changes needed for listing {listing_id}'
                }
        
        except Exception as e:
            logger.error(f"Error updating editable fields for listing {listing_id}: {e}")
            return {
                'success': False,
                'message': f'Error updating editable fields: {str(e)}'
            }