#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
extract_translations.py - 从Python源文件中提取tr()调用并生成.ts文件

这个脚本解析Python源文件，提取所有self.tr("...")调用的文本，
然后生成Qt Linguist格式的.ts翻译文件。
"""

import re
import ast
from pathlib import Path
from xml.etree import ElementTree as ET
from xml.dom import minidom


PROJECT_ROOT = Path(__file__).parent.parent
SOURCE_DIRS = [
    PROJECT_ROOT / 'ui',
    PROJECT_ROOT / 'utils',
    PROJECT_ROOT / 'data',
]
TRANSLATIONS_DIR = PROJECT_ROOT / 'translations' / 'source'
# 只支持中文和英文
LANGUAGES = ['zh_CN', 'en_US']


def extract_tr_strings(file_path):
    """从Python文件中提取所有tr()字符串"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 匹配 self.tr("...") 和 self.tr('...')
        pattern = r'self\.tr\([\'"](.+?)[\'"]\)'
        matches = re.findall(pattern, content, re.MULTILINE | re.DOTALL)

        # 去重并保留顺序
        unique_strings = []
        seen = set()
        for match in matches:
            # 处理转义字符
            match = match.replace('\\"', '"').replace("\\'", "'")
            if match not in seen:
                seen.add(match)
                unique_strings.append(match)

        return unique_strings
    except Exception as e:
        print(f"  ✗ 读取文件失败: {file_path.name} - {e}")
        return []


def find_all_python_files():
    """查找所有Python源文件"""
    python_files = []

    for source_dir in SOURCE_DIRS:
        if source_dir.exists():
            python_files.extend(source_dir.rglob('*.py'))

    # 添加main.py
    main_py = PROJECT_ROOT / 'main.py'
    if main_py.exists():
        python_files.append(main_py)

    return python_files


def get_class_name(file_path):
    """从文件中提取类名作为context"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 匹配类定义
        class_match = re.search(r'class\s+(\w+)', content)
        if class_match:
            return class_match.group(1)

        # 如果没有类，使用文件名
        return file_path.stem
    except:
        return file_path.stem


def create_ts_file(language_code, translations_dict):
    """创建.ts翻译文件"""
    # 创建XML根元素
    ts = ET.Element('TS')
    ts.set('version', '2.1')
    ts.set('language', language_code)

    # 按context(类名)分组
    for context_name, messages in sorted(translations_dict.items()):
        context = ET.SubElement(ts, 'context')
        name_elem = ET.SubElement(context, 'name')
        name_elem.text = context_name

        for source_text in sorted(set(messages)):
            message = ET.SubElement(context, 'message')

            source = ET.SubElement(message, 'source')
            source.text = source_text

            translation = ET.SubElement(message, 'translation')
            # zh_CN使用原文，其他语言留空等待翻译
            if language_code == 'zh_CN':
                translation.text = source_text
            else:
                translation.set('type', 'unfinished')

    # 美化XML
    xml_str = ET.tostring(ts, encoding='utf-8')
    dom = minidom.parseString(xml_str)
    pretty_xml = dom.toprettyxml(indent='  ', encoding='utf-8')

    # 移除多余的空行
    lines = pretty_xml.decode('utf-8').split('\n')
    lines = [line for line in lines if line.strip()]

    return '\n'.join(lines)


def main():
    print("=" * 60)
    print("BioNexus 翻译提取工具")
    print("=" * 60)

    # 确保输出目录存在
    TRANSLATIONS_DIR.mkdir(parents=True, exist_ok=True)

    # 查找所有Python文件
    python_files = find_all_python_files()
    print(f"\n找到 {len(python_files)} 个Python源文件\n")

    # 提取所有翻译字符串
    translations_dict = {}  # {context: [strings]}
    total_strings = 0

    for py_file in python_files:
        strings = extract_tr_strings(py_file)
        if strings:
            context_name = get_class_name(py_file)
            if context_name not in translations_dict:
                translations_dict[context_name] = []
            translations_dict[context_name].extend(strings)
            total_strings += len(strings)
            print(f"  ✓ {py_file.name}: {len(strings)} 个字符串")

    print(f"\n总计提取: {total_strings} 个可翻译字符串")
    print(f"分布在: {len(translations_dict)} 个上下文中\n")

    # 为每种语言生成.ts文件
    for lang in LANGUAGES:
        ts_file = TRANSLATIONS_DIR / f"bionexus_{lang}.ts"
        print(f"正在生成: {ts_file.name}")

        try:
            xml_content = create_ts_file(lang, translations_dict)
            with open(ts_file, 'w', encoding='utf-8') as f:
                f.write(xml_content)
            print(f"  ✓ 生成成功\n")
        except Exception as e:
            print(f"  ✗ 生成失败: {e}\n")

    print("=" * 60)
    print("翻译文件生成完成!")
    print(f"翻译文件位置: {TRANSLATIONS_DIR}")
    print("\n下一步:")
    print("  1. 编辑 bionexus_en_US.ts 添加英文翻译")
    print("  2. 运行 compile_translations.py 编译为.qm文件")
    print("=" * 60)


if __name__ == '__main__':
    main()
