"""Configuration management for Email Helper.

This module provides centralized configuration management for the entire
email helper application. It consolidates configuration loading, validation,
and access patterns into a single, well-structured interface.

The ConfigManager handles:
- Environment variable loading
- Configuration file parsing
- Default value management
- Configuration validation
- Type conversion and parsing
- Secure credential management

This replaces scattered configuration code throughout the application
with a single, consistent configuration interface.
"""

import os
import json
from typing import Any, Dict, Optional, Union
from pathlib import Path
from dotenv import load_dotenv


class ConfigManager:
    """Centralized configuration management."""
    
    def __init__(self, config_file: Optional[str] = None):
        # Load environment variables
        load_dotenv()
        
        # Initialize configuration
        self._config: Dict[str, Any] = {}
        self._load_defaults()
        
        # Load from file if provided
        if config_file and os.path.exists(config_file):
            self._load_from_file(config_file)
            
    def _load_defaults(self):
        """Load default configuration values."""
        self._config = {
            'azure': {
                'endpoint': os.getenv('AZURE_OPENAI_ENDPOINT'),
                'api_key': os.getenv('AZURE_OPENAI_API_KEY'),
                'api_version': os.getenv('AZURE_OPENAI_API_VERSION', '2024-02-15-preview'),
                'deployment_name': os.getenv('AZURE_OPENAI_DEPLOYMENT_NAME', 'gpt-4o-mini'),
                'model': os.getenv('AZURE_OPENAI_MODEL', 'gpt-4o-mini')
            },
            'email': {
                'default_folder': 'Inbox',
                'batch_size': 50,
                'thread_context_limit': 10
            },
            'processing': {
                'confidence_threshold': 0.7,
                'max_retries': 3,
                'timeout_seconds': 30
            },
            'storage': {
                'base_dir': self._get_runtime_data_dir(),
                'database_name': 'email_helper_history.db',
                'backup_enabled': True
            },
            'ui': {
                'window_title': 'Email Helper',
                'default_width': 1200,
                'default_height': 800,
                'theme': 'default'
            },
            'logging': {
                'level': 'INFO',
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                'file_enabled': True
            }
        }
        
    def _load_from_file(self, config_file: str):
        """Load configuration from JSON file."""
        try:
            with open(config_file, 'r') as f:
                file_config = json.load(f)
                self._merge_config(self._config, file_config)
        except Exception as e:
            print(f"Warning: Could not load config file {config_file}: {e}")
            
    def _merge_config(self, base: Dict, override: Dict):
        """Recursively merge configuration dictionaries."""
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._merge_config(base[key], value)
            else:
                base[key] = value
                
    def _get_runtime_data_dir(self) -> str:
        """Get the runtime data directory path."""
        current_dir = Path(__file__).parent.parent.parent
        return str(current_dir / 'runtime_data')
        
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value using dot notation."""
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
                
        return value
        
    def set(self, key: str, value: Any):
        """Set configuration value using dot notation."""
        keys = key.split('.')
        config = self._config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
            
        config[keys[-1]] = value
        
    def get_azure_config(self) -> Dict[str, Any]:
        """Get Azure configuration as dictionary."""
        return self._config.get('azure', {})
        
    def get_storage_path(self, filename: str) -> str:
        """Get full path for storage file."""
        base_dir = self.get('storage.base_dir')
        return os.path.join(base_dir, filename)
        
    def is_configured(self) -> bool:
        """Check if essential configuration is present."""
        azure_config = self.get_azure_config()
        return bool(azure_config.get('endpoint') and 
                   (azure_config.get('api_key') or os.getenv('AZURE_CLIENT_ID')))
                   
    def validate(self) -> list:
        """Validate configuration and return list of issues."""
        issues = []
        
        # Check Azure configuration
        azure_config = self.get_azure_config()
        if not azure_config.get('endpoint'):
            issues.append("Azure OpenAI endpoint not configured")
            
        if not azure_config.get('api_key') and not os.getenv('AZURE_CLIENT_ID'):
            issues.append("Azure authentication not configured")
            
        # Check storage directory
        storage_dir = self.get('storage.base_dir')
        if not os.path.exists(storage_dir):
            try:
                os.makedirs(storage_dir, exist_ok=True)
            except Exception as e:
                issues.append(f"Cannot create storage directory: {e}")
                
        return issues


# Global configuration instance
config = ConfigManager()