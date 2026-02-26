#!/usr/bin/env python3
"""
Settings configuration for spec2.0 AI DOM Engine
Single source of truth: .env only. No config file for API keys.
"""

import os
from pathlib import Path
from typing import Optional

# Load .env from project root (Nexora.ai) - same for all entry points
_env_path = Path(__file__).parent.parent / ".env"
if _env_path.exists():
    from dotenv import load_dotenv
    load_dotenv(_env_path)

class Settings:
    """Application settings with API key management"""
    
    def __init__(self):
        # Try Viser AI config dir first, then fall back to spec2 dir
        viser_config_dir = Path.home() / ".viser_ai"
        spec2_config_dir = Path.home() / ".spec2"
        
        if (viser_config_dir / "config.json").exists():
            self.config_dir = viser_config_dir
        elif (spec2_config_dir / "config.json").exists():
            self.config_dir = spec2_config_dir
        else:
            # Default to viser_ai for new installs
            self.config_dir = viser_config_dir
        
        self.config_file = self.config_dir / "config.json"
        self._config = {}
        self._load_config()
    
    def _load_config(self):
        """Load configuration from file"""
        if self.config_file.exists():
            try:
                import json
                with open(self.config_file, 'r') as f:
                    self._config = json.load(f)
            except Exception as e:
                print(f"Warning: Could not load config: {e}")
                self._config = {}
    
    def _save_config(self):
        """Save configuration to file"""
        try:
            self.config_dir.mkdir(exist_ok=True)
            import json
            with open(self.config_file, 'w') as f:
                json.dump(self._config, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save config: {e}")
    
    @property
    def groq_api_key(self) -> Optional[str]:
        """Get Groq API key from .env only"""
        return os.getenv('GROQ_API_KEY')
    
    @groq_api_key.setter
    def groq_api_key(self, value: str):
        """Set Groq API key in config file"""
        self._config['groq_api_key'] = value
        self._save_config()
    
    @property
    def gemini_api_key(self) -> Optional[str]:
        """Get Gemini API key from .env only"""
        return os.getenv('GEMINI_API_KEY')
    
    @gemini_api_key.setter
    def gemini_api_key(self, value: str):
        """Set Gemini API key in config file"""
        self._config['gemini_api_key'] = value
        self._save_config()
    
    @property
    def openai_api_key(self) -> Optional[str]:
        """Get OpenAI API key from .env only"""
        return os.getenv('OPENAI_API_KEY')
    
    @openai_api_key.setter
    def openai_api_key(self, value: str):
        """Set OpenAI API key in config file"""
        self._config['openai_api_key'] = value
        self._save_config()
    
    @property
    def default_provider(self) -> str:
        """Get default AI provider"""
        return self._config.get('default_provider', 'groq')
    
    @default_provider.setter
    def default_provider(self, value: str):
        """Set default AI provider"""
        self._config['default_provider'] = value
        self._save_config()
    
    def has_groq_key(self) -> bool:
        """Check if Groq API key is available"""
        return bool(self.groq_api_key)
    
    def has_gemini_key(self) -> bool:
        """Check if Gemini API key is available"""
        return bool(self.gemini_api_key)
    
    def has_openai_key(self) -> bool:
        """Check if OpenAI API key is available"""
        return bool(self.openai_api_key)
    
    def get_available_providers(self) -> list:
        """Get list of available providers"""
        providers = []
        if self.has_groq_key():
            providers.append('groq')
        if self.has_gemini_key():
            providers.append('gemini')
        if self.has_openai_key():
            providers.append('openai')
        return providers
    
    def print_status(self):
        """Print current configuration status"""
        print("🤖 Viser AI - Core Engine Configuration")
        print("=" * 50)
        print(f"GROQ_API_KEY: {'✅ Set' if self.has_groq_key() else '❌ Missing'}")
        print(f"GEMINI_API_KEY: {'✅ Set' if self.has_gemini_key() else '❌ Missing'}")
        print(f"OPENAI_API_KEY: {'✅ Set' if self.has_openai_key() else '❌ Missing'}")
        print(f"Default Provider: {self.default_provider}")
        print(f"Available Providers: {', '.join(self.get_available_providers()) or 'None'}")
        print(f"Config File: {self.config_file}")
        print("=" * 50)

# Global settings instance
settings = Settings()

def get_settings() -> Settings:
    """Get global settings instance"""
    return settings
