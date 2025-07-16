#!/usr/bin/env python3
"""
Listings route handlers for GTI Listings app.
Handles main listing page and POST endpoint for new listings.
"""

import json
import logging
from flask import request, jsonify, render_template

logger = logging.getLogger(__name__)

def create_listings_routes(app, store):
    """Register listings routes with the Flask app."""
    
    @app.route('/listings', methods=['POST'])
    def add_listing():
        """Accept new listing data via POST request."""
        try:
            # Check content type first
            if not request.is_json:
                logger.error("Request content type is not JSON")
                return jsonify({'error': 'Content-Type must be application/json'}), 400
            
            # Get JSON data from request
            data = request.get_json()
            
            if data is None:
                logger.error("No JSON data provided in request")
                return jsonify({'error': 'No JSON data provided'}), 400
            
            # Basic field check - core fields are required, title/location are optional
            required_fields = ['url', 'price', 'year', 'mileage', 'distance', 'vin']
            missing_fields = [field for field in required_fields if field not in data]
            
            if missing_fields:
                logger.error(f"Missing required fields: {missing_fields}")
                return jsonify({'error': f'Missing required fields: {missing_fields}'}), 400
            
            # Attempt to store or update the listing
            result = store.add_listing(data)
            
            if result['success']:
                # New listing created
                logger.info(f"Added listing with VIN: {data.get('vin', 'N/A')}")
                return jsonify({
                    'message': 'Listing added successfully', 
                    'id': result['id'],
                    'updated': False
                }), 201
            elif result['updated']:
                # Existing listing updated
                logger.info(f"Updated listing with VIN: {data.get('vin', 'N/A')} - {result['change_summary']}")
                return jsonify({
                    'message': f"Listing updated: {result['change_summary']}", 
                    'id': result['id'],
                    'updated': True,
                    'changes': result['changes']
                }), 200
            else:
                # No changes detected
                logger.info(f"No changes for listing with VIN: {data.get('vin', 'N/A')}")
                return jsonify({
                    'message': 'No changes detected', 
                    'id': result['id'],
                    'updated': False
                }), 200
        
        except Exception as e:
            logger.error(f"Error processing listing: {str(e)}")
            return jsonify({'error': 'Internal server error'}), 500

    @app.route('/', methods=['GET'])
    def index():
        """Display all collected listings."""
        try:
            listings = store.get_all_listings()
            count = len(listings)
            
            # Sort by price (extract numeric value)
            def extract_price(listing):
                try:
                    price_str = listing.get('data', {}).get('price', '$0')
                    return int(price_str.replace('$', '').replace(',', ''))
                except:
                    return 0
            
            listings.sort(key=extract_price)
            
            return render_template('index.html', listings=listings, count=count)
        except Exception as e:
            logger.error(f"Error displaying listings: {str(e)}")
            return f"Error loading listings: {str(e)}", 500