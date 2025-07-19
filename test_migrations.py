#!/usr/bin/env python3
"""
Tests for the data migration system.
"""

import pytest
import tempfile
import json
import shutil
from pathlib import Path
from migrations import DataMigrator, migration_url_to_multi_site


class TestDataMigrator:
    """Test the DataMigrator class."""
    
    @pytest.fixture
    def temp_dirs(self):
        """Create temporary directories for testing."""
        temp_dir = Path(tempfile.mkdtemp())
        data_dir = temp_dir / "data"
        backup_dir = temp_dir / "backups"
        
        data_dir.mkdir()
        backup_dir.mkdir()
        
        yield data_dir, backup_dir
        
        # Cleanup
        shutil.rmtree(temp_dir)
    
    def test_create_backup(self, temp_dirs):
        """Test backup creation."""
        data_dir, backup_dir = temp_dirs
        migrator = DataMigrator(str(data_dir), str(backup_dir))
        
        # Create some test data
        test_file = data_dir / "test.json"
        test_data = {"test": "data"}
        with open(test_file, 'w') as f:
            json.dump(test_data, f)
        
        # Create backup
        backup_path = migrator.create_backup("test_migration")
        
        assert backup_path.exists()
        assert backup_path.name.startswith("data_backup_test_migration_")
        assert backup_path.suffix == ".gz"
    
    def test_restore_backup(self, temp_dirs):
        """Test backup restoration."""
        data_dir, backup_dir = temp_dirs
        migrator = DataMigrator(str(data_dir), str(backup_dir))
        
        # Create test data and backup
        test_file = data_dir / "test.json"
        original_data = {"original": "data"}
        with open(test_file, 'w') as f:
            json.dump(original_data, f)
        
        backup_path = migrator.create_backup("test_restore")
        
        # Modify data
        modified_data = {"modified": "data"}
        with open(test_file, 'w') as f:
            json.dump(modified_data, f)
        
        # Restore backup
        success = migrator.restore_backup(backup_path)
        assert success
        
        # Verify restoration
        with open(test_file, 'r') as f:
            restored_data = json.load(f)
        assert restored_data == original_data
    
    def test_migration_function(self, temp_dirs):
        """Test running a migration function."""
        data_dir, backup_dir = temp_dirs
        migrator = DataMigrator(str(data_dir), str(backup_dir))
        
        # Create test data
        test_file = data_dir / "test.json"
        with open(test_file, 'w') as f:
            json.dump({"test": "data"}, f)
        
        # Define a simple migration
        def test_migration(data_path):
            test_file = data_path / "test.json"
            with open(test_file, 'r') as f:
                data = json.load(f)
            data["migrated"] = True
            with open(test_file, 'w') as f:
                json.dump(data, f)
            return True
        
        # Run migration
        success = migrator.run_migration("test_migration", test_migration)
        assert success
        
        # Verify migration worked
        with open(test_file, 'r') as f:
            data = json.load(f)
        assert data["migrated"] is True


class TestURLMigration:
    """Test the specific URL to multi-site migration."""
    
    @pytest.fixture
    def temp_data_dir(self):
        """Create temporary data directory with test listings."""
        temp_dir = Path(tempfile.mkdtemp())
        data_dir = temp_dir / "data"
        data_dir.mkdir()
        
        # Create test listings with old URL format
        listings = [
            {
                "id": "listing1",
                "data": {
                    "url": "https://cargurus.com/listing/123",
                    "price": "$25000",
                    "year": "2020",
                    "vin": "VIN123"
                },
                "comments": ""
            },
            {
                "id": "listing2", 
                "data": {
                    "url": "https://autotrader.com/listing/456",
                    "price": "$30000",
                    "year": "2021",
                    "vin": "VIN456"
                },
                "comments": ""
            }
        ]
        
        for i, listing in enumerate(listings):
            file_path = data_dir / f"listing{i+1}.json"
            with open(file_path, 'w') as f:
                json.dump(listing, f, indent=2)
        
        yield data_dir
        
        # Cleanup
        shutil.rmtree(temp_dir)
    
    def test_url_migration(self, temp_data_dir):
        """Test URL to multi-site migration."""
        # Run migration
        success = migration_url_to_multi_site(temp_data_dir)
        assert success
        
        # Check migration results
        listing1_path = temp_data_dir / "listing1.json"
        with open(listing1_path, 'r') as f:
            listing1 = json.load(f)
        
        data1 = listing1["data"]
        assert "url" not in data1  # Old field removed
        assert "urls" in data1     # New field added
        assert data1["urls"]["cargurus"] == "https://cargurus.com/listing/123"
        assert data1["last_updated_site"] == "cargurus"
        assert data1["sites_seen"] == ["cargurus"]
        
        # Check second listing
        listing2_path = temp_data_dir / "listing2.json"
        with open(listing2_path, 'r') as f:
            listing2 = json.load(f)
        
        data2 = listing2["data"]
        assert data2["urls"]["autotrader"] == "https://autotrader.com/listing/456"
        assert data2["last_updated_site"] == "autotrader"
        assert data2["sites_seen"] == ["autotrader"]
    
    def test_migration_idempotent(self, temp_data_dir):
        """Test that migration can be run multiple times safely."""
        # Run migration twice
        success1 = migration_url_to_multi_site(temp_data_dir)
        success2 = migration_url_to_multi_site(temp_data_dir)
        
        assert success1
        assert success2
        
        # Verify data is still correct
        listing1_path = temp_data_dir / "listing1.json"
        with open(listing1_path, 'r') as f:
            listing1 = json.load(f)
        
        data1 = listing1["data"]
        assert data1["urls"]["cargurus"] == "https://cargurus.com/listing/123"
        assert data1["last_updated_site"] == "cargurus"