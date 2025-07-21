#!/usr/bin/env python3
"""
Configuration routes for GTI Listings app.
"""

from flask import render_template, request, jsonify, redirect, url_for
import logging

logger = logging.getLogger(__name__)

def create_config_routes(app, config_manager):
    """Create configuration-related routes."""
    
    @app.route('/config', methods=['GET'])
    def config_page():
        """Display configuration page."""
        try:
            config = config_manager.get_all()
            return render_template('config.html', config=config)
        except Exception as e:
            logger.error(f"Error loading config page: {e}")
            return jsonify({"error": str(e)}), 500
    
    @app.route('/config', methods=['POST'])
    def save_config():
        """Save configuration settings."""
        try:
            # Get form data
            sample_setting = request.form.get('sample_setting', '').strip()
            
            # Validate the input (basic validation for now)
            if len(sample_setting) > 1000:  # Reasonable limit
                return jsonify({"error": "Setting value too long (max 1000 characters)"}), 400
            
            # Update configuration
            config_manager.set('sample_setting', sample_setting)
            
            logger.info(f"Configuration updated: sample_setting = '{sample_setting}'")
            
            # Return success response
            return redirect(url_for('config_page'))
            
        except Exception as e:
            logger.error(f"Error saving config: {e}")
            return jsonify({"error": str(e)}), 500