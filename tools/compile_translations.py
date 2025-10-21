#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
compile_translations.py - 编译翻译文件

功能:
1. 将.ts源翻译文件编译为.qm二进制文件
2. .qm文件体积小,加载速度快
3. 自动处理所有语言

依赖: lrelease (PyQt5-tools或Qt自带)
用法: python tools/compile_translations.py
"""

import subprocess
import sys
from pathlib import Path

# 导入我们自己的.ts到.qm编译器
try:
    from ts_to_qm_compiler import QMCompiler
    HAS_CUSTOM_COMPILER = True
except ImportError:
    HAS_CUSTOM_COMPILER = False


# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent

# 翻译文件目录
TRANSLATIONS_SOURCE_DIR = PROJECT_ROOT / 'translations' / 'source'
TRANSLATIONS_COMPILED_DIR = PROJECT_ROOT / 'translations' / 'compiled'


def compile_with_lrelease(ts_file, qm_file):
    """使用lrelease命令编译"""
    cmd = [
        'lrelease',
        str(ts_file),
        '-qm', str(qm_file)
    ]

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        check=True
    )

    # lrelease输出到stderr
    stats = []
    if result.stderr:
        for line in result.stderr.split('\n'):
            if 'Generated' in line or 'Ignored' in line:
                stats.append(line.strip())
    return stats


def compile_with_custom(ts_file, qm_file):
    """使用自定义的Python编译器"""
    count = QMCompiler.compile_file(ts_file, qm_file)
    return [f"已编译 {count} 条翻译消息"]


def compile_translations():
    """编译所有.ts文件为.qm文件"""
    print("=" * 60)
    print("BioNexus 翻译文件编译工具")
    print("=" * 60)

    # 确保目录存在
    TRANSLATIONS_COMPILED_DIR.mkdir(parents=True, exist_ok=True)

    # 查找所有.ts文件
    ts_files = list(TRANSLATIONS_SOURCE_DIR.glob('*.ts'))

    if not ts_files:
        print(f"\n错误: 在 {TRANSLATIONS_SOURCE_DIR} 中没有找到.ts文件!")
        print("请先运行 update_translations.py 生成翻译文件")
        return False

    print(f"\n找到 {len(ts_files)} 个翻译文件\n")

    # 检测编译方法
    use_custom_compiler = False
    try:
        subprocess.run(['lrelease', '--version'], capture_output=True, check=True)
        print("✓ 找到lrelease命令,使用标准编译方法\n")
    except (subprocess.CalledProcessError, FileNotFoundError):
        if HAS_CUSTOM_COMPILER:
            print("⚠ 未找到lrelease命令,使用自定义Python编译器")
            print("  使用纯Python实现的.ts到.qm编译器\n")
            use_custom_compiler = True
        else:
            print("✗ 未找到lrelease命令且自定义编译器不可用")
            print("  错误: 无法导入 ts_to_qm_compiler 模块")
            return False

    # 编译每个.ts文件
    success_count = 0
    for ts_file in ts_files:
        qm_file = TRANSLATIONS_COMPILED_DIR / ts_file.with_suffix('.qm').name
        print(f"编译: {ts_file.name} -> {qm_file.name}")

        try:
            if use_custom_compiler:
                stats = compile_with_custom(ts_file, qm_file)
            else:
                stats = compile_with_lrelease(ts_file, qm_file)

            print(f"  ✓ 编译成功")
            for stat in stats:
                print(f"  {stat}")

            success_count += 1

        except subprocess.CalledProcessError as e:
            print(f"  ✗ 编译失败: {e}")
            if e.stderr:
                print(f"  错误: {e.stderr}")
        except Exception as e:
            print(f"  ✗ 错误: {e}")

        print()

    print("=" * 60)
    print(f"编译完成: {success_count}/{len(ts_files)} 成功")
    print(f"输出目录: {TRANSLATIONS_COMPILED_DIR}")
    print("\n翻译文件已就绪,可以在应用中使用!")
    print("=" * 60)

    return success_count == len(ts_files)


if __name__ == '__main__':
    success = compile_translations()
    sys.exit(0 if success else 1)
