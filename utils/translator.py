#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
TranslationManager - Global translation manager with PyQt5 integration

Uses simple YAML-based i18n system instead of Qt's .qm files
Provides backward compatibility with Qt's tr() system
"""

import logging
from typing import Optional
from PyQt5.QtCore import QObject, pyqtSignal

# Import our simple i18n system
from utils.i18n import SimpleI18n, get_i18n

# Get logger
logger = logging.getLogger('BioNexus.Translation')


class TranslationManager(QObject):
    """
    Global translation manager
    
    Integrates simple YAML-based i18n with PyQt5's signal system
    """

    # Language switch signal
    languageChanged = pyqtSignal(str)  # locale

    # Supported languages
    SUPPORTED_LANGUAGES = SimpleI18n.SUPPORTED_LANGUAGES

    def __init__(self):
        """Initialize translation manager"""
        logger.debug("TranslationManager.__init__ called")
        
        # MUST call parent __init__ FIRST for QObject
        super().__init__()
        logger.debug("super().__init__() completed")

        # Get the i18n instance
        self._i18n = get_i18n()
        
        logger.info("TranslationManager initialized successfully")

    def load_language(self, locale: str) -> bool:
        """
        Load specified language

        Args:
            locale: Language code, e.g. 'zh_CN', 'en_US', 'de_DE'

        Returns:
            bool: Whether loading was successful
        """
        try:
            logger.info("=" * 60)
            logger.info("START load_language")
            logger.info(f"Requested locale: {locale}")
            
            old_locale = self._i18n.get_current_locale()
            logger.info(f"Current locale: {old_locale}")

            if locale not in self.SUPPORTED_LANGUAGES:
                logger.error(f"Unsupported language: {locale}")
                logger.error(f"Supported languages: {list(self.SUPPORTED_LANGUAGES.keys())}")
                return False

            # Switch language in i18n system
            success = self._i18n.set_language(locale)
            
            if not success:
                logger.error(f"FAILED: Could not switch to {locale}")
                return False

            logger.info(f"SUCCESS: Language switched: {old_locale} -> {locale}")

            # Emit language change signal
            if old_locale != locale:
                logger.info(f"Preparing to emit languageChanged signal, locale={locale}")
                try:
                    receivers = self.receivers(self.languageChanged)
                    logger.info(f"languageChanged signal has {receivers} receiver(s)")
                except Exception as e:
                    logger.warning(f"Unable to get signal receiver count: {e}")

                logger.info("Emitting languageChanged signal NOW...")
                self.languageChanged.emit(locale)
                logger.info("SUCCESS: languageChanged signal emitted")
            else:
                logger.info(f"Language unchanged, not emitting signal: {old_locale} == {locale}")

            logger.info("=" * 60)
            return True

        except Exception as e:
            logger.error(f"EXCEPTION in load_language: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False

    def switch_language(self, locale: str) -> bool:
        """
        Switch language (alias of load_language)

        Args:
            locale: Language code

        Returns:
            bool: Whether switch was successful
        """
        logger.info(f"switch_language called, locale={locale}")
        result = self.load_language(locale)
        logger.info(f"switch_language returned: {result}")
        return result

    def get_current_locale(self) -> str:
        """Get current language code"""
        return self._i18n.get_current_locale()

    def get_current_language_name(self) -> str:
        """Get current language display name"""
        return self._i18n.get_language_name()

    @staticmethod
    def get_supported_languages() -> dict:
        """Get supported languages list"""
        return TranslationManager.SUPPORTED_LANGUAGES.copy()
    
    def translate(self, text: str, context: str = None) -> str:
        """
        Translate text
        
        Args:
            text: Source text (English)
            context: Optional context
            
        Returns:
            Translated text
        """
        return self._i18n.translate(text, context)


# Create global singleton instance
_translator_instance: Optional[TranslationManager] = None


def get_translator() -> TranslationManager:
    """Get global translation manager instance"""
    global _translator_instance
    if _translator_instance is None:
        logger.info("Creating global TranslationManager instance")
        _translator_instance = TranslationManager()
        logger.info("Global TranslationManager instance created")
    return _translator_instance


def switch_language(locale: str) -> bool:
    """Global language switch function"""
    return get_translator().switch_language(locale)


def current_locale() -> str:
    """Get current language code"""
    return get_translator().get_current_locale()


# Provide a global tr() function for backward compatibility
def tr(text: str, context: str = None) -> str:
    """
    Translate text (global function for backward compatibility)
    
    This function can be used in place of QWidget.tr()
    
    Args:
        text: Source text (English)
        context: Optional context
        
    Returns:
        Translated text
        
    Example:
        from utils.translator import tr
        label.setText(tr("Settings"))
    """
    return get_translator().translate(text, context)
