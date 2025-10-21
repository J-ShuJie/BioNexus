#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Tool localization helpers

Provides a stable API for getting localized tool texts used across UI and core.

Current scope:
- get_localized_tool_description(tool_data): returns a description string based
  on current locale with sensible fallbacks.

This module is intentionally lightweight and independent of PyQt.
"""

from typing import Dict

try:
    # Prefer the app's translation/i18n layer to get current locale
    from utils.translator import current_locale  # type: ignore
except Exception:
    try:
        from utils.i18n import current_locale  # type: ignore
    except Exception:
        # Fallback if translation system is unavailable at import time
        def current_locale() -> str:  # type: ignore
            return 'zh_CN'


_SUFFIX_BY_LOCALE = {
    'zh_CN': ('zh', 'cn', 'zh_cn', 'zh-CN'),
    'en_US': ('en', 'en_us', 'en-US'),
    'de_DE': ('de', 'de_de', 'de-DE'),
}


def _from_variant_fields(data: Dict, locale: str) -> str:
    """Try to read description from variant fields like description_en/zh/de."""
    # Direct exact match first
    key_exact = f'description_{locale}'
    if key_exact in data and isinstance(data[key_exact], str):
        return data[key_exact]

    # Try common suffixes for the locale
    for suf in _SUFFIX_BY_LOCALE.get(locale, ()):  # type: ignore[arg-type]
        key = f'description_{suf}'
        if key in data and isinstance(data[key], str):
            return data[key]
    return ''


def get_localized_tool_description(tool_data: Dict) -> str:
    """
    Return a localized description for a tool.

    Priority:
    1) tool_data['descriptions'][current_locale]
    2) tool_data['description_<variant>'] (e.g., description_en/zh/de)
    3) tool_data['description']
    4) ''
    """
    if not isinstance(tool_data, dict):
        return ''

    locale = current_locale() or 'zh_CN'

    # 1) Look for consolidated mapping
    descriptions = tool_data.get('descriptions')
    if isinstance(descriptions, dict):
        # Exact locale
        if locale in descriptions and isinstance(descriptions[locale], str):
            return descriptions[locale]
        # Common fallbacks
        for fallback in ('en_US', 'zh_CN', 'de_DE'):
            val = descriptions.get(fallback)
            if isinstance(val, str) and val:
                return val

    # 2) Variant fields like description_en/zh/de
    variant = _from_variant_fields(tool_data, locale)
    if variant:
        return variant

    # 3) Plain description
    desc = tool_data.get('description')
    if isinstance(desc, str):
        return desc

    # 4) Nothing available
    return ''

