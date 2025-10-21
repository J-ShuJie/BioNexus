#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
PyQt5 tr() method patch

Patches QWidget.tr() to use our simple i18n system instead of Qt's QTranslator
This allows existing code using self.tr() to work without modifications
"""

import logging
from PyQt5.QtWidgets import QWidget
from utils.translator import get_translator

logger = logging.getLogger('BioNexus.QTrPatch')

# Save original tr method
_original_tr = QWidget.tr


def patched_tr(self, text: str, *args, **kwargs) -> str:
    """
    Patched tr() method that uses our i18n system

    Args:
        self: QWidget instance
        text: Text to translate

    Returns:
        Translated text
    """
    # Get context from class name
    context = self.__class__.__name__

    # Use our translation system
    translator = get_translator()
    return translator.translate(text, context)


def install_tr_patch():
    """
    Install the tr() patch globally

    Call this once at application startup
    """
    QWidget.tr = patched_tr
    logger.info("✓ PyQt5 tr() method patched to use simple i18n system")
    print("✓ PyQt5 tr() method patched to use simple i18n system")


def uninstall_tr_patch():
    """
    Remove the tr() patch

    Restores original Qt behavior
    """
    QWidget.tr = _original_tr
    logger.info("✓ PyQt5 tr() method patch removed")
    print("✓ PyQt5 tr() method patch removed")
