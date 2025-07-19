#!/usr/bin/env python3
"""
Listings route handlers for GTI Listings app.
Handles main listing page and POST endpoint for new listings.
"""

import json
import logging
import csv
import io
import re
from flask import request, jsonify, render_template, make_response
from desirability import add_desirability_scores
from site_mappings import process_site_data, merge_site_data, check_desirability_completeness

logger = logging.getLogger(__name__)

def extract_distance_from_location(location):
    """
    Extract distance from location text like "San Francisco, CA (1,888 mi away)".
    
    Returns:
        str: Numeric distance string like "1888" or None if not found
    """
    if not location:
        return None
    
    # Look for pattern like "(123 mi away)" or "(1,234 mi away)" with flexible spacing
    distance_pattern = r'\(\s*(\d+(?:,\d+)?)\s*mi\s+away\s*\)'
    match = re.search(distance_pattern, location, re.IGNORECASE)
    
    if match:
        # Extract just the number and remove commas
        number_part = match.group(1).replace(',', '')
        return number_part
    
    return None

def process_listing_data(data):
    """
    Process incoming listing data to extract distance from location if needed.
    
    Args:
        data: Raw listing data dict
        
    Returns:
        dict: Processed listing data with distance field populated if possible
    """
    processed_data = data.copy()
    
    # If distance is not provided, empty, or "Unknown", try to extract it from location
    distance_value = processed_data.get('distance')
    should_extract_distance = (
        'distance' not in processed_data or 
        not distance_value or 
        distance_value.lower() == 'unknown'
    )
    
    if should_extract_distance:
        location = processed_data.get('location')
        if location:
            extracted_distance = extract_distance_from_location(location)
            if extracted_distance:
                processed_data['distance'] = extracted_distance
                logger.info(f"Extracted distance '{extracted_distance}' from location: {location}")
    
    return processed_data

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
            
            # Log received data for debugging
            site_name = data.get('site', 'unknown')
            logger.info(f"📥 Received listing data from {site_name}: {data}")
            
            # Process site-specific data into internal format
            processed_data = process_site_data(data)
            
            # Apply any needed derivations (e.g., distance from location)
            processed_data = process_listing_data(processed_data)
            
            # Basic field check - core fields are required for any listing
            required_fields = ['price', 'year', 'mileage', 'vin']
            missing_fields = [field for field in required_fields if field not in processed_data]
            
            if missing_fields:
                logger.error(f"Missing required fields: {missing_fields}")
                return jsonify({'error': f'Missing required fields: {missing_fields}'}), 400
            
            # Attempt to store or update the listing
            result = store.add_listing(processed_data)
            
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
            
            # Calculate desirability scores for all listings
            if listings:
                # Check for listings with missing desirability fields
                for listing in listings:
                    is_complete, missing_fields = check_desirability_completeness(listing.get('data', {}))
                    if not is_complete:
                        logger.warning(f"⚠️ Listing {listing.get('id', 'unknown')} missing desirability fields: {missing_fields}")
                        # Add warning flag for UI display
                        listing['desirability_warning'] = f"Missing: {', '.join(missing_fields)}"
                
                listings = add_desirability_scores(listings)
            
            # Get sort parameter from query string
            sort_by = request.args.get('sort', 'price')
            
            if sort_by == 'desirability':
                # Sort by desirability score (highest first)
                listings.sort(key=lambda x: x.get('desirability_score', 0), reverse=True)
                sort_description = "Sorted by desirability"
            else:
                # Default: sort by price (lowest first)
                def extract_price(listing):
                    try:
                        price_str = listing.get('data', {}).get('price', '$0')
                        return int(price_str.replace('$', '').replace(',', ''))
                    except:
                        return 0
                
                listings.sort(key=extract_price)
                sort_description = "Sorted by price"
            
            return render_template('index.html', 
                                 listings=listings, 
                                 count=count, 
                                 sort_by=sort_by,
                                 sort_description=sort_description)
        except Exception as e:
            logger.error(f"Error displaying listings: {str(e)}")
            return f"Error loading listings: {str(e)}", 500

    @app.route('/listings/<listing_id>', methods=['DELETE'])
    def delete_listing(listing_id):
        """Delete a listing by moving it to deleted folder and removing from index."""
        try:
            result = store.delete_listing(listing_id)
            
            if result['success']:
                logger.info(f"Successfully deleted listing {listing_id}")
                return jsonify({
                    'message': result['message'],
                    'id': listing_id,
                    'vin': result.get('vin')
                }), 200
            else:
                logger.warning(f"Failed to delete listing {listing_id}: {result['message']}")
                return jsonify({'error': result['message']}), 404
        
        except Exception as e:
            logger.error(f"Error deleting listing {listing_id}: {str(e)}")
            return jsonify({'error': 'Internal server error'}), 500

    @app.route('/listings/export.csv', methods=['GET'])
    def export_csv():
        """Export all listings to CSV with specified columns: link, price, year, mileage, vin."""
        try:
            listings = store.get_all_listings()
            
            # Create CSV in memory
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write header row
            writer.writerow(['link', 'price', 'year', 'mileage', 'vin'])
            
            # Write data rows
            for listing in listings:
                data = listing.get('data', {})
                writer.writerow([
                    data.get('url', ''),
                    data.get('price', ''),
                    data.get('year', ''),
                    data.get('mileage', ''),
                    data.get('vin', '')
                ])
            
            # Create response
            output.seek(0)
            csv_data = output.getvalue()
            output.close()
            
            response = make_response(csv_data)
            response.headers['Content-Type'] = 'text/csv'
            response.headers['Content-Disposition'] = 'attachment; filename=gti-listings-export.csv'
            
            logger.info(f"Exported {len(listings)} listings to CSV")
            return response
            
        except Exception as e:
            logger.error(f"Error exporting CSV: {str(e)}")
            return f"Error exporting CSV: {str(e)}", 500