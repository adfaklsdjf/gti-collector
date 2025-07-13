#!/usr/bin/env python3
"""
GTI Listings Flask App
Simple Flask app to collect used car listings via POST endpoint.
"""

import json
import logging
from flask import Flask, request, jsonify
from store import Store

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
store = Store()

@app.route('/listings', methods=['POST'])
def add_listing():
    """Accept new listing data via POST request."""
    try:
        # Get JSON data from request
        data = request.get_json()
        
        if not data:
            logger.error("No JSON data provided in request")
            return jsonify({'error': 'No JSON data provided'}), 400
        
        # Basic field check - all fields are required for now
        required_fields = ['url', 'price', 'year', 'mileage', 'distance', 'vin']
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            logger.error(f"Missing required fields: {missing_fields}")
            return jsonify({'error': f'Missing required fields: {missing_fields}'}), 400
        
        # Attempt to store the listing
        result = store.add_listing(data)
        
        if result['success']:
            logger.info(f"Added listing with VIN: {data.get('vin', 'N/A')}")
            return jsonify({'message': 'Listing added successfully', 'id': result['id']}), 201
        else:
            logger.info(f"Duplicate listing with VIN: {data.get('vin', 'N/A')}")
            return jsonify({'message': 'Listing already exists (duplicate VIN)', 'id': result['id']}), 200
    
    except Exception as e:
        logger.error(f"Error processing listing: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Simple health check endpoint."""
    return jsonify({'status': 'healthy'}), 200

if __name__ == '__main__':
    logger.info("Starting GTI Listings Flask app on port 5000")
    app.run(debug=True, port=5000, host='127.0.0.1')