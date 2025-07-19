#!/usr/bin/env python3
"""
GTI Listings Flask App
Simple Flask app to collect used car listings via POST endpoint.
"""

from flask import Flask
from flask_cors import CORS
from store import Store
from config import setup_logging
from routes.listings import create_listings_routes
from routes.individual import create_individual_routes
from routes.health import create_health_routes
from schema_migrations import SchemaMigrator

# Setup logging
logger = setup_logging()

def run_preflight_checks():
    """Run pre-flight checks including schema migrations."""
    logger.info("🔍 Running pre-flight checks...")
    
    # Check and run schema migrations if needed
    migrator = SchemaMigrator()
    migration_needed, current_version, target_version = migrator.check_migration_needed()
    
    if migration_needed:
        logger.info(f"📋 Schema migration needed: v{current_version} -> v{target_version}")
        success = migrator.run_preflight_migration()
        if not success:
            logger.error("❌ Schema migration failed - aborting startup")
            raise RuntimeError("Schema migration failed")
        logger.info("✅ Schema migration completed successfully")
    else:
        logger.info(f"ℹ️ Schema is current (v{current_version})")
    
    logger.info("✅ Pre-flight checks completed")

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all domains on all routes

# Run pre-flight checks
run_preflight_checks()

# Initialize store
store = Store()

# Register routes
create_listings_routes(app, store)
create_individual_routes(app, store)
create_health_routes(app)

if __name__ == '__main__':
    logger.info("Starting GTI Listings Flask app on port 5000")
    app.run(debug=True, port=5000, host='127.0.0.1')