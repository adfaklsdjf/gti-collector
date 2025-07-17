#!/usr/bin/env python3
"""
Tests for desirability calculation module.
"""

import pytest
from desirability import (
    normalize_price, normalize_mileage, normalize_year, normalize_distance,
    calculate_desirability_score, add_desirability_scores
)


class TestNormalizationFunctions:
    """Test individual normalization functions."""
    
    def test_normalize_price_basic(self):
        """Test basic price normalization."""
        prices = ['$20,000', '$30,000', '$40,000']
        
        # Lowest price should get highest score (100)
        assert normalize_price('$20,000', prices) == 100.0
        
        # Highest price should get lowest score (0)
        assert normalize_price('$40,000', prices) == 0.0
        
        # Middle price should get middle score (50)
        assert normalize_price('$30,000', prices) == 50.0
    
    def test_normalize_price_single_value(self):
        """Test price normalization with single price."""
        prices = ['$25,000']
        assert normalize_price('$25,000', prices) == 50.0
    
    def test_normalize_price_invalid_input(self):
        """Test price normalization with invalid input."""
        prices = ['$20,000', '$30,000']
        assert normalize_price('invalid', prices) == 50.0
        assert normalize_price('', prices) == 50.0
        assert normalize_price(None, prices) == 50.0
    
    def test_normalize_mileage_basic(self):
        """Test basic mileage normalization."""
        mileages = ['10,000', '50,000', '100,000']
        
        # Lowest mileage should get highest score (100)
        assert normalize_mileage('10,000', mileages) == 100.0
        
        # Highest mileage should get lowest score (0)
        assert normalize_mileage('100,000', mileages) == 0.0
        
        # Middle mileage should get middle score (50)
        assert normalize_mileage('50,000', mileages) == pytest.approx(55.6, abs=0.1)
    
    def test_normalize_year_basic(self):
        """Test basic year normalization."""
        years = ['2018', '2020', '2022']
        
        # Newest year should get highest score (100)
        assert normalize_year('2022', years) == 100.0
        
        # Oldest year should get lowest score (0)
        assert normalize_year('2018', years) == 0.0
        
        # Middle year should get middle score (50)
        assert normalize_year('2020', years) == 50.0
    
    def test_normalize_distance_basic(self):
        """Test basic distance normalization."""
        distances = ['10', '50', '100']
        
        # Shortest distance should get highest score (100)
        assert normalize_distance('10', distances) == 100.0
        
        # Longest distance should get lowest score (0)
        assert normalize_distance('100', distances) == 0.0
        
        # Middle distance should get middle score (50)
        assert normalize_distance('50', distances) == pytest.approx(55.6, abs=0.1)
    
    def test_normalize_distance_none_input(self):
        """Test distance normalization with None input."""
        distances = ['10', '50', '100']
        assert normalize_distance(None, distances) == 25.0
        assert normalize_distance('', distances) == 25.0
    
    def test_normalize_empty_lists(self):
        """Test normalization functions with empty input lists."""
        assert normalize_price('$25,000', []) == 50.0
        assert normalize_mileage('50,000', []) == 50.0
        assert normalize_year('2020', []) == 50.0
        assert normalize_distance('50', []) == 50.0


class TestDesirabilityCalculation:
    """Test overall desirability calculation."""
    
    @pytest.fixture
    def sample_listings(self):
        """Sample listings for testing."""
        return [
            {
                'id': '1',
                'data': {
                    'price': '$20,000',
                    'mileage': '30,000',
                    'year': '2022',
                    'distance': '10',
                    'vin': 'VIN1'
                }
            },
            {
                'id': '2', 
                'data': {
                    'price': '$25,000',
                    'mileage': '50,000',
                    'year': '2020',
                    'distance': '25',
                    'vin': 'VIN2'
                }
            },
            {
                'id': '3',
                'data': {
                    'price': '$30,000',
                    'mileage': '80,000', 
                    'year': '2018',
                    'distance': '50',
                    'vin': 'VIN3'
                }
            }
        ]
    
    def test_calculate_desirability_score_best_car(self, sample_listings):
        """Test that the best car gets the highest score."""
        # Car 1 should score highest: cheapest, lowest miles, newest, closest
        score1 = calculate_desirability_score(sample_listings[0], sample_listings)
        score2 = calculate_desirability_score(sample_listings[1], sample_listings)
        score3 = calculate_desirability_score(sample_listings[2], sample_listings)
        
        assert score1 > score2 > score3
        assert score1 > 80  # Should be quite high
        assert score3 < 20  # Should be quite low
    
    def test_calculate_desirability_score_missing_data(self, sample_listings):
        """Test desirability calculation with missing data."""
        listing_missing_distance = {
            'id': '4',
            'data': {
                'price': '$22,000',
                'mileage': '40,000',
                'year': '2021',
                'vin': 'VIN4'
                # No distance field
            }
        }
        
        all_listings = sample_listings + [listing_missing_distance]
        score = calculate_desirability_score(listing_missing_distance, all_listings)
        
        # Should still get a reasonable score, but penalized for missing distance
        assert 0 <= score <= 100
    
    def test_add_desirability_scores(self, sample_listings):
        """Test adding desirability scores to listings."""
        listings_with_scores = add_desirability_scores(sample_listings)
        
        # Check that scores were added
        for listing in listings_with_scores:
            assert 'desirability_score' in listing
            assert 0 <= listing['desirability_score'] <= 100
        
        # Check that best car has highest score
        scores = [l['desirability_score'] for l in listings_with_scores]
        assert max(scores) == listings_with_scores[0]['desirability_score']
        assert min(scores) == listings_with_scores[2]['desirability_score']
    
    def test_add_desirability_scores_empty_list(self):
        """Test adding scores to empty list."""
        result = add_desirability_scores([])
        assert result == []
    
    def test_desirability_weights_impact(self, sample_listings):
        """Test that different factors have appropriate impact on score."""
        # Create two cars that differ only in one factor
        car_cheap = {
            'id': '1',
            'data': {'price': '$20,000', 'mileage': '50,000', 'year': '2020', 'distance': '30'}
        }
        car_expensive = {
            'id': '2', 
            'data': {'price': '$40,000', 'mileage': '50,000', 'year': '2020', 'distance': '30'}
        }
        
        test_listings = [car_cheap, car_expensive]
        
        score_cheap = calculate_desirability_score(car_cheap, test_listings)
        score_expensive = calculate_desirability_score(car_expensive, test_listings)
        
        # Cheaper car should have significantly higher score (price weight = 0.4)
        assert score_cheap > score_expensive
        assert (score_cheap - score_expensive) > 30  # Should be substantial difference
    
    def test_score_range_validity(self, sample_listings):
        """Test that all scores are in valid 0-100 range."""
        for listing in sample_listings:
            score = calculate_desirability_score(listing, sample_listings)
            assert 0 <= score <= 100
            assert isinstance(score, float)