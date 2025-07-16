#!/usr/bin/env python3
"""
Integration tests for Flask app endpoints.
Tests API functionality, error handling, and response formats.
"""

import pytest
import tempfile
import shutil
import json


@pytest.fixture
def client():
    """Create a test client for the Flask app."""
    from flask import Flask
    from flask_cors import CORS
    from store import Store
    from config import setup_logging
    from routes.listings import create_listings_routes
    from routes.individual import create_individual_routes
    from routes.health import create_health_routes
    
    # Create a test Flask app with isolated store
    test_app = Flask(__name__)
    test_app.config['TESTING'] = True
    CORS(test_app)
    
    # Use temporary directory for test data
    temp_dir = tempfile.mkdtemp()
    test_store = Store(data_dir=temp_dir)
    
    # Register routes with the test store
    create_listings_routes(test_app, test_store)
    create_individual_routes(test_app, test_store)
    create_health_routes(test_app)
    
    with test_app.test_client() as client:
        yield client
    
    # Cleanup
    shutil.rmtree(temp_dir)


@pytest.fixture
def sample_listing_payload():
    """Sample POST payload for testing."""
    return {
        'url': 'https://test.com/listing/123',
        'price': '$25,000',
        'year': '2019',
        'mileage': '45000',
        'distance': '15 mi away',
        'vin': 'WVWZZZ1JZ1W123456',
        'title': '2019 Volkswagen Golf GTI 2.0T SE 4-Door FWD',
        'location': 'Cleveland, OH (15 mi away)'
    }


class TestHealthEndpoint:
    """Test health check endpoint."""
    
    def test_health_check_success(self, client):
        """Test health endpoint returns healthy status."""
        response = client.get('/health')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['status'] == 'healthy'


class TestListingsPostEndpoint:
    """Test POST /listings endpoint."""
    
    def test_add_listing_success(self, client, sample_listing_payload):
        """Test successfully adding a new listing."""
        response = client.post('/listings',
                             data=json.dumps(sample_listing_payload),
                             content_type='application/json')
        
        assert response.status_code == 201
        
        data = json.loads(response.data)
        assert data['message'] == 'Listing added successfully'
        assert 'id' in data
        assert len(data['id']) == 36  # UUID length
    
    def test_add_duplicate_listing_no_changes(self, client, sample_listing_payload):
        """Test adding duplicate VIN with no changes."""
        # Add first listing
        response1 = client.post('/listings',
                               data=json.dumps(sample_listing_payload),
                               content_type='application/json')
        assert response1.status_code == 201
        first_id = json.loads(response1.data)['id']
        
        # Add duplicate with no changes
        response2 = client.post('/listings',
                               data=json.dumps(sample_listing_payload),
                               content_type='application/json')
        assert response2.status_code == 200
        
        data = json.loads(response2.data)
        assert data['message'] == 'No changes detected'
        assert data['id'] == first_id
        assert data['updated'] is False
    
    def test_add_duplicate_listing_with_updates(self, client, sample_listing_payload):
        """Test adding duplicate VIN with changes triggers update."""
        # Add first listing
        response1 = client.post('/listings',
                               data=json.dumps(sample_listing_payload),
                               content_type='application/json')
        assert response1.status_code == 201
        first_id = json.loads(response1.data)['id']
        
        # Add duplicate with changes
        updated_payload = sample_listing_payload.copy()
        updated_payload['price'] = '$24,000'
        updated_payload['title'] = 'Updated Title'
        
        response2 = client.post('/listings',
                               data=json.dumps(updated_payload),
                               content_type='application/json')
        assert response2.status_code == 200
        
        data = json.loads(response2.data)
        assert 'Listing updated:' in data['message']
        assert data['id'] == first_id
        assert data['updated'] is True
        assert 'changes' in data
        assert 'price' in data['changes']
        assert 'title' in data['changes']
    
    def test_missing_required_fields(self, client):
        """Test missing required fields returns error."""
        incomplete_payload = {
            'url': 'https://test.com/listing/123',
            'price': '$25,000'
            # Missing year, mileage, distance, vin
        }
        
        response = client.post('/listings',
                             data=json.dumps(incomplete_payload),
                             content_type='application/json')
        
        assert response.status_code == 400
        
        data = json.loads(response.data)
        assert 'Missing required fields' in data['error']
        assert 'year' in data['error']
        assert 'vin' in data['error']
    
    def test_no_json_data(self, client):
        """Test request without JSON data returns error."""
        response = client.post('/listings',
                             data='not json',
                             content_type='text/plain')
        
        assert response.status_code == 400
        
        data = json.loads(response.data)
        assert data['error'] == 'Content-Type must be application/json'
    
    def test_empty_json_data(self, client):
        """Test request with empty JSON returns error."""
        response = client.post('/listings',
                             data='{}',
                             content_type='application/json')
        
        assert response.status_code == 400
        
        data = json.loads(response.data)
        assert 'Missing required fields' in data['error']
    
    def test_optional_fields_accepted(self, client):
        """Test that optional fields (title, location) are stored."""
        payload = {
            'url': 'https://test.com/listing/123',
            'price': '$25,000',
            'year': '2019',
            'mileage': '45000',
            'distance': '15 mi away',
            'vin': 'WVWZZZ1JZ1W123456'
            # No title or location
        }
        
        response = client.post('/listings',
                             data=json.dumps(payload),
                             content_type='application/json')
        
        assert response.status_code == 201


class TestIndexEndpoint:
    """Test GET / (index) endpoint."""
    
    def test_index_empty_state(self, client):
        """Test index page with no listings."""
        response = client.get('/')
        assert response.status_code == 200
        assert b'No listings yet' in response.data
        assert b'Use the browser extension' in response.data
    
    def test_index_with_listings(self, client, sample_listing_payload):
        """Test index page displays listings."""
        # Add a listing first
        client.post('/listings',
                   data=json.dumps(sample_listing_payload),
                   content_type='application/json')
        
        response = client.get('/')
        assert response.status_code == 200
        
        # Check for listing data in HTML
        assert b'GTI Listings' in response.data
        assert b'$25,000' in response.data
        assert b'2019' in response.data
        assert sample_listing_payload['vin'].encode() in response.data
        
        # Check for title and location if present
        if 'title' in sample_listing_payload:
            assert sample_listing_payload['title'].encode() in response.data
        if 'location' in sample_listing_payload:
            assert sample_listing_payload['location'].encode() in response.data
    
    def test_index_listing_count(self, client, sample_listing_payload):
        """Test that listing count is displayed correctly."""
        response = client.get('/')
        assert b'0 listings collected' in response.data
        
        # Add one listing
        client.post('/listings',
                   data=json.dumps(sample_listing_payload),
                   content_type='application/json')
        
        response = client.get('/')
        assert b'1 listings collected' in response.data
        
        # Add another with different VIN
        second_listing = sample_listing_payload.copy()
        second_listing['vin'] = 'WVWZZZ1JZ1W654321'
        client.post('/listings',
                   data=json.dumps(second_listing),
                   content_type='application/json')
        
        response = client.get('/')
        assert b'2 listings collected' in response.data


class TestIndividualListingPage:
    """Test individual listing detail page."""
    
    def test_view_listing_success(self, client, sample_listing_payload):
        """Test viewing individual listing page."""
        # First add a listing
        response = client.post('/listings',
                             data=json.dumps(sample_listing_payload),
                             content_type='application/json')
        assert response.status_code == 201
        
        listing_id = json.loads(response.data)['id']
        
        # Then view the individual listing page
        response = client.get(f'/listing/{listing_id}')
        assert response.status_code == 200
        
        # Check that listing details are displayed
        assert sample_listing_payload['price'].encode() in response.data
        assert sample_listing_payload['year'].encode() in response.data
        assert sample_listing_payload['vin'].encode() in response.data
        assert sample_listing_payload['title'].encode() in response.data
        assert sample_listing_payload['location'].encode() in response.data
        
        # Check for page-specific elements
        assert b'Vehicle Details' in response.data
        assert b'Back to All Listings' in response.data
        assert b'View Original Listing' in response.data
        assert b'Vehicle Identification Number' in response.data
    
    def test_view_listing_not_found(self, client):
        """Test viewing non-existent listing returns 404."""
        fake_id = 'nonexistent-listing-id'
        response = client.get(f'/listing/{fake_id}')
        assert response.status_code == 404
        assert b'Listing not found' in response.data
    
    def test_listing_links_from_index(self, client, sample_listing_payload):
        """Test that index page contains links to individual listings."""
        # Add a listing
        response = client.post('/listings',
                             data=json.dumps(sample_listing_payload),
                             content_type='application/json')
        assert response.status_code == 201
        
        listing_id = json.loads(response.data)['id']
        
        # Check index page contains link to individual listing
        response = client.get('/')
        assert response.status_code == 200
        
        expected_link = f'/listing/{listing_id}'.encode()
        assert expected_link in response.data
        
        # Check both the title link and the "View Details" link
        assert b'View Details' in response.data


class TestCorsHeaders:
    """Test CORS headers are present."""
    
    def test_cors_headers_present(self, client, sample_listing_payload):
        """Test that CORS headers are included in responses."""
        response = client.post('/listings',
                             data=json.dumps(sample_listing_payload),
                             content_type='application/json')
        
        # Flask-CORS should add these headers
        assert 'Access-Control-Allow-Origin' in response.headers
    
    def test_options_request(self, client):
        """Test OPTIONS preflight request for CORS."""
        response = client.options('/listings')
        assert response.status_code == 200


class TestDeleteListing:
    """Test DELETE /listings/<id> endpoint."""
    
    def test_delete_listing_success(self, client, sample_listing_payload):
        """Test successfully deleting a listing."""
        # First add a listing
        response = client.post('/listings',
                             data=json.dumps(sample_listing_payload),
                             content_type='application/json')
        assert response.status_code == 201
        
        listing_id = json.loads(response.data)['id']
        
        # Delete the listing
        response = client.delete(f'/listings/{listing_id}')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['message'] == f'Listing {listing_id} deleted successfully'
        assert data['id'] == listing_id
        assert data['vin'] == sample_listing_payload['vin']
        
        # Verify listing is no longer available via individual page
        response = client.get(f'/listing/{listing_id}')
        assert response.status_code == 404
        
        # Verify listing is no longer in main listings page
        response = client.get('/')
        assert response.status_code == 200
        assert listing_id.encode() not in response.data
    
    def test_delete_listing_not_found(self, client):
        """Test deleting non-existent listing returns 404."""
        fake_id = 'nonexistent-listing-id'
        response = client.delete(f'/listings/{fake_id}')
        assert response.status_code == 404
        
        data = json.loads(response.data)
        assert 'not found' in data['error']
        assert fake_id in data['error']
    
    def test_delete_listing_affects_listing_count(self, client, sample_listing_payload):
        """Test that deleting a listing affects the listing count on main page."""
        # Add a listing
        response = client.post('/listings',
                             data=json.dumps(sample_listing_payload),
                             content_type='application/json')
        assert response.status_code == 201
        
        listing_id = json.loads(response.data)['id']
        
        # Verify listing appears on main page
        response = client.get('/')
        assert response.status_code == 200
        assert b'1 listings collected' in response.data
        
        # Delete the listing
        response = client.delete(f'/listings/{listing_id}')
        assert response.status_code == 200
        
        # Verify listing count decreased
        response = client.get('/')
        assert response.status_code == 200
        assert b'0 listings collected' in response.data
        assert b'No listings yet' in response.data
    
    def test_delete_listing_multiple(self, client, sample_listing_payload):
        """Test deleting multiple listings."""
        # Add two listings
        response1 = client.post('/listings',
                              data=json.dumps(sample_listing_payload),
                              content_type='application/json')
        assert response1.status_code == 201
        listing_id1 = json.loads(response1.data)['id']
        
        # Add second listing with different VIN
        second_listing = sample_listing_payload.copy()
        second_listing['vin'] = 'WVWZZZ1JZ1W654321'
        second_listing['title'] = 'Different GTI'
        response2 = client.post('/listings',
                              data=json.dumps(second_listing),
                              content_type='application/json')
        assert response2.status_code == 201
        listing_id2 = json.loads(response2.data)['id']
        
        # Verify both listings exist
        response = client.get('/')
        assert b'2 listings collected' in response.data
        
        # Delete first listing
        response = client.delete(f'/listings/{listing_id1}')
        assert response.status_code == 200
        
        # Verify count decreased
        response = client.get('/')
        assert b'1 listings collected' in response.data
        
        # Delete second listing
        response = client.delete(f'/listings/{listing_id2}')
        assert response.status_code == 200
        
        # Verify no listings remain
        response = client.get('/')
        assert b'0 listings collected' in response.data
        assert b'No listings yet' in response.data