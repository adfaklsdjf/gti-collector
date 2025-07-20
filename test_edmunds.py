#!/usr/bin/env python3
"""
Test script for Edmunds integration using sample data
"""

import json
from site_mappings import process_site_data

def test_edmunds_processing():
    """Test processing of sample Edmunds data"""
    
    # Sample data from your Edmunds JS snippet output
    sample_edmunds_data = {
        'site': 'edmunds',
        'url': 'https://www.edmunds.com/inventory/example-listing',
        'Title': '2019 Volkswagen Golf GTI - VIN: 3VW5T7AU5KM037436',
        'Mileage': '29,404',
        'Trim': 'SE 4dr Hatchback (2.0L 4cyl Turbo 6M)',
        'Ext. Color': 'Deep Black Pearl',
        'Int. Color': 'Titan Black w/Red Stitching leather',
        'Accidents': 'No Reported Accidents',
        'Owners': '1',
        'Price': '24857',
        'Stock #': '2114P',
        'VIN': '3VW5T7AU5KM037436'
    }
    
    print("🧪 Testing Edmunds data processing...")
    print(f"📥 Input data: {json.dumps(sample_edmunds_data, indent=2)}")
    
    # Process the data through site mappings
    processed_data = process_site_data(sample_edmunds_data)
    
    print(f"📤 Processed data: {json.dumps(processed_data, indent=2)}")
    
    # Verify key mappings
    expected_mappings = {
        'title': '2019 Volkswagen Golf GTI - VIN: 3VW5T7AU5KM037436',
        'price': '$24857',  # Should have $ prefix added
        'mileage': '29,404',
        'trim_level': 'SE 4dr Hatchback (2.0L 4cyl Turbo 6M)',
        'exterior_color': 'Deep Black Pearl',
        'interior_color': 'Titan Black w/Red Stitching leather',
        'accidents': '0 accidents reported',  # Should be normalized
        'previous_owners': '1',
        'vin': '3VW5T7AU5KM037436',
        'stock_number': '2114P',
        'urls': {'edmunds': 'https://www.edmunds.com/inventory/example-listing'},
        'last_updated_site': 'edmunds'
    }
    
    print("\n🔍 Verification:")
    all_correct = True
    
    for field, expected_value in expected_mappings.items():
        actual_value = processed_data.get(field)
        if actual_value == expected_value:
            print(f"✅ {field}: {actual_value}")
        else:
            print(f"❌ {field}: expected '{expected_value}', got '{actual_value}'")
            all_correct = False
    
    if all_correct:
        print("\n🎉 All mappings verified successfully!")
    else:
        print("\n⚠️ Some mappings need adjustment")
    
    return processed_data

if __name__ == "__main__":
    test_edmunds_processing()