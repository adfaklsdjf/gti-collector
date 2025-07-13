#!/usr/bin/env python3
"""
Storage module for GTI listings.
Handles persistence and deduplication based on VIN.
"""

import json
import os
import uuid
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class Store:
    """Simple file-based storage with VIN deduplication."""
    
    def __init__(self, data_dir='data'):
        """Initialize store with data directory."""
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        # Create indices directory for tracking VINs
        self.indices_dir = self.data_dir / 'indices'
        self.indices_dir.mkdir(exist_ok=True)
        
        self.vin_index_file = self.indices_dir / 'vin_to_id.json'
        self.vin_index = self._load_vin_index()
    
    def _load_vin_index(self):
        """Load VIN to file ID mapping."""
        if self.vin_index_file.exists():
            try:
                with open(self.vin_index_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading VIN index: {e}")
                return {}
        return {}
    
    def _save_vin_index(self):
        """Save VIN to file ID mapping."""
        try:
            with open(self.vin_index_file, 'w') as f:
                json.dump(self.vin_index, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving VIN index: {e}")
    
    def add_listing(self, listing_data):
        """
        Add a listing to storage.
        Returns dict with 'success' boolean and 'id' of listing.
        """
        vin = listing_data.get('vin')
        
        if not vin:
            raise ValueError("VIN is required for storage")
        
        # Check if VIN already exists
        if vin in self.vin_index:
            existing_id = self.vin_index[vin]
            logger.info(f"Listing with VIN {vin} already exists with ID {existing_id}")
            return {'success': False, 'id': existing_id}
        
        # Generate new unique ID
        listing_id = str(uuid.uuid4())
        
        # Add metadata
        listing_with_metadata = {
            'id': listing_id,
            'data': listing_data
        }
        
        # Save listing to file
        listing_file = self.data_dir / f"{listing_id}.json"
        try:
            with open(listing_file, 'w') as f:
                json.dump(listing_with_metadata, f, indent=2)
            
            # Update VIN index
            self.vin_index[vin] = listing_id
            self._save_vin_index()
            
            logger.info(f"Saved new listing with ID {listing_id} and VIN {vin}")
            return {'success': True, 'id': listing_id}
        
        except Exception as e:
            logger.error(f"Error saving listing: {e}")
            raise
    
    def get_all_listings(self):
        """Retrieve all listings."""
        listings = []
        
        for listing_file in self.data_dir.glob("*.json"):
            try:
                with open(listing_file, 'r') as f:
                    listing_data = json.load(f)
                    listings.append(listing_data)
            except Exception as e:
                logger.error(f"Error reading listing file {listing_file}: {e}")
                continue
        
        return listings
    
    def get_listing_count(self):
        """Get total number of stored listings."""
        return len(list(self.data_dir.glob("*.json")))