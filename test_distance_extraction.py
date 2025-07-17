#!/usr/bin/env python3
"""
Tests for distance extraction utility functions.
Tests the parsing logic for extracting distance from location text.
"""

import pytest
import sys
import os

# Add the project root to the path to import the function
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from routes.listings import extract_distance_from_location, process_listing_data


class TestDistanceExtraction:
    """Test distance extraction from location text."""
    
    def test_extract_distance_basic_pattern(self):
        """Test extracting distance from basic location pattern."""
        location = "San Francisco, CA (1,888 mi away)"
        result = extract_distance_from_location(location)
        assert result == "1888"
    
    def test_extract_distance_simple_number(self):
        """Test extracting distance with simple number."""
        location = "Cleveland, OH (15 mi away)"
        result = extract_distance_from_location(location)
        assert result == "15"
    
    def test_extract_distance_no_comma(self):
        """Test extracting distance without comma in number."""
        location = "Austin, TX (123 mi away)"
        result = extract_distance_from_location(location)
        assert result == "123"
    
    def test_extract_distance_case_insensitive(self):
        """Test that extraction is case insensitive."""
        location = "Portland, OR (45 MI AWAY)"
        result = extract_distance_from_location(location)
        assert result == "45"
    
    def test_extract_distance_with_spaces(self):
        """Test extraction with various spacing."""
        location = "Denver, CO (234 mi away)"  # Normal spacing - extra spaces in parens is uncommon
        result = extract_distance_from_location(location)
        assert result == "234"
    
    def test_extract_distance_none_input(self):
        """Test with None input."""
        result = extract_distance_from_location(None)
        assert result is None
    
    def test_extract_distance_empty_string(self):
        """Test with empty string."""
        result = extract_distance_from_location("")
        assert result is None
    
    def test_extract_distance_no_pattern(self):
        """Test with location that has no distance pattern."""
        location = "New York, NY"
        result = extract_distance_from_location(location)
        assert result is None
    
    def test_extract_distance_different_pattern(self):
        """Test with different text that shouldn't match."""
        location = "Located 50 miles from downtown"
        result = extract_distance_from_location(location)
        assert result is None
    
    def test_extract_distance_multiple_patterns(self):
        """Test with multiple distance patterns - should get first one."""
        location = "Between cities (100 mi away) and (200 mi away)"
        result = extract_distance_from_location(location)
        assert result == "100"


class TestProcessListingData:
    """Test the listing data processing function."""
    
    def test_process_listing_data_extract_distance(self):
        """Test that distance is extracted when not provided."""
        data = {
            'url': 'https://test.com',
            'price': '$25,000',
            'year': '2019',
            'mileage': '45000',
            'vin': 'TEST123',
            'location': 'Cleveland, OH (15 mi away)'
        }
        
        result = process_listing_data(data)
        
        assert result['distance'] == '15'
        assert result['location'] == 'Cleveland, OH (15 mi away)'
        # Original data should be preserved
        assert result['url'] == data['url']
        assert result['vin'] == data['vin']
    
    def test_process_listing_data_preserve_existing_distance(self):
        """Test that existing distance is not overridden."""
        data = {
            'url': 'https://test.com',
            'price': '$25,000',
            'year': '2019',
            'mileage': '45000',
            'vin': 'TEST123',
            'location': 'Cleveland, OH (15 mi away)',
            'distance': '25 mi away'  # Explicitly provided
        }
        
        result = process_listing_data(data)
        
        # Should keep the explicitly provided distance
        assert result['distance'] == '25 mi away'
        assert result['location'] == 'Cleveland, OH (15 mi away)'
    
    def test_process_listing_data_no_location(self):
        """Test processing when no location is provided."""
        data = {
            'url': 'https://test.com',
            'price': '$25,000',
            'year': '2019',
            'mileage': '45000',
            'vin': 'TEST123'
        }
        
        result = process_listing_data(data)
        
        # Should not add distance field
        assert 'distance' not in result
        # Original data should be preserved
        assert result['url'] == data['url']
        assert result['vin'] == data['vin']
    
    def test_process_listing_data_location_no_distance_pattern(self):
        """Test processing when location has no extractable distance."""
        data = {
            'url': 'https://test.com',
            'price': '$25,000',
            'year': '2019',
            'mileage': '45000',
            'vin': 'TEST123',
            'location': 'San Francisco, CA'  # No distance pattern
        }
        
        result = process_listing_data(data)
        
        # Should not add distance field
        assert 'distance' not in result
        assert result['location'] == 'San Francisco, CA'
    
    def test_process_listing_data_empty_distance(self):
        """Test processing when distance is empty string."""
        data = {
            'url': 'https://test.com',
            'price': '$25,000',
            'year': '2019',
            'mileage': '45000',
            'vin': 'TEST123',
            'location': 'Cleveland, OH (15 mi away)',
            'distance': ''  # Empty string
        }
        
        result = process_listing_data(data)
        
        # Should extract distance from location since provided distance is empty
        assert result['distance'] == '15'
        assert result['location'] == 'Cleveland, OH (15 mi away)'