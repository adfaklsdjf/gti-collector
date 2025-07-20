#!/usr/bin/env python3
"""
Individual listing route handler for GTI Listings app.
Handles detailed view of individual car listings.
"""

import logging
from flask import render_template, request, jsonify

logger = logging.getLogger(__name__)

def create_individual_routes(app, store):
    """Register individual listing routes with the Flask app."""
    
    @app.route('/listing/<listing_id>', methods=['GET'])
    def view_listing(listing_id):
        """Display individual listing details."""
        try:
            listing = store.get_listing_by_id(listing_id)
            
            if not listing:
                return "Listing not found", 404
            
            return render_template('listing_detail.html', listing=listing)
        except Exception as e:
            logger.error(f"Error displaying listing {listing_id}: {str(e)}")
            return f"Error loading listing: {str(e)}", 500
    
    @app.route('/listing/<listing_id>/comments', methods=['PUT'])
    def update_comments(listing_id):
        """Update comments for a specific listing."""
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
            
            # Extract comments from request
            comments = data.get('comments', '')
            
            # Update comments using store
            result = store.update_comments(listing_id, comments)
            
            if result['success']:
                logger.info(f"Updated comments for listing {listing_id}")
                return jsonify({
                    'message': result['message'],
                    'success': True
                }), 200
            else:
                logger.warning(f"Failed to update comments for listing {listing_id}: {result['message']}")
                return jsonify({'error': result['message']}), 404
        
        except Exception as e:
            logger.error(f"Error updating comments for listing {listing_id}: {str(e)}")
            return jsonify({'error': 'Internal server error'}), 500
    
    @app.route('/listing/<listing_id>/fields', methods=['PUT'])
    def update_editable_fields(listing_id):
        """Update editable fields for a specific listing."""
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
            
            # Extract editable fields from request
            editable_fields = {}
            if 'performance_package' in data:
                editable_fields['performance_package'] = data['performance_package']
            
            # Update editable fields using store
            result = store.update_editable_fields(listing_id, editable_fields)
            
            if result['success']:
                logger.info(f"Updated editable fields for listing {listing_id}: {editable_fields}")
                return jsonify({
                    'message': result['message'],
                    'success': True
                }), 200
            else:
                logger.warning(f"Failed to update editable fields for listing {listing_id}: {result['message']}")
                return jsonify({'error': result['message']}), 404
        
        except Exception as e:
            logger.error(f"Error updating editable fields for listing {listing_id}: {str(e)}")
            return jsonify({'error': 'Internal server error'}), 500