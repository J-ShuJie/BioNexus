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

# Lightweight access to i18n translator without requiring PyQt
try:
    from utils.i18n import get_i18n  # type: ignore
except Exception:
    get_i18n = None  # type: ignore


_SUFFIX_BY_LOCALE = {
    'zh_CN': ('zh', 'cn', 'zh_cn', 'zh-CN'),
    'en_US': ('en', 'en_us', 'en-US'),
    'de_DE': ('de', 'de_de', 'de-DE'),
}


def _from_variant_fields(data: Dict, locale: str) -> str:
    """
    Deprecated: variant-field based lookups are no longer used.
    This function always returns an empty string to enforce YAML as the
    single source of truth for localized tool descriptions.
    """
    return ''


def get_localized_tool_description(tool_data: Dict) -> str:
    """
    Return a localized description for a tool.

    Source of truth:
    - YAML: context 'Tools', key '<tool_id>.Description' only
    """
    if not isinstance(tool_data, dict):
        return ''

    locale = current_locale() or 'zh_CN'

    # 0) YAML-based i18n lookups (single source of truth)
    #    Try multiple well-defined keys to ensure robustness across catalogs:
    #    a) Tools -> "<ToolID>.Description" (preferred)
    #    b) ToolDescriptions -> "<ToolID>"
    #    c) ToolDescriptionsBySlug -> "<slug>" where slug is lowercase alnum of ToolID
    try:
        if get_i18n is not None:
            raw_id = str(tool_data.get('id') or tool_data.get('name') or '').strip()
            if raw_id:
                # Normalize whitespace -> single spaces
                tool_id = ' '.join(raw_id.split())
                slug = ''.join(ch.lower() for ch in tool_id if ch.isalnum())
                i18n = get_i18n()

                # a) Tools/<ToolID>.Description
                key_a = f"{tool_id}.Description"
                val_a = i18n.translate(key_a, context='Tools')
                if isinstance(val_a, str) and val_a and val_a != key_a:
                    return val_a

                # b) ToolDescriptions/<ToolID>
                key_b = tool_id
                val_b = i18n.translate(key_b, context='ToolDescriptions')
                if isinstance(val_b, str) and val_b and val_b != key_b:
                    return val_b

                # c) ToolDescriptionsBySlug/<slug>
                key_c = slug
                val_c = i18n.translate(key_c, context='ToolDescriptionsBySlug')
                if isinstance(val_c, str) and val_c and val_c != key_c:
                    return val_c
    except Exception:
        # YAML lookup only; if it fails, fall through and return '' below
        pass

    # YAML is the only accepted source. If no YAML entry is found, return empty string.
    return ''
