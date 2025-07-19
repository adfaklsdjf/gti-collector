#!/usr/bin/env python3
"""
Schema-versioned migration framework for GTI Listings app.
Provides repeatable, safe data structure evolution with per-file version tracking.
"""

import json
import logging
import tarfile
import shutil
import sys
import os
import importlib.util
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import re

# Set up migration-specific logging
migration_logger = logging.getLogger('schema_migrations')
migration_handler = logging.FileHandler('migrations.log')
migration_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
migration_handler.setFormatter(migration_formatter)
migration_logger.addHandler(migration_handler)
migration_logger.setLevel(logging.INFO)

class MigrationError(Exception):
    """Custom exception for migration errors."""
    pass

class SchemaMigrator:
    """
    Schema-versioned migration system with per-file version tracking.
    """
    
    def __init__(self, data_dir: str = "data", backup_dir: str = "backups", migrations_dir: str = "migrations"):
        self.data_dir = Path(data_dir)
        self.backup_dir = Path(backup_dir)
        self.migrations_dir = Path(migrations_dir)
        self.backup_dir.mkdir(exist_ok=True)
        
        migration_logger.info(f"🚀 SchemaMigrator initialized - data: {self.data_dir}, backups: {self.backup_dir}, migrations: {self.migrations_dir}")
    
    def get_available_migrations(self) -> List[int]:
        """
        Get list of available migration versions from migrations directory.
        
        Returns:
            List[int]: Sorted list of available migration version numbers
        """
        if not self.migrations_dir.exists():
            return []
            
        migration_files = list(self.migrations_dir.glob("v*.py"))
        versions = []
        
        for file_path in migration_files:
            # Extract version number from filename like v002_description.py
            match = re.match(r'v(\d+)_.*\.py$', file_path.name)
            if match:
                versions.append(int(match.group(1)))
        
        return sorted(versions)
    
    def get_current_schema_version(self) -> int:
        """
        Get the current expected schema version (highest available migration).
        
        Returns:
            int: Current schema version
        """
        available = self.get_available_migrations()
        return max(available) if available else 0
    
    def get_file_schema_version(self, file_path: Path) -> int:
        """
        Get the schema version of a specific file.
        
        Args:
            file_path: Path to the file to check
            
        Returns:
            int: Schema version of the file (0 if no version found)
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data.get('schema_version', 0)
        except Exception as e:
            migration_logger.warning(f"Could not read schema version from {file_path}: {e}")
            return 0
    
    def get_pending_migrations(self, current_version: int) -> List[int]:
        """
        Get list of migrations that need to be applied to reach current schema.
        
        Args:
            current_version: Current version of the file
            
        Returns:
            List[int]: Sorted list of migration versions to apply
        """
        available = self.get_available_migrations()
        target_version = self.get_current_schema_version()
        
        return [v for v in available if current_version < v <= target_version]
    
    def load_migration(self, version: int):
        """
        Dynamically load a migration module.
        
        Args:
            version: Migration version to load
            
        Returns:
            Migration module with migrate() function
        """
        # Find migration file
        pattern = f"v{version:03d}_*.py"
        migration_files = list(self.migrations_dir.glob(pattern))
        
        if not migration_files:
            raise MigrationError(f"Migration v{version:03d} not found")
        
        if len(migration_files) > 1:
            raise MigrationError(f"Multiple migration files found for v{version:03d}")
        
        migration_file = migration_files[0]
        
        # Load the module
        spec = importlib.util.spec_from_file_location(f"migration_v{version:03d}", migration_file)
        if spec is None or spec.loader is None:
            raise MigrationError(f"Could not load migration {migration_file}")
        
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        if not hasattr(module, 'migrate'):
            raise MigrationError(f"Migration {migration_file} missing migrate() function")
        
        return module
    
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
    
    def migrate_file(self, file_path: Path, target_version: int) -> bool:
        """
        Migrate a single file to the target schema version.
        
        Args:
            file_path: Path to file to migrate
            target_version: Target schema version
            
        Returns:
            bool: True if migration successful
        """
        current_version = self.get_file_schema_version(file_path)
        pending = self.get_pending_migrations(current_version)
        
        if not pending:
            migration_logger.debug(f"📋 {file_path.name} already at version {current_version}")
            return True
        
        migration_logger.info(f"🔧 Migrating {file_path.name} from v{current_version} to v{target_version}")
        
        try:
            # Load current file content
            with open(file_path, 'r', encoding='utf-8') as f:
                file_data = json.load(f)
            
            # Apply each pending migration
            for version in pending:
                migration_logger.debug(f"⚡ Applying migration v{version:03d} to {file_path.name}")
                
                migration_module = self.load_migration(version)
                file_data = migration_module.migrate(file_data)
                
                # Ensure schema version is updated
                file_data['schema_version'] = version
            
            # Save migrated file
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(file_data, f, indent=2, ensure_ascii=False)
            
            migration_logger.info(f"✅ {file_path.name} migrated successfully to v{target_version}")
            return True
            
        except Exception as e:
            migration_logger.error(f"❌ Failed to migrate {file_path.name}: {e}")
            return False
    
    def get_index_file_path(self) -> Path:
        """Get path to the VIN index file."""
        return self.data_dir / "indices" / "vin_to_id.json"
    
    def get_listing_files(self) -> List[Path]:
        """Get all listing JSON files in the data directory."""
        if not self.data_dir.exists():
            return []
        return [f for f in self.data_dir.glob("*.json") if f.is_file()]
    
    def check_migration_needed(self) -> Tuple[bool, int, int]:
        """
        Check if migration is needed by examining the index file.
        
        Returns:
            Tuple[bool, int, int]: (migration_needed, current_version, target_version)
        """
        index_path = self.get_index_file_path()
        current_version = self.get_file_schema_version(index_path) if index_path.exists() else 0
        target_version = self.get_current_schema_version()
        
        migration_needed = current_version < target_version
        
        return migration_needed, current_version, target_version
    
    def run_preflight_migration(self) -> bool:
        """
        Run pre-flight migration check and migrate all files if needed.
        
        Returns:
            bool: True if migration successful or not needed
        """
        migration_needed, current_version, target_version = self.check_migration_needed()
        
        if not migration_needed:
            migration_logger.info(f"ℹ️ Schema is current (v{current_version}), no migration needed")
            return True
        
        migration_logger.info(f"🔧 Starting preflight migration from v{current_version} to v{target_version}")
        
        # Create backup before migration
        backup_path = self.create_backup(f"preflight_v{current_version}_to_v{target_version}")
        
        try:
            # Migrate index first
            index_path = self.get_index_file_path()
            if index_path.exists():
                if not self.migrate_file(index_path, target_version):
                    raise MigrationError("Index migration failed")
            
            # Migrate all listing files
            listing_files = self.get_listing_files()
            failed_files = []
            
            for file_path in listing_files:
                if not self.migrate_file(file_path, target_version):
                    failed_files.append(file_path.name)
            
            if failed_files:
                raise MigrationError(f"Migration failed for files: {failed_files}")
            
            migration_logger.info(f"✅ Preflight migration completed successfully")
            return True
            
        except Exception as e:
            migration_logger.error(f"❌ Preflight migration failed: {e}")
            return False
    
    def migrate_file_jit(self, file_path: Path) -> bool:
        """
        Perform just-in-time migration of a single file with warning.
        
        Args:
            file_path: Path to file that needs migration
            
        Returns:
            bool: True if migration successful
        """
        current_version = self.get_file_schema_version(file_path)
        target_version = self.get_current_schema_version()
        
        if current_version >= target_version:
            return True
        
        migration_logger.warning(f"⚠️ Just-in-time migration required for {file_path.name} (v{current_version} -> v{target_version})")
        
        return self.migrate_file(file_path, target_version)


def main():
    """Command-line interface for running schema migrations."""
    if len(sys.argv) < 2:
        print("Usage: python schema_migrations.py <command> [args]")
        print("Commands:")
        print("  preflight               - Run preflight migration check")
        print("  check                   - Check if migration is needed")
        print("  list-migrations         - List available migrations")
        print("  backup <name>           - Create a backup")
        return
    
    command = sys.argv[1]
    migrator = SchemaMigrator()
    
    if command == "preflight":
        success = migrator.run_preflight_migration()
        print("Preflight migration completed successfully" if success else "Preflight migration failed")
    
    elif command == "check":
        needed, current, target = migrator.check_migration_needed()
        if needed:
            print(f"Migration needed: v{current} -> v{target}")
        else:
            print(f"Schema is current: v{current}")
    
    elif command == "list-migrations":
        migrations = migrator.get_available_migrations()
        if migrations:
            print("Available migrations:")
            for version in migrations:
                print(f"  v{version:03d}")
        else:
            print("No migrations found")
    
    elif command == "backup":
        if len(sys.argv) < 3:
            print("Error: backup command requires a name")
            return
        name = sys.argv[2]
        backup_path = migrator.create_backup(name)
        print(f"Backup created: {backup_path}")
    
    else:
        print(f"Unknown command: {command}")


if __name__ == "__main__":
    main()