"""
Configuration manager for application settings.
Handles language, theme, and other preferences.
"""

import json
from pathlib import Path
from typing import Optional


class ConfigManager:
    """Manages application configuration and preferences."""
    
    CONFIG_DIR = Path.home() / ".EncryptionSystem"
    CONFIG_FILE = CONFIG_DIR / "config.json"
    
    DEFAULT_CONFIG = {
        "language": "en",
        "theme": "dark",
    }
    
    def __init__(self):
        """Initialize configuration manager and load config."""
        self._config = self.DEFAULT_CONFIG.copy()
        self._load_config()
    
    def _ensure_config_dir(self):
        """Ensure config directory exists."""
        self.CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    
    def _load_config(self):
        """Load configuration from file."""
        if self.CONFIG_FILE.exists():
            try:
                with open(self.CONFIG_FILE, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    self._config.update(loaded)
            except Exception as e:
                print(f"Warning: Could not load config: {e}")
    
    def save(self):
        """Save configuration to file."""
        self._ensure_config_dir()
        try:
            with open(self.CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(self._config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Warning: Could not save config: {e}")
    
    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """
        Get a configuration value.
        
        Args:
            key: Configuration key
            default: Default value if key not found
        
        Returns:
            Configuration value or default
        """
        return self._config.get(key, default)
    
    def set(self, key: str, value: str):
        """
        Set a configuration value.
        
        Args:
            key: Configuration key
            value: Configuration value
        """
        self._config[key] = value
        self.save()
    
    def get_language(self) -> str:
        """Get current language setting."""
        return self._config.get("language", "en")
    
    def set_language(self, language: str):
        """Set language and save."""
        self._config["language"] = language
        self.save()
    
    def get_theme(self) -> str:
        """Get current theme setting."""
        return self._config.get("theme", "dark")
    
    def set_theme(self, theme: str):
        """Set theme and save."""
        self._config["theme"] = theme
        self.save()


# Global config instance
_config: Optional[ConfigManager] = None


def init_config() -> ConfigManager:
    """Initialize the global config manager."""
    global _config
    _config = ConfigManager()
    return _config


def get_config() -> ConfigManager:
    """Get the global config manager instance."""
    if _config is None:
        init_config()
    return _config

