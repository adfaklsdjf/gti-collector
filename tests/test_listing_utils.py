#!/usr/bin/env python3
"""
Unit tests for listing_utils module.
Tests data comparison and merging functionality.
"""

import pytest
from listing_utils import compare_listing_data, merge_listing_data, format_change_summary


class TestCompareListingData:
    """Test listing data comparison functionality."""
    
    def test_no_changes_detected(self):
        """Test when no changes are detected."""
        existing = {
            'price': '$25,000',
            'year': '2019',
            'mileage': '45000',
            'vin': 'WVWZZZ1JZ1W123456'
        }
        new = existing.copy()
        
        result = compare_listing_data(existing, new)
        
        assert result['has_changes'] is False
        assert result['changes'] == {}
        assert result['updated_data'] == existing
    
    def test_price_change_detected(self):
        """Test price change detection."""
        existing = {
            'price': '$25,000',
            'year': '2019',
            'vin': 'WVWZZZ1JZ1W123456'
        }
        new = {
            'price': '$24,500',
            'year': '2019',
            'vin': 'WVWZZZ1JZ1W123456'
        }
        
        result = compare_listing_data(existing, new)
        
        assert result['has_changes'] is True
        assert 'price' in result['changes']
        assert result['changes']['price']['old'] == '$25,000'
        assert result['changes']['price']['new'] == '$24,500'
        assert result['updated_data']['price'] == '$24,500'
    
    def test_multiple_changes_detected(self):
        """Test multiple field changes."""
        existing = {
            'price': '$25,000',
            'mileage': '45000',
            'location': 'Cleveland, OH',
            'vin': 'WVWZZZ1JZ1W123456'
        }
        new = {
            'price': '$24,500',
            'mileage': '46000',
            'location': 'Cleveland, OH (15 mi away)',
            'vin': 'WVWZZZ1JZ1W123456'
        }
        
        result = compare_listing_data(existing, new)
        
        assert result['has_changes'] is True
        assert len(result['changes']) == 3
        assert 'price' in result['changes']
        assert 'mileage' in result['changes']
        assert 'location' in result['changes']
    
    def test_new_field_added(self):
        """Test when new field is added."""
        existing = {
            'price': '$25,000',
            'vin': 'WVWZZZ1JZ1W123456'
        }
        new = {
            'price': '$25,000',
            'title': '2019 Volkswagen Golf GTI',
            'vin': 'WVWZZZ1JZ1W123456'
        }
        
        result = compare_listing_data(existing, new)
        
        assert result['has_changes'] is True
        assert 'title' in result['changes']
        assert result['changes']['title']['old'] is None
        assert result['changes']['title']['new'] == '2019 Volkswagen Golf GTI'
        assert result['updated_data']['title'] == '2019 Volkswagen Golf GTI'
    
    def test_none_values_ignored(self):
        """Test that None values in new data don't create changes."""
        existing = {
            'price': '$25,000',
            'title': 'Existing Title',
            'vin': 'WVWZZZ1JZ1W123456'
        }
        new = {
            'price': '$25,000',
            'title': None,
            'vin': 'WVWZZZ1JZ1W123456'
        }
        
        result = compare_listing_data(existing, new)
        
        assert result['has_changes'] is False
        assert result['updated_data']['title'] == 'Existing Title'


class TestMergeListingData:
    """Test listing data merging functionality."""
    
    def test_merge_preserves_existing(self):
        """Test that existing values are preserved when new is None."""
        existing = {
            'price': '$25,000',
            'title': 'Existing Title',
            'vin': 'WVWZZZ1JZ1W123456'
        }
        new = {
            'price': '$24,500',
            'title': None,
            'location': 'New Location'
        }
        
        result = merge_listing_data(existing, new)
        
        assert result['price'] == '$24,500'  # Updated
        assert result['title'] == 'Existing Title'  # Preserved
        assert result['location'] == 'New Location'  # Added
        assert result['vin'] == 'WVWZZZ1JZ1W123456'  # Preserved
    
    def test_merge_empty_strings_ignored(self):
        """Test that empty strings in new data are ignored."""
        existing = {'title': 'Existing Title'}
        new = {'title': ''}
        
        result = merge_listing_data(existing, new)
        
        assert result['title'] == 'Existing Title'


class TestFormatChangeSummary:
    """Test change summary formatting."""
    
    def test_no_changes_summary(self):
        """Test summary for no changes."""
        result = format_change_summary({})
        assert result == "No changes detected"
    
    def test_single_change_summary(self):
        """Test summary for single change."""
        changes = {
            'price': {'old': '$25,000', 'new': '$24,500'}
        }
        result = format_change_summary(changes)
        assert "Updated 1 field(s)" in result
        assert "price: $25,000 → $24,500" in result
    
    def test_multiple_changes_summary(self):
        """Test summary for multiple changes."""
        changes = {
            'price': {'old': '$25,000', 'new': '$24,500'},
            'mileage': {'old': '45000', 'new': '46000'}
        }
        result = format_change_summary(changes)
        assert "Updated 2 field(s)" in result
        assert "price: $25,000 → $24,500" in result
        assert "mileage: 45000 → 46000" in result
    
    def test_none_values_in_summary(self):
        """Test summary formatting with None values."""
        changes = {
            'title': {'old': None, 'new': 'New Title'}
        }
        result = format_change_summary(changes)
        assert "title: None → New Title" in result