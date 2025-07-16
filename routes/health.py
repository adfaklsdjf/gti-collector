#!/usr/bin/env python3
"""
Health check route handler for GTI Listings app.
Provides simple health check endpoint.
"""

from flask import jsonify

def create_health_routes(app):
    """Register health check routes with the Flask app."""
    
    @app.route('/health', methods=['GET'])
    def health_check():
        """Simple health check endpoint."""
        return jsonify({'status': 'healthy'}), 200