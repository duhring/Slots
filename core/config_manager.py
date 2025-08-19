"""
Configuration manager for editorial highlights
Handles GitHub settings and user preferences
"""

import json
import os
from pathlib import Path
from typing import Dict, Optional


class ConfigManager:
    def __init__(self):
        self.config_dir = Path.home() / '.editorial_highlights'
        self.config_file = self.config_dir / 'config.json'
        self.ensure_config_dir()
    
    def ensure_config_dir(self):
        """Ensure configuration directory exists"""
        self.config_dir.mkdir(parents=True, exist_ok=True)
    
    def has_github_config(self) -> bool:
        """Check if GitHub configuration exists"""
        if not self.config_file.exists():
            return False
        
        try:
            config = self.load_config()
            return 'github' in config and 'username' in config['github']
        except:
            return False
    
    def get_github_config(self) -> Dict[str, str]:
        """Get GitHub configuration"""
        config = self.load_config()
        
        if 'github' not in config:
            return {}
        
        github_config = config['github']
        
        # Return with defaults
        return {
            'username': github_config.get('username', ''),
            'repo': github_config.get('repo', 'editorial-highlights')
        }
    
    def save_github_config(self, username: str, repo: str):
        """Save GitHub configuration"""
        config = self.load_config()
        
        config['github'] = {
            'username': username,
            'repo': repo
        }
        
        self.save_config(config)
    
    def load_config(self) -> Dict:
        """Load configuration from file"""
        if not self.config_file.exists():
            return {}
        
        try:
            with open(self.config_file, 'r') as f:
                return json.load(f)
        except:
            return {}
    
    def save_config(self, config: Dict):
        """Save configuration to file"""
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=2)
    
    def get_preference(self, key: str, default=None):
        """Get a user preference"""
        config = self.load_config()
        preferences = config.get('preferences', {})
        return preferences.get(key, default)
    
    def set_preference(self, key: str, value):
        """Set a user preference"""
        config = self.load_config()
        
        if 'preferences' not in config:
            config['preferences'] = {}
        
        config['preferences'][key] = value
        self.save_config(config)
    
    def get_recent_keywords(self, limit: int = 10) -> list:
        """Get recently used keywords"""
        config = self.load_config()
        return config.get('recent_keywords', [])[:limit]
    
    def add_recent_keywords(self, keywords: list):
        """Add keywords to recent list"""
        config = self.load_config()
        
        if 'recent_keywords' not in config:
            config['recent_keywords'] = []
        
        # Add new keywords to front, remove duplicates
        for keyword in reversed(keywords):
            if keyword in config['recent_keywords']:
                config['recent_keywords'].remove(keyword)
            config['recent_keywords'].insert(0, keyword)
        
        # Keep only last 50 keywords
        config['recent_keywords'] = config['recent_keywords'][:50]
        
        self.save_config(config)