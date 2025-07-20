#!/usr/bin/env python3
"""
Integration tests for Flask app endpoints.
Tests API functionality, error handling, and response formats.
"""

import pytest
import tempfile
import shutil
import json
import os


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
    # Set template folder to parent directory since we're in tests/ subdirectory
    template_folder = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates')
    test_app = Flask(__name__, template_folder=template_folder)
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
        'site': 'cargurus',
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
        """Test adding duplicate VIN with no content changes (only multi-site tracking update)."""
        # Add first listing
        response1 = client.post('/listings',
                               data=json.dumps(sample_listing_payload),
                               content_type='application/json')
        assert response1.status_code == 201
        first_id = json.loads(response1.data)['id']
        
        # Add duplicate with no changes - should update sites_seen tracking
        response2 = client.post('/listings',
                               data=json.dumps(sample_listing_payload),
                               content_type='application/json')
        assert response2.status_code == 200
        
        data = json.loads(response2.data)
        assert 'sites_seen' in data['message']  # Multi-site tracking was updated
        assert data['id'] == first_id
        assert data['updated'] is True  # Updated for multi-site tracking
    
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
            # Missing year, mileage, vin (distance is now optional)
        }
        
        response = client.post('/listings',
                             data=json.dumps(incomplete_payload),
                             content_type='application/json')
        
        assert response.status_code == 400
        
        data = json.loads(response.data)
        assert 'Missing required fields' in data['error']
        assert 'year' in data['error']
        assert 'vin' in data['error']
        # distance should not be in error since it's optional now
        assert 'distance' not in data['error']
    
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
        """Test that optional fields (title, location, distance) are stored."""
        payload = {
            'site': 'cargurus',
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
    
    def test_missing_distance_accepted(self, client):
        """Test that missing distance field is accepted since it's optional."""
        payload = {
            'site': 'cargurus',
            'url': 'https://test.com/listing/123',
            'price': '$25,000',
            'year': '2019',
            'mileage': '45000',
            'vin': 'WVWZZZ1JZ1W123456'
            # No distance field - should be accepted
        }
        
        response = client.post('/listings',
                             data=json.dumps(payload),
                             content_type='application/json')
        
        assert response.status_code == 201
    
    def test_distance_extracted_from_location(self, client):
        """Test that distance is extracted from location when not provided separately."""
        payload = {
            'site': 'cargurus',
            'url': 'https://test.com/listing/123',
            'price': '$25,000',
            'year': '2019',
            'mileage': '45000',
            'vin': 'WVWZZZ1JZ1W123456',
            'location': 'San Francisco, CA (1,888 mi away)'
            # No distance field - should be extracted from location
        }
        
        response = client.post('/listings',
                             data=json.dumps(payload),
                             content_type='application/json')
        
        assert response.status_code == 201
        
        # Verify the listing was stored with extracted distance
        listing_id = json.loads(response.data)['id']
        
        # Check via individual listing endpoint to see if distance was extracted
        listing_response = client.get(f'/listing/{listing_id}')
        assert listing_response.status_code == 200
        # The distance should be visible in the listing details (numeric format)
        assert b'1888' in listing_response.data
    
    def test_distance_not_extracted_when_provided(self, client):
        """Test that provided distance is not overridden by location extraction."""
        payload = {
            'site': 'cargurus',
            'url': 'https://test.com/listing/123',
            'price': '$25,000',
            'year': '2019',
            'mileage': '45000',
            'vin': 'WVWZZZ1JZ1W123456',
            'location': 'San Francisco, CA (1,888 mi away)',
            'distance': '25 mi away'  # Explicitly provided - should not be overridden
        }
        
        response = client.post('/listings',
                             data=json.dumps(payload),
                             content_type='application/json')
        
        assert response.status_code == 201
        
        # Verify the explicitly provided distance is preserved
        listing_id = json.loads(response.data)['id']
        listing_response = client.get(f'/listing/{listing_id}')
        assert listing_response.status_code == 200
        # Should show the explicitly provided distance, not the extracted one
        assert b'25 mi away' in listing_response.data
        assert b'1,888 mi away' not in listing_response.data.replace(b'San Francisco, CA (1,888 mi away)', b'')


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


class TestCommentsAPI:
    """Test comments API endpoint."""
    
    def test_update_comments_success(self, client, sample_listing_payload):
        """Test successfully updating comments for a listing."""
        # First add a listing
        response = client.post('/listings',
                             data=json.dumps(sample_listing_payload),
                             content_type='application/json')
        assert response.status_code == 201
        
        listing_id = json.loads(response.data)['id']
        
        # Update comments
        comments_data = {
            'comments': 'This is a great car!\nLooks very clean.\nWill check it out tomorrow.'
        }
        response = client.put(f'/listing/{listing_id}/comments',
                            data=json.dumps(comments_data),
                            content_type='application/json')
        
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'updated' in data['message']
        
        # Verify comments were saved by viewing the listing page
        response = client.get(f'/listing/{listing_id}')
        assert response.status_code == 200
        assert comments_data['comments'].encode() in response.data
    
    def test_update_comments_with_unicode(self, client, sample_listing_payload):
        """Test updating comments with unicode characters."""
        # First add a listing
        response = client.post('/listings',
                             data=json.dumps(sample_listing_payload),
                             content_type='application/json')
        assert response.status_code == 201
        
        listing_id = json.loads(response.data)['id']
        
        # Update comments with unicode
        comments_data = {
            'comments': 'Great car! 🚗\nPrice looks good 💰\nEmoji test: 🎉 ✨ 🔥'
        }
        response = client.put(f'/listing/{listing_id}/comments',
                            data=json.dumps(comments_data),
                            content_type='application/json')
        
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['success'] is True
    
    def test_update_comments_empty_string(self, client, sample_listing_payload):
        """Test updating comments with empty string (clearing comments)."""
        # First add a listing
        response = client.post('/listings',
                             data=json.dumps(sample_listing_payload),
                             content_type='application/json')
        assert response.status_code == 201
        
        listing_id = json.loads(response.data)['id']
        
        # Clear comments
        comments_data = {'comments': ''}
        response = client.put(f'/listing/{listing_id}/comments',
                            data=json.dumps(comments_data),
                            content_type='application/json')
        
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['success'] is True
    
    def test_update_comments_not_found(self, client):
        """Test updating comments for non-existent listing."""
        fake_id = 'nonexistent-listing-id'
        comments_data = {'comments': 'Some comments'}
        
        response = client.put(f'/listing/{fake_id}/comments',
                            data=json.dumps(comments_data),
                            content_type='application/json')
        
        assert response.status_code == 404
        
        data = json.loads(response.data)
        assert 'not found' in data['error']
        assert fake_id in data['error']
    
    def test_update_comments_no_json(self, client, sample_listing_payload):
        """Test updating comments without JSON data."""
        # First add a listing
        response = client.post('/listings',
                             data=json.dumps(sample_listing_payload),
                             content_type='application/json')
        assert response.status_code == 201
        
        listing_id = json.loads(response.data)['id']
        
        # Try to update without JSON
        response = client.put(f'/listing/{listing_id}/comments',
                            data='not json',
                            content_type='text/plain')
        
        assert response.status_code == 400
        
        data = json.loads(response.data)
        assert data['error'] == 'Content-Type must be application/json'
    
    def test_update_comments_empty_json(self, client, sample_listing_payload):
        """Test updating comments with empty JSON."""
        # First add a listing
        response = client.post('/listings',
                             data=json.dumps(sample_listing_payload),
                             content_type='application/json')
        assert response.status_code == 201
        
        listing_id = json.loads(response.data)['id']
        
        # Try to update with empty JSON
        response = client.put(f'/listing/{listing_id}/comments',
                            data='{}',
                            content_type='application/json')
        
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['success'] is True


class TestCSVExport:
    """Test CSV export functionality."""
    
    def test_csv_export_empty_listings(self, client):
        """Test CSV export with no listings."""
        response = client.get('/listings/export.csv')
        assert response.status_code == 200
        assert response.headers['Content-Type'] == 'text/csv'
        assert response.headers['Content-Disposition'] == 'attachment; filename=gti-listings-export.csv'
        
        # Should have header row only
        csv_data = response.data.decode('utf-8')
        lines = [line.strip() for line in csv_data.strip().split('\n')]
        assert len(lines) == 1
        assert lines[0] == 'link,price,year,mileage,vin'
    
    def test_csv_export_single_listing(self, client, sample_listing_payload):
        """Test CSV export with single listing."""
        # Add a listing first
        client.post('/listings',
                   data=json.dumps(sample_listing_payload),
                   content_type='application/json')
        
        response = client.get('/listings/export.csv')
        assert response.status_code == 200
        assert response.headers['Content-Type'] == 'text/csv'
        
        csv_data = response.data.decode('utf-8')
        lines = [line.strip() for line in csv_data.strip().split('\n')]
        assert len(lines) == 2  # Header + 1 data row
        
        # Check header
        assert lines[0] == 'link,price,year,mileage,vin'
        
        # Check data row - price will be quoted if it contains special characters
        assert sample_listing_payload['url'] in lines[1]
        assert sample_listing_payload['price'] in lines[1] or f'"{sample_listing_payload["price"]}"' in lines[1]
        assert sample_listing_payload['year'] in lines[1]
        assert sample_listing_payload['mileage'] in lines[1]
        assert sample_listing_payload['vin'] in lines[1]
    
    def test_csv_export_multiple_listings(self, client, sample_listing_payload):
        """Test CSV export with multiple listings."""
        # Add first listing
        client.post('/listings',
                   data=json.dumps(sample_listing_payload),
                   content_type='application/json')
        
        # Add second listing with different VIN
        second_listing = sample_listing_payload.copy()
        second_listing['vin'] = 'WVWZZZ1JZ1W654321'
        second_listing['price'] = '$24,000'
        second_listing['year'] = '2020'
        client.post('/listings',
                   data=json.dumps(second_listing),
                   content_type='application/json')
        
        response = client.get('/listings/export.csv')
        assert response.status_code == 200
        
        csv_data = response.data.decode('utf-8')
        lines = [line.strip() for line in csv_data.strip().split('\n')]
        assert len(lines) == 3  # Header + 2 data rows
        
        # Check header
        assert lines[0] == 'link,price,year,mileage,vin'
        
        # Check that both listings are present (order may vary)
        data_rows = lines[1:]
        vins_in_export = [row.split(',')[-1] for row in data_rows]
        assert sample_listing_payload['vin'] in vins_in_export
        assert second_listing['vin'] in vins_in_export
    
    def test_csv_export_missing_fields(self, client):
        """Test CSV export with listings missing some fields."""
        # Add a listing with missing optional fields
        minimal_listing = {
            'url': 'https://test.com/listing/123',
            'price': '$25,000',
            'year': '2019',
            'mileage': '45000',
            'distance': '15 mi away',
            'vin': 'WVWZZZ1JZ1W123456'
            # Missing title and location
        }
        
        client.post('/listings',
                   data=json.dumps(minimal_listing),
                   content_type='application/json')
        
        response = client.get('/listings/export.csv')
        assert response.status_code == 200
        
        csv_data = response.data.decode('utf-8')
        lines = [line.strip() for line in csv_data.strip().split('\n')]
        assert len(lines) == 2
        
        # Check that missing fields are handled gracefully
        assert minimal_listing['url'] in lines[1]
        assert minimal_listing['price'] in lines[1] or f'"{minimal_listing["price"]}"' in lines[1]
        assert minimal_listing['year'] in lines[1]
        assert minimal_listing['mileage'] in lines[1]
        assert minimal_listing['vin'] in lines[1]
    
    def test_csv_export_special_characters(self, client):
        """Test CSV export with special characters in data."""
        # Add a listing with special characters
        special_listing = {
            'url': 'https://test.com/listing/123',
            'price': '$25,000',
            'year': '2019',
            'mileage': '45,000',  # Comma in mileage
            'distance': '15 mi away',
            'vin': 'WVWZZZ1JZ1W123456'
        }
        
        client.post('/listings',
                   data=json.dumps(special_listing),
                   content_type='application/json')
        
        response = client.get('/listings/export.csv')
        assert response.status_code == 200
        
        csv_data = response.data.decode('utf-8')
        lines = [line.strip() for line in csv_data.strip().split('\n')]
        assert len(lines) == 2
        
        # Check that CSV properly handles commas by quoting
        assert '"45,000"' in lines[1]  # Mileage with comma should be quoted
    
    def test_csv_export_button_visibility(self, client, sample_listing_payload):
        """Test that CSV export button appears only when listings exist."""
        # Initially no listings - button should not be visible
        response = client.get('/')
        assert response.status_code == 200
        assert b'Export CSV' not in response.data
        
        # Add a listing
        client.post('/listings',
                   data=json.dumps(sample_listing_payload),
                   content_type='application/json')
        
        # Now button should be visible
        response = client.get('/')
        assert response.status_code == 200
        assert b'Export CSV' in response.data
        assert b'/listings/export.csv' in response.data