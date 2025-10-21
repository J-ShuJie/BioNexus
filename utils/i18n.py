#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Simple YAML-based i18n system for BioNexus

Usage:
    from utils.i18n import _, set_language
    
    print(_("Hello"))  # 使用当前语言翻译
    
    set_language("zh_CN")  # 切换到中文
    print(_("Hello"))  # 输出: "你好"
"""

import yaml
import logging
from pathlib import Path
from typing import Dict, Optional

logger = logging.getLogger('BioNexus.i18n')


class SimpleI18n:
    """
    Simple YAML-based translation system
    
    Features:
    - Load translations from YAML files
    - Switch languages at runtime
    - Fallback to source text if translation missing
    - Easy to maintain and extend
    """
    
    SUPPORTED_LANGUAGES = {
        'zh_CN': '简体中文',
        'en_US': 'English',
        'de_DE': 'Deutsch',
    }
    
    def __init__(self):
        self._current_locale = 'zh_CN'
        self._translations: Dict[str, Dict[str, Dict[str, str]]] = {}
        self._i18n_dir = Path(__file__).parent.parent / 'translations' / 'i18n'
        
        # Load all translations
        self._load_all_translations()
        
        logger.info(f"i18n system initialized with {len(self._translations)} languages")
    
    def _load_all_translations(self):
        """Load all YAML translation files"""
        for locale in self.SUPPORTED_LANGUAGES.keys():
            yaml_file = self._i18n_dir / f"{locale}.yaml"
            if yaml_file.exists():
                try:
                    with open(yaml_file, 'r', encoding='utf-8') as f:
                        self._translations[locale] = yaml.safe_load(f) or {}
                    
                    # Count total translations
                    count = sum(len(context) for context in self._translations[locale].values())
                    logger.info(f"Loaded {locale}: {count} translations from {yaml_file.name}")
                except Exception as e:
                    logger.error(f"Failed to load {yaml_file}: {e}")
                    self._translations[locale] = {}
            else:
                logger.warning(f"Translation file not found: {yaml_file}")
                self._translations[locale] = {}
    
    def translate(self, text: str, context: str = None) -> str:
        """
        Translate text to current language
        
        Args:
            text: Source text (English)
            context: Optional context (class name)
        
        Returns:
            Translated text, or original if not found
        """
        if not text:
            return text
        
        locale_data = self._translations.get(self._current_locale, {})
        
        # Try with context first
        if context and context in locale_data:
            translation = locale_data[context].get(text)
            if translation:
                return translation
        
        # Try all contexts
        for context_data in locale_data.values():
            translation = context_data.get(text)
            if translation:
                return translation
        
        # Fallback to original text
        return text
    
    def set_language(self, locale: str) -> bool:
        """
        Switch to specified language
        
        Args:
            locale: Language code (e.g., 'zh_CN', 'en_US')
        
        Returns:
            bool: Success
        """
        if locale not in self.SUPPORTED_LANGUAGES:
            logger.error(f"Unsupported language: {locale}")
            return False
        
        old_locale = self._current_locale
        self._current_locale = locale
        logger.info(f"Language switched: {old_locale} -> {locale}")
        return True
    
    def get_current_locale(self) -> str:
        """Get current language code"""
        return self._current_locale
    
    def get_language_name(self, locale: str = None) -> str:
        """Get language display name"""
        locale = locale or self._current_locale
        return self.SUPPORTED_LANGUAGES.get(locale, locale)
    
    @staticmethod
    def get_supported_languages() -> dict:
        """Get all supported languages"""
        return SimpleI18n.SUPPORTED_LANGUAGES.copy()


# Global instance
_i18n_instance: Optional[SimpleI18n] = None


def get_i18n() -> SimpleI18n:
    """Get global i18n instance"""
    global _i18n_instance
    if _i18n_instance is None:
        _i18n_instance = SimpleI18n()
    return _i18n_instance


def _(text: str, context: str = None) -> str:
    """
    Translate text (shorthand function)
    
    Args:
        text: Source text
        context: Optional context
    
    Returns:
        Translated text
    
    Example:
        from utils.i18n import _
        print(_("Hello"))
    """
    return get_i18n().translate(text, context)


def set_language(locale: str) -> bool:
    """
    Switch language (shorthand function)
    
    Args:
        locale: Language code
    
    Returns:
        bool: Success
    
    Example:
        from utils.i18n import set_language
        set_language('zh_CN')
    """
    return get_i18n().set_language(locale)


def current_locale() -> str:
    """Get current language code"""
    return get_i18n().get_current_locale()


def current_language_name() -> str:
    """Get current language display name"""
    return get_i18n().get_language_name()
