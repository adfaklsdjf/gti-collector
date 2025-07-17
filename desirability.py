#!/usr/bin/env python3
"""
Desirability calculation module for GTI listings.
Implements multi-criteria decision analysis for ranking cars by desirability.
"""

import logging
import re
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


def normalize_price(price_str: str, all_prices: List[str]) -> float:
    """
    Normalize price to 0-100 scale where lower price = higher score.
    
    Args:
        price_str: Price string like "$25,000"
        all_prices: List of all price strings for min/max calculation
        
    Returns:
        float: Score from 0-100 (higher = more desirable)
    """
    try:
        # Convert price string to numeric
        price_numeric = int(price_str.replace('$', '').replace(',', ''))
        
        # Get min/max from all prices
        all_numeric = []
        for p in all_prices:
            try:
                all_numeric.append(int(p.replace('$', '').replace(',', '')))
            except (ValueError, AttributeError):
                continue
        
        if not all_numeric:
            return 50.0  # Default if no valid prices
            
        min_price = min(all_numeric)
        max_price = max(all_numeric)
        
        if max_price == min_price:
            return 50.0  # All prices same
            
        # Invert so lower price = higher score
        normalized = 100 * (max_price - price_numeric) / (max_price - min_price)
        return max(0, min(100, normalized))
        
    except (ValueError, AttributeError) as e:
        logger.warning(f"Could not normalize price '{price_str}': {e}")
        return 50.0


def normalize_mileage(mileage_str: str, all_mileages: List[str]) -> float:
    """
    Normalize mileage to 0-100 scale where lower mileage = higher score.
    
    Args:
        mileage_str: Mileage string like "45,000"
        all_mileages: List of all mileage strings for min/max calculation
        
    Returns:
        float: Score from 0-100 (higher = more desirable)
    """
    try:
        # Convert mileage string to numeric
        mileage_numeric = int(mileage_str.replace(',', ''))
        
        # Get min/max from all mileages
        all_numeric = []
        for m in all_mileages:
            try:
                all_numeric.append(int(m.replace(',', '')))
            except (ValueError, AttributeError):
                continue
        
        if not all_numeric:
            return 50.0  # Default if no valid mileages
            
        min_mileage = min(all_numeric)
        max_mileage = max(all_numeric)
        
        if max_mileage == min_mileage:
            return 50.0  # All mileages same
            
        # Invert so lower mileage = higher score
        normalized = 100 * (max_mileage - mileage_numeric) / (max_mileage - min_mileage)
        return max(0, min(100, normalized))
        
    except (ValueError, AttributeError) as e:
        logger.warning(f"Could not normalize mileage '{mileage_str}': {e}")
        return 50.0


def normalize_year(year_str: str, all_years: List[str]) -> float:
    """
    Normalize year to 0-100 scale where newer year = higher score.
    
    Args:
        year_str: Year string like "2019"
        all_years: List of all year strings for min/max calculation
        
    Returns:
        float: Score from 0-100 (higher = more desirable)
    """
    try:
        # Convert year string to numeric
        year_numeric = int(year_str)
        
        # Get min/max from all years
        all_numeric = []
        for y in all_years:
            try:
                all_numeric.append(int(y))
            except (ValueError, AttributeError):
                continue
        
        if not all_numeric:
            return 50.0  # Default if no valid years
            
        min_year = min(all_numeric)
        max_year = max(all_numeric)
        
        if max_year == min_year:
            return 50.0  # All years same
            
        # Higher year = higher score
        normalized = 100 * (year_numeric - min_year) / (max_year - min_year)
        return max(0, min(100, normalized))
        
    except (ValueError, AttributeError) as e:
        logger.warning(f"Could not normalize year '{year_str}': {e}")
        return 50.0


def normalize_distance(distance_str: Optional[str], all_distances: List[Optional[str]]) -> float:
    """
    Normalize distance to 0-100 scale where shorter distance = higher score.
    
    Args:
        distance_str: Distance string like "123" (numeric miles) or None
        all_distances: List of all distance strings for min/max calculation
        
    Returns:
        float: Score from 0-100 (higher = more desirable)
    """
    try:
        if not distance_str:
            return 25.0  # Penalty for unknown distance
            
        # Convert distance string to numeric
        distance_numeric = int(distance_str)
        
        # Get min/max from all distances (excluding None/empty)
        all_numeric = []
        for d in all_distances:
            if d:
                try:
                    all_numeric.append(int(d))
                except (ValueError, AttributeError):
                    continue
        
        if not all_numeric:
            return 50.0  # Default if no valid distances
            
        min_distance = min(all_numeric)
        max_distance = max(all_numeric)
        
        if max_distance == min_distance:
            return 50.0  # All distances same
            
        # Invert so lower distance = higher score
        normalized = 100 * (max_distance - distance_numeric) / (max_distance - min_distance)
        return max(0, min(100, normalized))
        
    except (ValueError, AttributeError) as e:
        logger.warning(f"Could not normalize distance '{distance_str}': {e}")
        return 25.0  # Penalty for invalid distance


def calculate_desirability_score(listing: Dict[str, Any], all_listings: List[Dict[str, Any]]) -> float:
    """
    Calculate overall desirability score for a listing using weighted normalization.
    
    Args:
        listing: Individual listing dict with 'data' field
        all_listings: List of all listings for normalization context
        
    Returns:
        float: Desirability score from 0-100 (higher = more desirable)
    """
    try:
        data = listing.get('data', {})
        
        # Extract all values for normalization context
        all_prices = [l.get('data', {}).get('price', '') for l in all_listings]
        all_mileages = [l.get('data', {}).get('mileage', '') for l in all_listings]
        all_years = [l.get('data', {}).get('year', '') for l in all_listings]
        all_distances = [l.get('data', {}).get('distance') for l in all_listings]
        
        # Calculate individual normalized scores
        price_score = normalize_price(data.get('price', ''), all_prices)
        mileage_score = normalize_mileage(data.get('mileage', ''), all_mileages)
        year_score = normalize_year(data.get('year', ''), all_years)
        distance_score = normalize_distance(data.get('distance'), all_distances)
        
        # Default weights (can be made configurable later)
        weights = {
            'price': 0.4,      # Price is most important
            'mileage': 0.3,    # Mileage second most important  
            'year': 0.2,       # Year moderately important
            'distance': 0.1    # Distance least important for now
        }
        
        # Calculate weighted score
        total_score = (
            price_score * weights['price'] +
            mileage_score * weights['mileage'] + 
            year_score * weights['year'] +
            distance_score * weights['distance']
        )
        
        logger.debug(f"Desirability for {data.get('vin', 'unknown')}: "
                    f"price={price_score:.1f}, mileage={mileage_score:.1f}, "
                    f"year={year_score:.1f}, distance={distance_score:.1f}, "
                    f"total={total_score:.1f}")
        
        return round(total_score, 1)
        
    except Exception as e:
        logger.error(f"Error calculating desirability for listing: {e}")
        return 0.0


def add_desirability_scores(listings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Add desirability scores to all listings in place.
    
    Args:
        listings: List of listing dicts
        
    Returns:
        List[Dict[str, Any]]: Same listings with desirability_score added to each
    """
    if not listings:
        return listings
        
    logger.info(f"Calculating desirability scores for {len(listings)} listings")
    
    for listing in listings:
        score = calculate_desirability_score(listing, listings)
        listing['desirability_score'] = score
        
    logger.info("Desirability score calculation complete")
    return listings