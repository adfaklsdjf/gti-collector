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

# Setup logging
logger = setup_logging()

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all domains on all routes

# Initialize store
store = Store()

# Register routes
create_listings_routes(app, store)
create_individual_routes(app, store)
create_health_routes(app)

if __name__ == '__main__':
    logger.info("Starting GTI Listings Flask app on port 5000")
    app.run(debug=True, port=5000, host='127.0.0.1')