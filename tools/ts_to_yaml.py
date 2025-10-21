#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Convert Qt .ts files to YAML translation files
"""

import yaml
from pathlib import Path
from xml.etree import ElementTree as ET


def ts_to_yaml(ts_file, yaml_file):
    """Convert .ts XML to YAML"""
    tree = ET.parse(ts_file)
    root = tree.getroot()
    
    translations = {}
    
    for context in root.findall('context'):
        context_name_elem = context.find('name')
        if context_name_elem is None:
            continue
        
        context_name = context_name_elem.text or "general"
        
        # Create nested dict for this context
        if context_name not in translations:
            translations[context_name] = {}
        
        for message in context.findall('message'):
            source_elem = message.find('source')
            translation_elem = message.find('translation')
            
            if source_elem is None:
                continue
            
            source_text = source_elem.text or ""
            
            if translation_elem is not None:
                trans_type = translation_elem.get('type', '')
                if trans_type != 'unfinished':
                    trans_text = translation_elem.text or ""
                    if trans_text:
                        # Use source text as key, translation as value
                        translations[context_name][source_text] = trans_text
    
    # Write to YAML
    with open(yaml_file, 'w', encoding='utf-8') as f:
        yaml.dump(translations, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
    
    # Count translations
    total = sum(len(context) for context in translations.values())
    print(f"✓ Converted {ts_file.name} -> {yaml_file.name} ({total} translations)")


def main():
    PROJECT_ROOT = Path(__file__).parent.parent
    TS_DIR = PROJECT_ROOT / 'translations' / 'source'
    YAML_DIR = PROJECT_ROOT / 'translations' / 'i18n'
    
    YAML_DIR.mkdir(parents=True, exist_ok=True)
    
    print("=" * 60)
    print("Converting .ts to YAML")
    print("=" * 60)
    
    ts_files = [
        ('bionexus_zh_CN.ts', 'zh_CN.yaml'),
        ('bionexus_en_US.ts', 'en_US.yaml'),
    ]
    
    for ts_name, yaml_name in ts_files:
        ts_file = TS_DIR / ts_name
        yaml_file = YAML_DIR / yaml_name
        
        if ts_file.exists():
            ts_to_yaml(ts_file, yaml_file)
        else:
            print(f"✗ Source file not found: {ts_file}")
    
    print("\n" + "=" * 60)
    print("Conversion complete!")
    print("=" * 60)


if __name__ == '__main__':
    main()
