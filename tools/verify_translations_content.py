#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
verify_translations_content.py - 验证翻译内容(不使用GUI)

直接读取.ts文件并统计翻译完成情况
"""

from pathlib import Path
from xml.etree import ElementTree as ET


PROJECT_ROOT = Path(__file__).parent.parent
TRANSLATIONS_DIR = PROJECT_ROOT / 'translations' / 'source'


def count_translations(ts_file):
    """统计.ts文件中的翻译情况"""
    try:
        tree = ET.parse(ts_file)
        root = tree.getroot()

        total = 0
        translated = 0
        unfinished = 0

        for message in root.findall('.//message'):
            total += 1
            translation = message.find('translation')
            if translation is not None:
                if translation.get('type') == 'unfinished':
                    unfinished += 1
                elif translation.text:
                    translated += 1

        return total, translated, unfinished
    except Exception as e:
        return 0, 0, 0


def main():
    """主函数"""
    print("=" * 60)
    print("翻译内容验证")
    print("=" * 60)

    ts_files = {
        'zh_CN': TRANSLATIONS_DIR / 'bionexus_zh_CN.ts',
        'en_US': TRANSLATIONS_DIR / 'bionexus_en_US.ts',
    }

    for lang, ts_file in ts_files.items():
        if not ts_file.exists():
            print(f"\n✗ {lang}: 文件不存在")
            continue

        total, translated, unfinished = count_translations(ts_file)

        print(f"\n{lang} ({ts_file.name}):")
        print(f"  总消息数: {total}")
        print(f"  已翻译: {translated}")
        print(f"  未完成: {unfinished}")

        if total > 0:
            percentage = (translated / total) * 100
            print(f"  完成度: {percentage:.1f}%")

            if percentage == 100:
                print(f"  ✓ 所有翻译已完成!")
            elif percentage > 0:
                print(f"  ⚠ 还有 {unfinished} 条翻译未完成")
            else:
                print(f"  ✗ 所有翻译均未完成")

    print("\n" + "=" * 60)
    print("验证完成!")
    print("=" * 60)


if __name__ == '__main__':
    main()
