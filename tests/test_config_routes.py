#!/usr/bin/env python3
"""
Tests for configuration web routes.
"""

import unittest
import tempfile
import os
from unittest.mock import patch, MagicMock
from flask import Flask
from config_manager import ConfigManager
from routes.config import create_config_routes

class TestConfigRoutes(unittest.TestCase):
    """Test configuration web routes."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create Flask test app
        self.app = Flask(__name__)
        self.app.config['TESTING'] = True
        
        # Create temporary config file
        self.temp_dir = tempfile.mkdtemp()
        self.config_file = os.path.join(self.temp_dir, 'test_config.json')
        
        # Create config manager and routes
        self.config_manager = ConfigManager(self.config_file)
        create_config_routes(self.app, self.config_manager)
        
        self.client = self.app.test_client()
    
    def tearDown(self):
        """Clean up test fixtures."""
        if os.path.exists(self.config_file):
            os.unlink(self.config_file)
        os.rmdir(self.temp_dir)
    
    @patch('routes.config.render_template')
    def test_config_page_get(self, mock_render):
        """Test GET request to configuration page."""
        mock_render.return_value = 'mocked template'
        
        response = self.client.get('/config')
        
        self.assertEqual(response.status_code, 200)
        mock_render.assert_called_once()
        # Verify template was called with config data
        call_args = mock_render.call_args
        self.assertEqual(call_args[0][0], 'config.html')
        self.assertIn('config', call_args[1])
    
    def test_config_page_post_valid(self):
        """Test POST request to configuration page with valid data."""
        response = self.client.post('/config', data={
            'sample_setting': 'Test Configuration Value'
        }, follow_redirects=False)
        
        # Should redirect back to config page
        self.assertEqual(response.status_code, 302)
        self.assertIn('/config', response.location)
        
        # Verify config was saved
        self.assertEqual(
            self.config_manager.get('sample_setting'), 
            'Test Configuration Value'
        )
    
    def test_config_page_post_empty(self):
        """Test POST request with empty value."""
        response = self.client.post('/config', data={
            'sample_setting': ''
        }, follow_redirects=False)
        
        # Should redirect successfully
        self.assertEqual(response.status_code, 302)
        
        # Verify empty string was saved
        self.assertEqual(self.config_manager.get('sample_setting'), '')
    
    def test_config_page_post_too_long(self):
        """Test POST request with value that's too long."""
        long_value = 'x' * 1001  # Exceeds 1000 character limit
        
        response = self.client.post('/config', data={
            'sample_setting': long_value
        })
        
        # Should return error
        self.assertEqual(response.status_code, 400)
        
        # Config should not be updated
        self.assertEqual(
            self.config_manager.get('sample_setting'), 
            'Default value'  # Should still have default
        )
    
    def test_config_page_post_missing_field(self):
        """Test POST request with missing form field."""
        response = self.client.post('/config', data={}, follow_redirects=False)
        
        # Should redirect (empty string is valid)
        self.assertEqual(response.status_code, 302)
        
        # Should save empty string
        self.assertEqual(self.config_manager.get('sample_setting'), '')

if __name__ == '__main__':
    unittest.main()