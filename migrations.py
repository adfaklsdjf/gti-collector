#!/usr/bin/env python3
"""
Data migration framework for GTI Listings app.
Provides repeatable, safe data structure evolution with backups and logging.
"""

import json
import logging
import tarfile
import shutil
import sys
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Callable, Optional

# Set up migration-specific logging
migration_logger = logging.getLogger('migrations')
migration_handler = logging.FileHandler('migrations.log')
migration_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
migration_handler.setFormatter(migration_formatter)
migration_logger.addHandler(migration_handler)
migration_logger.setLevel(logging.INFO)

class MigrationError(Exception):
    """Custom exception for migration errors."""
    pass

class DataMigrator:
    """
    Data migration system with automatic backups and rollback capability.
    """
    
    def __init__(self, data_dir: str = "data", backup_dir: str = "backups"):
        self.data_dir = Path(data_dir)
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(exist_ok=True)
        
        migration_logger.info(f"🚀 DataMigrator initialized - data: {self.data_dir}, backups: {self.backup_dir}")
    
    def create_backup(self, migration_name: str) -> Path:
        """
        Create a timestamped tarball backup of the data directory.
        
        Args:
            migration_name: Name of the migration being performed
            
        Returns:
            Path to the created backup file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"data_backup_{migration_name}_{timestamp}.tar.gz"
        backup_path = self.backup_dir / backup_filename
        
        if not self.data_dir.exists():
            migration_logger.warning(f"⚠️ Data directory {self.data_dir} does not exist, creating empty backup")
            # Create empty backup
            with tarfile.open(backup_path, "w:gz") as tar:
                pass
            return backup_path
        
        migration_logger.info(f"📦 Creating backup: {backup_filename}")
        
        try:
            with tarfile.open(backup_path, "w:gz") as tar:
                tar.add(self.data_dir, arcname="data", recursive=True)
            
            backup_size = backup_path.stat().st_size / (1024 * 1024)  # MB
            migration_logger.info(f"✅ Backup created successfully: {backup_filename} ({backup_size:.2f} MB)")
            
            return backup_path
            
        except Exception as e:
            migration_logger.error(f"❌ Failed to create backup: {e}")
            raise MigrationError(f"Backup creation failed: {e}")
    
    def restore_backup(self, backup_path: Path) -> bool:
        """
        Restore data from a backup file.
        
        Args:
            backup_path: Path to the backup file
            
        Returns:
            True if restoration successful
        """
        if not backup_path.exists():
            migration_logger.error(f"❌ Backup file not found: {backup_path}")
            return False
        
        migration_logger.info(f"🔄 Restoring backup: {backup_path.name}")
        
        try:
            # Remove current data directory if it exists
            if self.data_dir.exists():
                shutil.rmtree(self.data_dir)
                migration_logger.info(f"🗑️ Removed existing data directory")
            
            # Extract backup
            with tarfile.open(backup_path, "r:gz") as tar:
                tar.extractall(path=self.data_dir.parent, filter='data')
            
            migration_logger.info(f"✅ Backup restored successfully")
            return True
            
        except Exception as e:
            migration_logger.error(f"❌ Failed to restore backup: {e}")
            return False
    
    def list_backups(self) -> List[Path]:
        """List all available backup files."""
        backups = list(self.backup_dir.glob("data_backup_*.tar.gz"))
        backups.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        return backups
    
    def run_migration(self, migration_name: str, migration_func: Callable[[Path], bool]) -> bool:
        """
        Run a migration with automatic backup and error handling.
        
        Args:
            migration_name: Name/identifier for the migration
            migration_func: Function that performs the migration
            
        Returns:
            True if migration successful
        """
        migration_logger.info(f"🔧 Starting migration: {migration_name}")
        
        # Create backup before migration
        try:
            backup_path = self.create_backup(migration_name)
        except MigrationError as e:
            migration_logger.error(f"❌ Migration aborted due to backup failure: {e}")
            return False
        
        # Run the migration
        try:
            migration_logger.info(f"⚡ Executing migration function...")
            success = migration_func(self.data_dir)
            
            if success:
                migration_logger.info(f"✅ Migration '{migration_name}' completed successfully")
                return True
            else:
                migration_logger.error(f"❌ Migration '{migration_name}' failed")
                return False
                
        except Exception as e:
            migration_logger.error(f"💥 Migration '{migration_name}' crashed: {e}")
            
            # Offer to restore backup
            migration_logger.info(f"🔄 Attempting automatic rollback...")
            if self.restore_backup(backup_path):
                migration_logger.info(f"✅ Rollback successful, data restored from backup")
            else:
                migration_logger.error(f"❌ Rollback failed! Manual restoration may be needed")
                migration_logger.error(f"📋 Backup location: {backup_path}")
            
            return False
    
    def get_listing_files(self) -> List[Path]:
        """Get all listing JSON files in the data directory."""
        if not self.data_dir.exists():
            return []
        return list(self.data_dir.glob("*.json"))
    
    def load_listing(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """
        Load a listing from a JSON file.
        
        Args:
            file_path: Path to the listing file
            
        Returns:
            Listing data or None if loading failed
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            migration_logger.error(f"❌ Failed to load listing {file_path}: {e}")
            return None
    
    def save_listing(self, file_path: Path, listing_data: Dict[str, Any]) -> bool:
        """
        Save a listing to a JSON file.
        
        Args:
            file_path: Path to save the listing
            listing_data: Listing data to save
            
        Returns:
            True if save successful
        """
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(listing_data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            migration_logger.error(f"❌ Failed to save listing {file_path}: {e}")
            return False


def migration_url_to_multi_site(data_dir: Path) -> bool:
    """
    Migration: Convert single 'url' field to multi-site 'urls' structure.
    
    Before: {"data": {"url": "https://cargurus.com/...", ...}}
    After:  {"data": {"urls": {"cargurus": "https://cargurus.com/..."}, "last_updated_site": "cargurus", ...}}
    """
    migrator = DataMigrator(str(data_dir), str(data_dir.parent / "backups"))
    listing_files = migrator.get_listing_files()
    
    if not listing_files:
        migration_logger.info("ℹ️ No listing files found, migration complete")
        return True
    
    migration_logger.info(f"📋 Found {len(listing_files)} listings to migrate")
    
    migrated_count = 0
    error_count = 0
    
    for file_path in listing_files:
        listing = migrator.load_listing(file_path)
        if not listing:
            error_count += 1
            continue
        
        data = listing.get('data', {})
        
        # Check if already migrated (has 'urls' field)
        if 'urls' in data:
            migration_logger.debug(f"⏭️ Skipping already migrated listing: {file_path.name}")
            continue
        
        # Check if has old 'url' field
        if 'url' not in data:
            migration_logger.warning(f"⚠️ Listing {file_path.name} has no URL field, skipping")
            continue
        
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
        
        # Save migrated listing
        if migrator.save_listing(file_path, listing):
            migrated_count += 1
            migration_logger.debug(f"✅ Migrated {file_path.name}: {site} -> {old_url}")
        else:
            error_count += 1
    
    migration_logger.info(f"📊 Migration complete: {migrated_count} migrated, {error_count} errors")
    
    return error_count == 0


def main():
    """Command-line interface for running migrations."""
    if len(sys.argv) < 2:
        print("Usage: python migrations.py <command> [args]")
        print("Commands:")
        print("  backup <name>           - Create a backup")
        print("  list-backups            - List available backups")
        print("  restore <backup_file>   - Restore from backup")
        print("  migrate-urls            - Migrate single URLs to multi-site structure")
        return
    
    command = sys.argv[1]
    migrator = DataMigrator()
    
    if command == "backup":
        if len(sys.argv) < 3:
            print("Error: backup command requires a name")
            return
        name = sys.argv[2]
        backup_path = migrator.create_backup(name)
        print(f"Backup created: {backup_path}")
    
    elif command == "list-backups":
        backups = migrator.list_backups()
        if not backups:
            print("No backups found")
        else:
            print("Available backups:")
            for backup in backups:
                size = backup.stat().st_size / (1024 * 1024)
                mtime = datetime.fromtimestamp(backup.stat().st_mtime)
                print(f"  {backup.name} ({size:.2f} MB, {mtime.strftime('%Y-%m-%d %H:%M:%S')})")
    
    elif command == "restore":
        if len(sys.argv) < 3:
            print("Error: restore command requires a backup filename")
            return
        backup_name = sys.argv[2]
        backup_path = migrator.backup_dir / backup_name
        if migrator.restore_backup(backup_path):
            print("Restore successful")
        else:
            print("Restore failed")
    
    elif command == "migrate-urls":
        success = migrator.run_migration("url_to_multi_site", migration_url_to_multi_site)
        if success:
            print("Migration completed successfully")
        else:
            print("Migration failed")
    
    else:
        print(f"Unknown command: {command}")


if __name__ == "__main__":
    main()