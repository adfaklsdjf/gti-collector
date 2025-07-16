#!/usr/bin/env python3
"""
GTI Listings Flask App
Simple Flask app to collect used car listings via POST endpoint.
"""

import json
import logging
from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
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
CORS(app)  # Enable CORS for all domains on all routes
store = Store()

# Simple HTML template for listings page
LISTINGS_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GTI Listings</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .header {
            text-align: center;
            margin-bottom: 30px;
            padding: 20px;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .header h1 {
            color: #1f2937;
            margin: 0;
        }
        .stats {
            color: #6b7280;
            margin-top: 5px;
        }
        .listings-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
            gap: 20px;
            max-width: 1200px;
            margin: 0 auto;
        }
        .listing-card {
            background: white;
            border-radius: 8px;
            padding: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            border-left: 4px solid #3b82f6;
        }
        .listing-price {
            font-size: 24px;
            font-weight: bold;
            color: #059669;
            margin-bottom: 10px;
        }
        .listing-title {
            font-size: 18px;
            font-weight: 600;
            color: #1f2937;
            margin-bottom: 15px;
        }
        .listing-title a:hover {
            text-decoration: underline;
        }
        .listing-details {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;
            margin-bottom: 15px;
        }
        .detail-item {
            display: flex;
            flex-direction: column;
        }
        .detail-label {
            font-size: 12px;
            color: #6b7280;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .detail-value {
            font-size: 14px;
            color: #374151;
            font-weight: 500;
        }
        .vin {
            font-family: monospace;
            background: #f3f4f6;
            padding: 5px 8px;
            border-radius: 4px;
            font-size: 12px;
            color: #374151;
            margin-top: 10px;
        }
        .listing-url {
            margin-top: 15px;
        }
        .listing-url a {
            color: #3b82f6;
            text-decoration: none;
            font-size: 14px;
        }
        .listing-url a:hover {
            text-decoration: underline;
        }
        .listing-location {
            font-size: 14px;
            color: #6b7280;
            margin-bottom: 15px;
            font-weight: 500;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🚗 GTI Listings</h1>
        <div class="stats">{{ count }} listings collected • Sorted by price</div>
    </div>
    
    {% if listings %}
    <div class="listings-grid">
        {% for listing in listings %}
        <div class="listing-card">
            <div class="listing-price">{{ listing.data.price }}</div>
            <div class="listing-title">
                <a href="/listing/{{ listing.id }}" style="color: inherit; text-decoration: none;">{{ listing.data.title or (listing.data.year + " Volkswagen GTI") }}</a>
            </div>
            {% if listing.data.location %}
            <div class="listing-location">📍 {{ listing.data.location }}</div>
            {% endif %}
            
            <div class="listing-details">
                <div class="detail-item">
                    <span class="detail-label">Year</span>
                    <span class="detail-value">{{ listing.data.year }}</span>
                </div>
                <div class="detail-item">
                    <span class="detail-label">Mileage</span>
                    <span class="detail-value">{{ listing.data.mileage }}</span>
                </div>
                <div class="detail-item">
                    <span class="detail-label">Distance</span>
                    <span class="detail-value">{{ listing.data.distance }}</span>
                </div>
                <div class="detail-item">
                    <span class="detail-label">ID</span>
                    <span class="detail-value">{{ listing.id[:8] }}...</span>
                </div>
            </div>
            
            <div class="vin">VIN: {{ listing.data.vin }}</div>
            
            <div class="listing-url">
                <a href="{{ listing.data.url }}" target="_blank">View Original Listing →</a>
                <a href="/listing/{{ listing.id }}" style="display: inline-block; margin-left: 15px; color: #059669; text-decoration: none; font-weight: 500;">View Details →</a>
            </div>
        </div>
        {% endfor %}
    </div>
    {% else %}
    <div style="text-align: center; padding: 40px;">
        <h2>No listings yet</h2>
        <p>Use the browser extension to start collecting GTI listings!</p>
    </div>
    {% endif %}
</body>
</html>
'''

# Detailed listing template
LISTING_DETAIL_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ listing.data.title or (listing.data.year + " Volkswagen GTI") }} - GTI Listings</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 0;
            background-color: #f5f5f5;
            line-height: 1.6;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }
        .header {
            background: white;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .breadcrumb {
            color: #6b7280;
            margin-bottom: 15px;
        }
        .breadcrumb a {
            color: #3b82f6;
            text-decoration: none;
        }
        .breadcrumb a:hover {
            text-decoration: underline;
        }
        .listing-title {
            font-size: 28px;
            font-weight: bold;
            color: #1f2937;
            margin: 0 0 10px 0;
        }
        .listing-price {
            font-size: 32px;
            font-weight: bold;
            color: #059669;
            margin: 0;
        }
        .content-section {
            background: white;
            border-radius: 8px;
            padding: 25px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .section-title {
            font-size: 20px;
            font-weight: 600;
            color: #1f2937;
            margin: 0 0 20px 0;
            border-bottom: 2px solid #e5e7eb;
            padding-bottom: 10px;
        }
        .details-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
        }
        .detail-item {
            display: flex;
            flex-direction: column;
        }
        .detail-label {
            font-size: 12px;
            color: #6b7280;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 5px;
        }
        .detail-value {
            font-size: 16px;
            color: #374151;
            font-weight: 500;
        }
        .vin-section {
            background: #f9fafb;
            border: 1px solid #e5e7eb;
            border-radius: 6px;
            padding: 15px;
            margin-top: 15px;
        }
        .vin-label {
            font-size: 12px;
            color: #6b7280;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 5px;
        }
        .vin-value {
            font-family: 'Monaco', 'Menlo', monospace;
            font-size: 14px;
            color: #1f2937;
            font-weight: 600;
            letter-spacing: 1px;
        }
        .location-badge {
            display: inline-flex;
            align-items: center;
            background: #eff6ff;
            color: #1e40af;
            padding: 8px 12px;
            border-radius: 20px;
            font-size: 14px;
            font-weight: 500;
            margin-top: 10px;
        }
        .action-buttons {
            display: flex;
            gap: 15px;
            margin-top: 20px;
        }
        .btn {
            padding: 12px 24px;
            border: none;
            border-radius: 6px;
            font-size: 14px;
            font-weight: 500;
            cursor: pointer;
            text-decoration: none;
            display: inline-block;
            text-align: center;
            transition: all 0.2s;
        }
        .btn-primary {
            background: #3b82f6;
            color: white;
        }
        .btn-primary:hover {
            background: #2563eb;
        }
        .btn-secondary {
            background: #6b7280;
            color: white;
        }
        .btn-secondary:hover {
            background: #4b5563;
        }
        .metadata {
            color: #6b7280;
            font-size: 13px;
            margin-top: 15px;
            padding-top: 15px;
            border-top: 1px solid #e5e7eb;
        }
        .edit-section {
            background: #fef3c7;
            border: 1px solid #fbbf24;
            border-radius: 6px;
            padding: 15px;
            margin-top: 20px;
        }
        .edit-section h3 {
            color: #92400e;
            margin: 0 0 10px 0;
            font-size: 16px;
        }
        .edit-section p {
            color: #78350f;
            margin: 0;
            font-size: 14px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="breadcrumb">
                <a href="/">← Back to All Listings</a>
            </div>
            <h1 class="listing-title">{{ listing.data.title or (listing.data.year + " Volkswagen GTI") }}</h1>
            <div class="listing-price">{{ listing.data.price }}</div>
            {% if listing.data.location %}
            <div class="location-badge">
                📍 {{ listing.data.location }}
            </div>
            {% endif %}
        </div>

        <div class="content-section">
            <h2 class="section-title">Vehicle Details</h2>
            <div class="details-grid">
                <div class="detail-item">
                    <span class="detail-label">Year</span>
                    <span class="detail-value">{{ listing.data.year }}</span>
                </div>
                <div class="detail-item">
                    <span class="detail-label">Mileage</span>
                    <span class="detail-value">{{ listing.data.mileage }}</span>
                </div>
                <div class="detail-item">
                    <span class="detail-label">Distance</span>
                    <span class="detail-value">{{ listing.data.distance }}</span>
                </div>
                <div class="detail-item">
                    <span class="detail-label">Listing ID</span>
                    <span class="detail-value">{{ listing.id[:8] }}...</span>
                </div>
            </div>
            
            <div class="vin-section">
                <div class="vin-label">Vehicle Identification Number</div>
                <div class="vin-value">{{ listing.data.vin }}</div>
            </div>
            
            <div class="action-buttons">
                <a href="{{ listing.data.url }}" target="_blank" class="btn btn-primary">
                    View Original Listing →
                </a>
                <a href="/" class="btn btn-secondary">
                    Back to All Listings
                </a>
            </div>
            
            <div class="metadata">
                <strong>Internal ID:</strong> {{ listing.id }}<br>
                <strong>Data stored:</strong> {{ listing.data.keys() | list | length }} fields
            </div>
        </div>

        <div class="content-section">
            <div class="edit-section">
                <h3>🚧 Future Enhancement Area</h3>
                <p>This page will soon support editable fields like personal notes, favorites, custom tags, and other user-specific annotations.</p>
            </div>
        </div>
    </div>
</body>
</html>
'''

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
        
        return render_template_string(LISTINGS_TEMPLATE, listings=listings, count=count)
    except Exception as e:
        logger.error(f"Error displaying listings: {str(e)}")
        return f"Error loading listings: {str(e)}", 500

@app.route('/listing/<listing_id>', methods=['GET'])
def view_listing(listing_id):
    """Display individual listing details."""
    try:
        listing = store.get_listing_by_id(listing_id)
        
        if not listing:
            return "Listing not found", 404
        
        return render_template_string(LISTING_DETAIL_TEMPLATE, listing=listing)
    except Exception as e:
        logger.error(f"Error displaying listing {listing_id}: {str(e)}")
        return f"Error loading listing: {str(e)}", 500

@app.route('/health', methods=['GET'])
def health_check():
    """Simple health check endpoint."""
    return jsonify({'status': 'healthy'}), 200

if __name__ == '__main__':
    logger.info("Starting GTI Listings Flask app on port 5000")
    app.run(debug=True, port=5000, host='127.0.0.1')