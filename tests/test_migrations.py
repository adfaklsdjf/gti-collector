#!/usr/bin/env python3
"""
Tests for the data migration system.
"""

import pytest
import tempfile
import json
import shutil
from pathlib import Path
from schema_migrations import SchemaMigrator
from migrations.v001_url_to_multi_site import migrate as migrate_v001
from migrations.v002_add_schema_versioning import migrate as migrate_v002
from migrations.v004_add_performance_package import migrate as migrate_v004


class TestSchemaMigrator:
    """Test the SchemaMigrator class."""
    
    @pytest.fixture
    def temp_dirs(self):
        """Create temporary directories for testing."""
        temp_dir = Path(tempfile.mkdtemp())
        data_dir = temp_dir / "data"
        backup_dir = temp_dir / "backups"
        migrations_dir = temp_dir / "migrations"
        
        data_dir.mkdir()
        backup_dir.mkdir()
        migrations_dir.mkdir()
        
        yield data_dir, backup_dir, migrations_dir
        
        # Cleanup
        shutil.rmtree(temp_dir)
    
    def test_get_file_schema_version(self, temp_dirs):
        """Test reading schema version from files."""
        data_dir, backup_dir, migrations_dir = temp_dirs
        migrator = SchemaMigrator(str(data_dir), str(backup_dir), str(migrations_dir))
        
        # Test unversioned file
        test_file = data_dir / "test.json"
        test_data = {"data": {"test": "value"}}
        with open(test_file, 'w') as f:
            json.dump(test_data, f)
        
        version = migrator.get_file_schema_version(test_file)
        assert version == 0
        
        # Test versioned file
        versioned_data = {"schema_version": 2, "data": {"test": "value"}}
        with open(test_file, 'w') as f:
            json.dump(versioned_data, f)
        
        version = migrator.get_file_schema_version(test_file)
        assert version == 2
    
    def test_migrate_file_to_version(self, temp_dirs):
        """Test migrating a file using the v002 migration function."""
        data_dir, backup_dir, migrations_dir = temp_dirs
        
        # Create test data without schema version
        test_file = data_dir / "test.json"
        test_data = {"data": {"test": "value"}}
        with open(test_file, 'w') as f:
            json.dump(test_data, f)
        
        # Load and apply v002 migration directly
        with open(test_file, 'r') as f:
            file_data = json.load(f)
        
        migrated_data = migrate_v002(file_data)
        
        # Save migrated data back
        with open(test_file, 'w') as f:
            json.dump(migrated_data, f)
        
        # Verify schema version was added
        assert migrated_data["schema_version"] == 2


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
        """Test URL to multi-site migration using v001 migrate function."""
        # Run v001 migration directly on file data
        listing1_path = temp_data_dir / "listing1.json"
        with open(listing1_path, 'r') as f:
            listing1_data = json.load(f)
        
        # Apply v001 migration
        migrated_data = migrate_v001(listing1_data)
        
        # Save migrated data back
        with open(listing1_path, 'w') as f:
            json.dump(migrated_data, f, indent=2)
        
        # Check migration results
        with open(listing1_path, 'r') as f:
            listing1 = json.load(f)
        
        data1 = listing1["data"]
        assert "url" not in data1  # Old field removed
        assert "urls" in data1     # New field added
        assert data1["urls"]["cargurus"] == "https://cargurus.com/listing/123"
        assert data1["last_updated_site"] == "cargurus"
        assert data1["sites_seen"] == ["cargurus"]
    
    def test_migration_idempotent(self, temp_data_dir):
        """Test that migration can be run multiple times safely."""
        # Load and migrate listing twice
        listing1_path = temp_data_dir / "listing1.json"
        with open(listing1_path, 'r') as f:
            original_data = json.load(f)
        
        # First migration
        migrated_once = migrate_v001(original_data)
        # Second migration on already migrated data
        migrated_twice = migrate_v001(migrated_once)
        
        # Should be unchanged after second migration
        assert migrated_once == migrated_twice
        
        # Verify data is still correct
        data1 = migrated_twice["data"]
        assert data1["urls"]["cargurus"] == "https://cargurus.com/listing/123"
        assert data1["last_updated_site"] == "cargurus"
    
    def test_v004_performance_package_migration(self):
        """Test v004 migration adds performance_package field."""
        # Create test listing without performance_package
        test_listing = {
            "schema_version": 3,
            "id": "test-id",
            "data": {
                "price": "$25000",
                "year": "2019",
                "mileage": "45000",
                "vin": "WVWZZZ1JZ1W123456"
            },
            "comments": "",
            "created_date": "2023-01-01T12:00:00",
            "last_modified_date": "2023-01-01T12:00:00",
            "last_seen_date": "2023-01-01T12:00:00",
            "deleted_date": None
        }
        
        # Apply v004 migration
        migrated_listing = migrate_v004(test_listing)
        
        # Verify performance_package field was added with None value
        assert 'performance_package' in migrated_listing['data']
        assert migrated_listing['data']['performance_package'] is None
        
        # Verify other fields are unchanged
        assert migrated_listing['data']['price'] == "$25000"
        assert migrated_listing['data']['year'] == "2019"
        assert migrated_listing['id'] == "test-id"
    
    def test_v004_migration_idempotent(self):
        """Test that v004 migration can be run multiple times safely."""
        # Create test listing
        test_listing = {
            "schema_version": 3,
            "id": "test-id",
            "data": {
                "price": "$25000",
                "year": "2019",
                "performance_package": True  # Already has the field
            }
        }
        
        # Apply migration twice
        migrated_once = migrate_v004(test_listing)
        migrated_twice = migrate_v004(migrated_once)
        
        # Should be unchanged after second migration
        assert migrated_once == migrated_twice
        
        # Verify field value is preserved
        assert migrated_twice['data']['performance_package'] is True