"""
Translation module for Encryption System
Supports multiple languages with JSON translation files.
"""

import json
import locale
from pathlib import Path
from typing import Any, Optional


class TranslationManager:
    """Manages application translations."""
    
    SUPPORTED_LANGUAGES = ["en", "fr"]
    DEFAULT_LANGUAGE = "en"
    
    def __init__(self, language: Optional[str] = None):
        """
        Initialize the translation manager.
        
        Args:
            language: Language code (e.g., 'en', 'fr'). If None, detects system language.
        """
        self.language = language or self._detect_language()
        self._translations = self._load_translations()
    
    def _detect_language(self) -> str:
        """Detect system language from locale."""
        try:
            system_lang = locale.getlocale()[0]
            if system_lang:
                lang_code = system_lang.split("_")[0].lower()
                if lang_code in self.SUPPORTED_LANGUAGES:
                    return lang_code
        except Exception:
            pass
        return self.DEFAULT_LANGUAGE
    
    def _load_translations(self) -> dict[str, Any]:
        """Load translation JSON file for the current language."""
        translate_dir = Path(__file__).parent / "translate"
        lang_file = translate_dir / f"{self.language}.json"
        
        if not lang_file.exists():
            lang_file = translate_dir / f"{self.DEFAULT_LANGUAGE}.json"
        
        try:
            with open(lang_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: Could not load translations: {e}")
            return {}
    
    def get(self, key: str, default: str = "", **kwargs) -> str:
        """
        Get a translated string.
        
        Args:
            key: Translation key in dot notation (e.g., 'auth.btn_save')
            default: Default value if key not found
            **kwargs: Format arguments for string interpolation
        
        Returns:
            Translated string with formatted placeholders
        """
        keys = key.split(".")
        value = self._translations
        
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
        
        if value is None:
            return default
        
        if not isinstance(value, str):
            return default
        
        # Format string with provided arguments
        try:
            return value.format(**kwargs)
        except (KeyError, ValueError):
            return value
    
    def set_language(self, language: str) -> bool:
        """
        Change the current language.
        
        Args:
            language: Language code to switch to
        
        Returns:
            True if language was changed successfully, False otherwise
        """
        if language not in self.SUPPORTED_LANGUAGES:
            return False
        
        self.language = language
        self._translations = self._load_translations()
        return True
    
    def get_available_languages(self) -> list[str]:
        """Get list of available language codes."""
        return self.SUPPORTED_LANGUAGES.copy()


# Global translator instance
_translator: Optional[TranslationManager] = None


def init_translator(language: Optional[str] = None) -> TranslationManager:
    """Initialize the global translator."""
    global _translator
    _translator = TranslationManager(language)
    return _translator


def t(key: str, default: str = "", **kwargs) -> str:
    """
    Convenience function to get translated strings.
    
    Args:
        key: Translation key in dot notation
        default: Default value if key not found
        **kwargs: Format arguments
    
    Returns:
        Translated string
    """
    if _translator is None:
        init_translator()
    return _translator.get(key, default, **kwargs)


def set_language(language: str) -> bool:
    """Set the global translator language."""
    if _translator is None:
        init_translator()
    return _translator.set_language(language)


def get_translator() -> TranslationManager:
    """Get the global translator instance."""
    if _translator is None:
        init_translator()
    return _translator

