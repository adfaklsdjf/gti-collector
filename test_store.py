#!/usr/bin/env python3
"""
Unit tests for the Store class.
Tests VIN deduplication, file operations, and data integrity.
"""

import pytest
import tempfile
import shutil
import json
from pathlib import Path
from store import Store


@pytest.fixture
def temp_store():
    """Create a Store instance with temporary directory for testing."""
    temp_dir = tempfile.mkdtemp()
    store = Store(data_dir=temp_dir)
    yield store
    # Cleanup after test
    shutil.rmtree(temp_dir)


@pytest.fixture
def sample_listing():
    """Sample GTI listing data for testing."""
    return {
        'url': 'https://test.com/listing/123',
        'price': '$25,000',
        'year': '2019',
        'mileage': '45000',
        'distance': '15 mi away',
        'vin': 'WVWZZZ1JZ1W123456',
        'title': '2019 Volkswagen Golf GTI 2.0T SE 4-Door FWD',
        'location': 'Cleveland, OH (15 mi away)'
    }


class TestStore:
    """Test cases for Store class functionality."""
    
    def test_add_new_listing_success(self, temp_store, sample_listing):
        """Test adding a new listing successfully."""
        result = temp_store.add_listing(sample_listing)
        
        assert result['success'] is True
        assert 'id' in result
        assert len(result['id']) == 36  # UUID length
        
        # Verify listing count
        assert temp_store.get_listing_count() == 1
        
        # Verify VIN index was updated
        assert sample_listing['vin'] in temp_store.vin_index
        assert temp_store.vin_index[sample_listing['vin']] == result['id']
    
    def test_add_duplicate_vin_rejected(self, temp_store, sample_listing):
        """Test that duplicate VINs are rejected."""
        # Add first listing
        result1 = temp_store.add_listing(sample_listing)
        assert result1['success'] is True
        
        # Try to add same VIN again (different URL)
        duplicate_listing = sample_listing.copy()
        duplicate_listing['url'] = 'https://different.com/listing/456'
        duplicate_listing['price'] = '$26,000'
        
        result2 = temp_store.add_listing(duplicate_listing)
        assert result2['success'] is False
        assert result2['id'] == result1['id']  # Same ID returned
        
        # Verify only one listing exists
        assert temp_store.get_listing_count() == 1
    
    def test_add_listing_missing_vin_fails(self, temp_store):
        """Test that listings without VIN fail."""
        listing_no_vin = {
            'url': 'https://test.com/listing/123',
            'price': '$25,000',
            'year': '2019',
            'mileage': '45000',
            'distance': '15 mi away'
            # Missing VIN
        }
        
        with pytest.raises(ValueError, match="VIN is required"):
            temp_store.add_listing(listing_no_vin)
    
    def test_get_all_listings(self, temp_store, sample_listing):
        """Test retrieving all listings."""
        # Empty store
        listings = temp_store.get_all_listings()
        assert listings == []
        
        # Add one listing
        temp_store.add_listing(sample_listing)
        listings = temp_store.get_all_listings()
        assert len(listings) == 1
        assert listings[0]['data']['vin'] == sample_listing['vin']
        assert listings[0]['data']['title'] == sample_listing['title']
        
        # Add second listing with different VIN
        second_listing = sample_listing.copy()
        second_listing['vin'] = 'WVWZZZ1JZ1W654321'
        second_listing['title'] = '2020 Volkswagen Golf GTI'
        temp_store.add_listing(second_listing)
        
        listings = temp_store.get_all_listings()
        assert len(listings) == 2
    
    def test_vin_index_persistence(self, temp_store, sample_listing):
        """Test that VIN index is saved and loaded correctly."""
        # Add listing
        result = temp_store.add_listing(sample_listing)
        listing_id = result['id']
        
        # Create new store instance with same directory
        new_store = Store(data_dir=temp_store.data_dir)
        
        # Verify VIN index was loaded
        assert sample_listing['vin'] in new_store.vin_index
        assert new_store.vin_index[sample_listing['vin']] == listing_id
        
        # Verify duplicate detection still works
        duplicate_result = new_store.add_listing(sample_listing)
        assert duplicate_result['success'] is False
        assert duplicate_result['id'] == listing_id
    
    def test_data_directory_creation(self):
        """Test that data directories are created if they don't exist."""
        temp_dir = tempfile.mkdtemp()
        data_path = Path(temp_dir) / 'nonexistent' / 'data'
        
        try:
            # This should create the directory structure
            store = Store(data_dir=str(data_path))
            assert data_path.exists()
            assert (data_path / 'indices').exists()
        finally:
            shutil.rmtree(temp_dir)
    
    def test_listing_file_structure(self, temp_store, sample_listing):
        """Test that listing files have correct structure."""
        result = temp_store.add_listing(sample_listing)
        listing_id = result['id']
        
        # Read the saved file directly
        listing_file = temp_store.data_dir / f"{listing_id}.json"
        assert listing_file.exists()
        
        with open(listing_file, 'r') as f:
            saved_data = json.load(f)
        
        assert 'id' in saved_data
        assert 'data' in saved_data
        assert saved_data['id'] == listing_id
        assert saved_data['data']['vin'] == sample_listing['vin']
        assert saved_data['data']['title'] == sample_listing['title']