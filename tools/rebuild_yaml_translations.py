#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Rebuild YAML translations with English as keys
"""

import yaml
from pathlib import Path
from xml.etree import ElementTree as ET


def extract_translations(ts_zh, ts_en):
    """Extract translations from both .ts files and create proper mapping"""
    
    # Parse Chinese .ts (source is Chinese)
    tree_zh = ET.parse(ts_zh)
    root_zh = tree_zh.getroot()
    
    # Parse English .ts (source is Chinese, translation is English)
    tree_en = ET.parse(ts_en)
    root_en = tree_en.getroot()
    
    # Build mappings: Chinese -> English
    zh_to_en = {}
    for context in root_en.findall('context'):
        context_name = context.find('name')
        if context_name is None:
            continue
        ctx = context_name.text or "general"
        
        for message in context.findall('message'):
            source = message.find('source')
            translation = message.find('translation')
            
            if source is not None and translation is not None:
                zh_text = source.text or ""
                trans_type = translation.get('type', '')
                if trans_type != 'unfinished' and translation.text:
                    en_text = translation.text
                    if zh_text and en_text:
                        zh_to_en[zh_text] = en_text
    
    print(f"Built Chinese->English mapping: {len(zh_to_en)} pairs")
    
    # Now build final translations using English as keys
    translations = {
        'en_US': {},
        'zh_CN': {},
    }
    
    for context in root_en.findall('context'):
        context_name = context.find('name')
        if context_name is None:
            continue
        ctx = context_name.text or "general"
        
        if ctx not in translations['en_US']:
            translations['en_US'][ctx] = {}
            translations['zh_CN'][ctx] = {}
        
        for message in context.findall('message'):
            source = message.find('source')
            translation = message.find('translation')
            
            if source is not None and translation is not None:
                zh_text = source.text or ""
                trans_type = translation.get('type', '')
                
                if trans_type != 'unfinished' and translation.text:
                    en_text = translation.text
                    
                    if zh_text and en_text:
                        # English key -> English value (identity)
                        translations['en_US'][ctx][en_text] = en_text
                        # English key -> Chinese value
                        translations['zh_CN'][ctx][en_text] = zh_text
    
    return translations


def main():
    PROJECT_ROOT = Path(__file__).parent.parent
    TS_DIR = PROJECT_ROOT / 'translations' / 'source'
    YAML_DIR = PROJECT_ROOT / 'translations' / 'i18n'
    
    YAML_DIR.mkdir(parents=True, exist_ok=True)
    
    print("=" * 60)
    print("Rebuilding YAML translations with English as keys")
    print("=" * 60)
    
    ts_zh = TS_DIR / 'bionexus_zh_CN.ts'
    ts_en = TS_DIR / 'bionexus_en_US.ts'
    
    if not ts_zh.exists() or not ts_en.exists():
        print("✗ Source .ts files not found")
        return
    
    # Extract translations
    translations = extract_translations(ts_zh, ts_en)
    
    # Write YAML files
    for locale, data in translations.items():
        yaml_file = YAML_DIR / f"{locale}.yaml"
        
        with open(yaml_file, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=True)
        
        count = sum(len(ctx) for ctx in data.values())
        print(f"✓ Created {yaml_file.name} with {count} translations")
    
    # Create German template (copy of English as base)
    de_data = {}
    for ctx, messages in translations['en_US'].items():
        de_data[ctx] = {}
        for en_key in messages.keys():
            # TODO: Add German translations here
            # For now, use English as placeholder
            de_data[ctx][en_key] = en_key + " [DE]"
    
    de_file = YAML_DIR / 'de_DE.yaml'
    with open(de_file, 'w', encoding='utf-8') as f:
        yaml.dump(de_data, f, allow_unicode=True, default_flow_style=False, sort_keys=True)
    
    count = sum(len(ctx) for ctx in de_data.values())
    print(f"✓ Created {de_file.name} with {count} translations (placeholders)")
    
    print("\n" + "=" * 60)
    print("YAML rebuild complete!")
    print("=" * 60)
    print("\nNOTE: German translations are placeholders '[DE]'")
    print("Please translate them manually in: translations/i18n/de_DE.yaml")


if __name__ == '__main__':
    main()
