#!/usr/bin/env python3
"""
Individual listing route handler for GTI Listings app.
Handles detailed view of individual car listings.
"""

import logging
from flask import render_template

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