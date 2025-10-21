#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
update_translations.py - 自动更新翻译文件

功能:
1. 扫描所有Python源文件,提取tr()标记的文本
2. 更新.ts翻译文件
3. 支持增量更新(不覆盖已有翻译)

依赖: pylupdate5 (PyQt5-tools或PyQt5自带)
用法: python tools/update_translations.py
"""

import subprocess
import sys
from pathlib import Path


# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent

# 源代码目录(需要扫描的目录)
SOURCE_DIRS = [
    PROJECT_ROOT / 'ui',
    PROJECT_ROOT / 'utils',
    PROJECT_ROOT / 'data',
]

# 翻译文件输出目录
TRANSLATIONS_DIR = PROJECT_ROOT / 'translations' / 'source'

# 支持的语言 - 只支持中文和英文
LANGUAGES = ['zh_CN', 'en_US']


def find_python_files() -> list:
    """查找所有需要扫描的Python文件"""
    python_files = []

    for source_dir in SOURCE_DIRS:
        if source_dir.exists():
            python_files.extend(source_dir.rglob('*.py'))

    # 添加main.py
    main_py = PROJECT_ROOT / 'main.py'
    if main_py.exists():
        python_files.append(main_py)

    return [str(f) for f in python_files]


def update_translations():
    """更新所有翻译文件"""
    print("=" * 60)
    print("BioNexus 翻译文件更新工具")
    print("=" * 60)

    # 确保输出目录存在
    TRANSLATIONS_DIR.mkdir(parents=True, exist_ok=True)

    # 查找Python文件
    python_files = find_python_files()
    print(f"\n找到 {len(python_files)} 个Python源文件")

    if not python_files:
        print("错误: 没有找到Python源文件!")
        return False

    # 更新每个语言的.ts文件
    for lang in LANGUAGES:
        ts_file = TRANSLATIONS_DIR / f"bionexus_{lang}.ts"
        print(f"\n正在更新: {ts_file.name}")

        # 构建pylupdate5命令
        # pylupdate5会扫描源文件中的tr()调用,更新.ts文件
        cmd = [
            'pylupdate5',
            '-verbose',
            '-ts', str(ts_file),
        ] + python_files

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )

            print(f"  ✓ 更新成功")
            if result.stdout:
                print(f"  输出: {result.stdout.strip()}")

        except subprocess.CalledProcessError as e:
            print(f"  ✗ 更新失败: {e}")
            if e.stderr:
                print(f"  错误: {e.stderr}")
            return False
        except FileNotFoundError:
            print(f"  ✗ 错误: 找不到pylupdate5命令")
            print(f"  请确保已安装PyQt5: pip install PyQt5")
            return False

    print("\n" + "=" * 60)
    print("翻译文件更新完成!")
    print(f"翻译文件位置: {TRANSLATIONS_DIR}")
    print("\n下一步:")
    print("  1. 使用Qt Linguist打开.ts文件进行翻译")
    print("  2. 运行 compile_translations.py 编译为.qm文件")
    print("=" * 60)

    return True


if __name__ == '__main__':
    success = update_translations()
    sys.exit(0 if success else 1)
