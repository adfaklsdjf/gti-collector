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
    """Sample GTI listing data for testing (in internal processed format)."""
    return {
        'urls': {'cargurus': 'https://test.com/listing/123'},
        'last_updated_site': 'cargurus',
        'sites_seen': ['cargurus'],
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
    
    def test_add_duplicate_vin_upsert(self, temp_store, sample_listing):
        """Test that duplicate VINs trigger upsert behavior."""
        # Add first listing
        result1 = temp_store.add_listing(sample_listing)
        assert result1['success'] is True
        assert result1['updated'] is False
        
        # Try to add same VIN again with different data
        updated_listing = sample_listing.copy()
        updated_listing['urls'] = {'cargurus': 'https://different.com/listing/456'}
        updated_listing['price'] = '$26,000'
        updated_listing['title'] = 'Updated Title'
        
        result2 = temp_store.add_listing(updated_listing)
        assert result2['success'] is False  # Not a new listing
        assert result2['updated'] is True   # But was updated
        assert result2['id'] == result1['id']  # Same ID returned
        assert 'price' in result2['changes']
        assert 'title' in result2['changes']
        # URLs get merged in multi-site system, not tracked as changes when same site
        
        # Verify only one listing exists but with updated data
        assert temp_store.get_listing_count() == 1
        listings = temp_store.get_all_listings()
        assert listings[0]['data']['price'] == '$26,000'
        assert listings[0]['data']['title'] == 'Updated Title'
    
    def test_add_duplicate_vin_no_changes(self, temp_store, sample_listing):
        """Test duplicate VIN with identical data."""
        # Add first listing
        result1 = temp_store.add_listing(sample_listing)
        assert result1['success'] is True
        
        # Try to add identical listing
        result2 = temp_store.add_listing(sample_listing)
        assert result2['success'] is False
        assert result2['updated'] is True  # File was updated (last_seen_date)
        assert result2['change_summary'] == 'Updated last seen date only'
        assert result2['changes'] == {}
        
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
    
    def test_get_listing_by_id(self, temp_store, sample_listing):
        """Test retrieving a single listing by ID."""
        # Add a listing
        result = temp_store.add_listing(sample_listing)
        listing_id = result['id']
        
        # Retrieve it by ID
        retrieved_listing = temp_store.get_listing_by_id(listing_id)
        
        assert retrieved_listing is not None
        assert retrieved_listing['id'] == listing_id
        assert retrieved_listing['data']['vin'] == sample_listing['vin']
        assert retrieved_listing['data']['title'] == sample_listing['title']
        assert retrieved_listing['data']['price'] == sample_listing['price']
    
    def test_get_listing_by_id_not_found(self, temp_store):
        """Test retrieving non-existent listing returns None."""
        fake_id = 'nonexistent-listing-id'
        retrieved_listing = temp_store.get_listing_by_id(fake_id)
        
        assert retrieved_listing is None
    
    def test_delete_listing_success(self, temp_store, sample_listing):
        """Test successfully deleting a listing."""
        # Add a listing first
        result = temp_store.add_listing(sample_listing)
        listing_id = result['id']
        
        # Verify listing exists
        assert temp_store.get_listing_by_id(listing_id) is not None
        assert sample_listing['vin'] in temp_store.vin_index
        
        # Delete the listing
        delete_result = temp_store.delete_listing(listing_id)
        
        # Verify deletion was successful
        assert delete_result['success'] is True
        assert 'deleted successfully' in delete_result['message']
        assert delete_result['vin'] == sample_listing['vin']
        
        # Verify listing no longer exists in main directory
        assert temp_store.get_listing_by_id(listing_id) is None
        
        # Verify VIN removed from index
        assert sample_listing['vin'] not in temp_store.vin_index
        
        # Verify listing count decreased
        assert temp_store.get_listing_count() == 0
    
    def test_delete_listing_moved_to_deleted_folder(self, temp_store, sample_listing):
        """Test that deleted listing is moved to deleted folder."""
        # Add a listing first
        result = temp_store.add_listing(sample_listing)
        listing_id = result['id']
        
        # Delete the listing
        delete_result = temp_store.delete_listing(listing_id)
        assert delete_result['success'] is True
        
        # Verify file exists in deleted folder
        deleted_file = temp_store.data_dir / 'deleted' / f"{listing_id}.json"
        assert deleted_file.exists()
        
        # Verify deleted file contains original data plus deletion timestamp
        with open(deleted_file, 'r') as f:
            deleted_data = json.load(f)
        
        assert deleted_data['id'] == listing_id
        assert deleted_data['data']['vin'] == sample_listing['vin']
        assert deleted_data['data']['title'] == sample_listing['title']
        assert 'deleted_at' in deleted_data
        assert deleted_data['deleted_at'] is not None
    
    def test_delete_listing_not_found(self, temp_store):
        """Test deleting non-existent listing returns appropriate error."""
        fake_id = 'nonexistent-listing-id'
        delete_result = temp_store.delete_listing(fake_id)
        
        assert delete_result['success'] is False
        assert 'not found' in delete_result['message']
        assert fake_id in delete_result['message']
    
    def test_delete_listing_creates_deleted_directory(self, temp_store, sample_listing):
        """Test that deleted directory is created if it doesn't exist."""
        # Add a listing first
        result = temp_store.add_listing(sample_listing)
        listing_id = result['id']
        
        # Verify deleted directory doesn't exist yet
        deleted_dir = temp_store.data_dir / 'deleted'
        assert not deleted_dir.exists()
        
        # Delete the listing
        delete_result = temp_store.delete_listing(listing_id)
        assert delete_result['success'] is True
        
        # Verify deleted directory was created
        assert deleted_dir.exists()
        assert deleted_dir.is_dir()
    
    def test_delete_multiple_listings(self, temp_store, sample_listing):
        """Test deleting multiple listings."""
        # Add two listings
        result1 = temp_store.add_listing(sample_listing)
        listing_id1 = result1['id']
        
        second_listing = sample_listing.copy()
        second_listing['vin'] = 'WVWZZZ1JZ1W654321'
        second_listing['title'] = 'Different GTI'
        result2 = temp_store.add_listing(second_listing)
        listing_id2 = result2['id']
        
        # Verify both exist
        assert temp_store.get_listing_count() == 2
        
        # Delete first listing
        delete_result1 = temp_store.delete_listing(listing_id1)
        assert delete_result1['success'] is True
        assert temp_store.get_listing_count() == 1
        
        # Delete second listing
        delete_result2 = temp_store.delete_listing(listing_id2)
        assert delete_result2['success'] is True
        assert temp_store.get_listing_count() == 0
        
        # Verify both are in deleted folder
        deleted_dir = temp_store.data_dir / 'deleted'
        deleted_files = list(deleted_dir.glob("*.json"))
        assert len(deleted_files) == 2
    
    def test_update_comments_success(self, temp_store, sample_listing):
        """Test successfully updating comments for a listing."""
        # Add a listing first
        result = temp_store.add_listing(sample_listing)
        listing_id = result['id']
        
        # Update comments
        test_comments = "This is a great car!\nLooks very clean.\nWill check it out tomorrow."
        update_result = temp_store.update_comments(listing_id, test_comments)
        
        assert update_result['success'] is True
        assert 'updated' in update_result['message']
        
        # Verify comments were saved
        retrieved_listing = temp_store.get_listing_by_id(listing_id)
        assert retrieved_listing['comments'] == test_comments
    
    def test_update_comments_with_unicode(self, temp_store, sample_listing):
        """Test updating comments with unicode characters."""
        # Add a listing first
        result = temp_store.add_listing(sample_listing)
        listing_id = result['id']
        
        # Update comments with unicode
        test_comments = "Great car! 🚗\nPrice looks good 💰\nEmoji test: 🎉 ✨ 🔥"
        update_result = temp_store.update_comments(listing_id, test_comments)
        
        assert update_result['success'] is True
        
        # Verify unicode was preserved
        retrieved_listing = temp_store.get_listing_by_id(listing_id)
        assert retrieved_listing['comments'] == test_comments
    
    def test_update_comments_empty_string(self, temp_store, sample_listing):
        """Test updating comments with empty string (clearing comments)."""
        # Add a listing first
        result = temp_store.add_listing(sample_listing)
        listing_id = result['id']
        
        # First add some comments
        temp_store.update_comments(listing_id, "Some initial comments")
        
        # Then clear them
        update_result = temp_store.update_comments(listing_id, "")
        
        assert update_result['success'] is True
        
        # Verify comments were cleared
        retrieved_listing = temp_store.get_listing_by_id(listing_id)
        assert retrieved_listing['comments'] == ""
    
    def test_update_comments_not_found(self, temp_store):
        """Test updating comments for non-existent listing."""
        fake_id = 'nonexistent-listing-id'
        update_result = temp_store.update_comments(fake_id, "Some comments")
        
        assert update_result['success'] is False
        assert 'not found' in update_result['message']
        assert fake_id in update_result['message']
    
    def test_comments_preserved_during_listing_update(self, temp_store, sample_listing):
        """Test that comments are preserved when listing data is updated."""
        # Add a listing first
        result = temp_store.add_listing(sample_listing)
        listing_id = result['id']
        
        # Add comments
        test_comments = "My notes about this car"
        temp_store.update_comments(listing_id, test_comments)
        
        # Update the listing data (should preserve comments)
        updated_listing = sample_listing.copy()
        updated_listing['price'] = '$24,000'
        temp_store.add_listing(updated_listing)
        
        # Verify comments were preserved
        retrieved_listing = temp_store.get_listing_by_id(listing_id)
        assert retrieved_listing['comments'] == test_comments
        assert retrieved_listing['data']['price'] == '$24,000'
    
    def test_new_listing_has_empty_comments(self, temp_store, sample_listing):
        """Test that new listings start with empty comments."""
        result = temp_store.add_listing(sample_listing)
        listing_id = result['id']
        
        # Verify new listing has empty comments
        retrieved_listing = temp_store.get_listing_by_id(listing_id)
        assert retrieved_listing['comments'] == ""
    
    def test_update_performance_package_success(self, temp_store, sample_listing):
        """Test successfully updating performance_package field."""
        # Add a listing first
        result = temp_store.add_listing(sample_listing)
        listing_id = result['id']
        
        # Update performance_package to True
        update_result = temp_store.update_editable_fields(listing_id, {'performance_package': True})
        
        assert update_result['success'] is True
        assert 'performance_package' in update_result['message']
        
        # Verify field was saved
        retrieved_listing = temp_store.get_listing_by_id(listing_id)
        assert retrieved_listing['data']['performance_package'] is True
        
        # Update to False
        update_result = temp_store.update_editable_fields(listing_id, {'performance_package': False})
        
        assert update_result['success'] is True
        
        # Verify field was updated
        retrieved_listing = temp_store.get_listing_by_id(listing_id)
        assert retrieved_listing['data']['performance_package'] is False
    
    def test_update_performance_package_none_value(self, temp_store, sample_listing):
        """Test updating performance_package to None (not set)."""
        # Add a listing first
        result = temp_store.add_listing(sample_listing)
        listing_id = result['id']
        
        # Set to True first
        temp_store.update_editable_fields(listing_id, {'performance_package': True})
        
        # Update performance_package to None
        update_result = temp_store.update_editable_fields(listing_id, {'performance_package': None})
        
        assert update_result['success'] is True
        
        # Verify field was set to None
        retrieved_listing = temp_store.get_listing_by_id(listing_id)
        assert retrieved_listing['data']['performance_package'] is None
    
    def test_update_editable_fields_no_changes(self, temp_store, sample_listing):
        """Test updating editable fields when no changes are made."""
        # Add a listing first
        result = temp_store.add_listing(sample_listing)
        listing_id = result['id']
        
        # Set performance_package to True first
        temp_store.update_editable_fields(listing_id, {'performance_package': True})
        
        # Try to set it to True again (no change)
        update_result = temp_store.update_editable_fields(listing_id, {'performance_package': True})
        
        assert update_result['success'] is True
        assert 'No changes needed' in update_result['message']
    
    def test_update_editable_fields_not_found(self, temp_store):
        """Test updating editable fields for non-existent listing."""
        fake_id = 'nonexistent-listing-id'
        update_result = temp_store.update_editable_fields(fake_id, {'performance_package': True})
        
        assert update_result['success'] is False
        assert 'not found' in update_result['message']
        assert fake_id in update_result['message']
    
    def test_update_editable_fields_invalid_field(self, temp_store, sample_listing):
        """Test that only allowed editable fields can be updated."""
        # Add a listing first
        result = temp_store.add_listing(sample_listing)
        listing_id = result['id']
        
        # Try to update a non-editable field
        update_result = temp_store.update_editable_fields(listing_id, {'price': '$30000', 'performance_package': True})
        
        assert update_result['success'] is True
        
        # Verify only performance_package was updated, not price
        retrieved_listing = temp_store.get_listing_by_id(listing_id)
        assert retrieved_listing['data']['performance_package'] is True
        assert retrieved_listing['data']['price'] == '$25,000'  # Original price unchanged
    
    def test_editable_fields_preserved_during_listing_update(self, temp_store, sample_listing):
        """Test that editable fields are preserved when listing data is updated."""
        # Add a listing first
        result = temp_store.add_listing(sample_listing)
        listing_id = result['id']
        
        # Set performance_package
        temp_store.update_editable_fields(listing_id, {'performance_package': True})
        
        # Update the listing data (should preserve editable fields)
        updated_listing = sample_listing.copy()
        updated_listing['price'] = '$24,000'
        temp_store.add_listing(updated_listing)
        
        # Verify performance_package was preserved
        retrieved_listing = temp_store.get_listing_by_id(listing_id)
        assert retrieved_listing['data']['performance_package'] is True
        assert retrieved_listing['data']['price'] == '$24,000'
    
    def test_backward_compatibility_missing_comments(self, temp_store, sample_listing):
        """Test that old listings without comments field get empty comments."""
        # Add a listing first
        result = temp_store.add_listing(sample_listing)
        listing_id = result['id']
        
        # Manually modify the file to remove comments field (simulating old format)
        listing_file = temp_store.data_dir / f"{listing_id}.json"
        with open(listing_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Remove comments field
        del data['comments']
        
        with open(listing_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        # Now retrieve the listing - should have empty comments
        retrieved_listing = temp_store.get_listing_by_id(listing_id)
        assert retrieved_listing['comments'] == ""
    
    def test_new_listing_has_date_fields(self, temp_store, sample_listing):
        """Test that new listings have all date tracking fields set."""
        result = temp_store.add_listing(sample_listing)
        listing_id = result['id']
        
        # Verify new listing has all date fields
        retrieved_listing = temp_store.get_listing_by_id(listing_id)
        assert 'created_date' in retrieved_listing
        assert 'last_modified_date' in retrieved_listing
        assert 'last_seen_date' in retrieved_listing
        assert 'deleted_date' in retrieved_listing
        
        # Verify date values are reasonable
        assert retrieved_listing['created_date'] is not None
        assert retrieved_listing['last_modified_date'] is not None
        assert retrieved_listing['last_seen_date'] is not None
        assert retrieved_listing['deleted_date'] is None  # Active listing
        
        # Verify created_date == last_modified_date == last_seen_date for new listing
        assert retrieved_listing['created_date'] == retrieved_listing['last_modified_date']
        assert retrieved_listing['created_date'] == retrieved_listing['last_seen_date']
    
    def test_update_with_changes_updates_modified_date(self, temp_store, sample_listing):
        """Test that meaningful changes update last_modified_date."""
        # Add initial listing
        result = temp_store.add_listing(sample_listing)
        listing_id = result['id']
        original_listing = temp_store.get_listing_by_id(listing_id)
        
        import time
        time.sleep(0.01)  # Small delay to ensure different timestamps
        
        # Update with meaningful changes
        updated_listing = sample_listing.copy()
        updated_listing['price'] = '$26,000'
        updated_listing['title'] = 'Updated Title'
        
        update_result = temp_store.add_listing(updated_listing)
        assert update_result['updated'] is True
        assert 'price' in update_result['changes']
        
        # Check the updated listing
        final_listing = temp_store.get_listing_by_id(listing_id)
        
        # created_date should not change
        assert final_listing['created_date'] == original_listing['created_date']
        
        # last_modified_date should be updated
        assert final_listing['last_modified_date'] != original_listing['last_modified_date']
        
        # last_seen_date should be updated
        assert final_listing['last_seen_date'] != original_listing['last_seen_date']
        
        # deleted_date should remain None
        assert final_listing['deleted_date'] is None
    
    def test_update_without_changes_only_updates_seen_date(self, temp_store, sample_listing):
        """Test that duplicate data only updates last_seen_date."""
        # Add initial listing
        result = temp_store.add_listing(sample_listing)
        listing_id = result['id']
        original_listing = temp_store.get_listing_by_id(listing_id)
        
        import time
        time.sleep(0.01)  # Small delay to ensure different timestamps
        
        # Submit identical data
        update_result = temp_store.add_listing(sample_listing)
        assert update_result['updated'] is True  # File was updated (last_seen_date)
        assert update_result['change_summary'] == 'Updated last seen date only'
        
        # Check the updated listing
        final_listing = temp_store.get_listing_by_id(listing_id)
        
        # created_date should not change
        assert final_listing['created_date'] == original_listing['created_date']
        
        # last_modified_date should NOT change (no meaningful changes)
        assert final_listing['last_modified_date'] == original_listing['last_modified_date']
        
        # last_seen_date should be updated
        assert final_listing['last_seen_date'] != original_listing['last_seen_date']
        
        # deleted_date should remain None
        assert final_listing['deleted_date'] is None
    
    def test_delete_listing_sets_deleted_date(self, temp_store, sample_listing):
        """Test that deleting a listing sets deleted_date."""
        # Add a listing first
        result = temp_store.add_listing(sample_listing)
        listing_id = result['id']
        
        # Delete the listing
        delete_result = temp_store.delete_listing(listing_id)
        assert delete_result['success'] is True
        
        # Verify file exists in deleted folder with deleted_date set
        deleted_file = temp_store.data_dir / 'deleted' / f"{listing_id}.json"
        assert deleted_file.exists()
        
        with open(deleted_file, 'r') as f:
            deleted_data = json.load(f)
        
        # Verify both old and new deletion timestamps are set
        assert 'deleted_at' in deleted_data  # Backwards compatibility
        assert 'deleted_date' in deleted_data  # New date tracking system
        assert deleted_data['deleted_date'] is not None
        assert deleted_data['deleted_at'] is not None
        assert deleted_data['deleted_date'] == deleted_data['deleted_at']  # Should be same
    
    def test_backward_compatibility_missing_date_fields(self, temp_store, sample_listing):
        """Test that old listings without date fields get default values."""
        # Add a listing first
        result = temp_store.add_listing(sample_listing)
        listing_id = result['id']
        
        # Manually modify the file to remove date fields (simulating old format)
        listing_file = temp_store.data_dir / f"{listing_id}.json"
        with open(listing_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Remove date fields
        for field in ['created_date', 'last_modified_date', 'last_seen_date', 'deleted_date']:
            if field in data:
                del data[field]
        
        with open(listing_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        # Now retrieve the listing - should have date fields populated
        retrieved_listing = temp_store.get_listing_by_id(listing_id)
        assert 'created_date' in retrieved_listing
        assert 'last_modified_date' in retrieved_listing
        assert 'last_seen_date' in retrieved_listing
        assert 'deleted_date' in retrieved_listing
        assert retrieved_listing['deleted_date'] is None
        
        # All other date fields should have reasonable values
        assert retrieved_listing['created_date'] is not None
        assert retrieved_listing['last_modified_date'] is not None
        assert retrieved_listing['last_seen_date'] is not None