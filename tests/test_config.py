#!/usr/bin/env python3
"""
Tests for configuration management functionality.
"""

import unittest
import tempfile
import os
import json
from pathlib import Path
from config_manager import ConfigManager

class TestConfigManager(unittest.TestCase):
    """Test configuration manager functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary config file for testing
        self.temp_dir = tempfile.mkdtemp()
        self.config_file = os.path.join(self.temp_dir, 'test_config.json')
        
    def tearDown(self):
        """Clean up test fixtures."""
        # Remove temporary files
        if os.path.exists(self.config_file):
            os.unlink(self.config_file)
        os.rmdir(self.temp_dir)
    
    def test_default_config_creation(self):
        """Test that default configuration is created when no file exists."""
        config_manager = ConfigManager(self.config_file)
        
        # Should have default values
        self.assertEqual(config_manager.get('sample_setting'), 'Default value')
        
        # Config file should be created
        self.assertTrue(os.path.exists(self.config_file))
    
    def test_config_persistence(self):
        """Test that configuration persists between instances."""
        # Create first instance and set a value
        config_manager1 = ConfigManager(self.config_file)
        config_manager1.set('sample_setting', 'Test Value 1')
        
        # Create second instance and verify value persisted
        config_manager2 = ConfigManager(self.config_file)
        self.assertEqual(config_manager2.get('sample_setting'), 'Test Value 1')
    
    def test_config_get_and_set(self):
        """Test getting and setting configuration values."""
        config_manager = ConfigManager(self.config_file)
        
        # Test default value
        self.assertEqual(config_manager.get('sample_setting'), 'Default value')
        
        # Test setting new value
        config_manager.set('sample_setting', 'New Value')
        self.assertEqual(config_manager.get('sample_setting'), 'New Value')
        
        # Test getting non-existent key with default
        self.assertIsNone(config_manager.get('nonexistent'))
        self.assertEqual(config_manager.get('nonexistent', 'default'), 'default')
    
    def test_config_update(self):
        """Test updating multiple configuration values at once."""
        config_manager = ConfigManager(self.config_file)
        
        updates = {
            'sample_setting': 'Updated Value',
            'new_setting': 'New Value'
        }
        
        config_manager.update(updates)
        
        self.assertEqual(config_manager.get('sample_setting'), 'Updated Value')
        self.assertEqual(config_manager.get('new_setting'), 'New Value')
    
    def test_config_get_all(self):
        """Test getting all configuration values."""
        config_manager = ConfigManager(self.config_file)
        config_manager.set('sample_setting', 'Test Value')
        
        all_config = config_manager.get_all()
        
        self.assertIsInstance(all_config, dict)
        self.assertEqual(all_config['sample_setting'], 'Test Value')
    
    def test_corrupted_config_file(self):
        """Test handling of corrupted configuration file."""
        # Create a corrupted JSON file
        with open(self.config_file, 'w') as f:
            f.write('invalid json content {')
        
        # Should fall back to defaults
        config_manager = ConfigManager(self.config_file)
        self.assertEqual(config_manager.get('sample_setting'), 'Default value')
    
    def test_config_file_validation(self):
        """Test that configuration values are properly saved as JSON."""
        config_manager = ConfigManager(self.config_file)
        config_manager.set('sample_setting', 'JSON Test Value')
        
        # Read file directly and verify JSON structure
        with open(self.config_file, 'r') as f:
            saved_config = json.load(f)
        
        self.assertEqual(saved_config['sample_setting'], 'JSON Test Value')

if __name__ == '__main__':
    unittest.main()