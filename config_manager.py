#!/usr/bin/env python3
"""
Configuration management for GTI Listings app.
Handles storing and retrieving user configuration settings.
"""

import json
import os
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class ConfigManager:
    """Simple file-based configuration storage."""
    
    def __init__(self, config_file='config.json'):
        """Initialize configuration manager."""
        self.config_file = Path(config_file)
        self.config = self._load_config()
    
    def _load_config(self):
        """Load configuration from file."""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                logger.error(f"Error loading config file: {e}")
                return self._get_default_config()
        else:
            # Create default config file
            default_config = self._get_default_config()
            self._save_config(default_config)
            return default_config
    
    def _get_default_config(self):
        """Get default configuration values."""
        return {
            "sample_setting": "Default value"
        }
    
    def _save_config(self, config=None):
        """Save configuration to file."""
        if config is None:
            config = self.config
        
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
            logger.info(f"Configuration saved to {self.config_file}")
        except IOError as e:
            logger.error(f"Error saving config file: {e}")
            raise
    
    def get(self, key, default=None):
        """Get a configuration value."""
        return self.config.get(key, default)
    
    def set(self, key, value):
        """Set a configuration value and save to file."""
        self.config[key] = value
        self._save_config()
    
    def get_all(self):
        """Get all configuration values."""
        return self.config.copy()
    
    def update(self, updates):
        """Update multiple configuration values at once."""
        self.config.update(updates)
        self._save_config()