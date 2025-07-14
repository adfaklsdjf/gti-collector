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
            <div class="listing-title">{{ listing.data.title or (listing.data.year + " Volkswagen GTI") }}</div>
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

@app.route('/listings', methods=['POST'])
def add_listing():
    """Accept new listing data via POST request."""
    try:
        # Get JSON data from request
        data = request.get_json()
        
        if not data:
            logger.error("No JSON data provided in request")
            return jsonify({'error': 'No JSON data provided'}), 400
        
        # Basic field check - core fields are required, title/location are optional
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

@app.route('/health', methods=['GET'])
def health_check():
    """Simple health check endpoint."""
    return jsonify({'status': 'healthy'}), 200

if __name__ == '__main__':
    logger.info("Starting GTI Listings Flask app on port 5000")
    app.run(debug=True, port=5000, host='127.0.0.1')