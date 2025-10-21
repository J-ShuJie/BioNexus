#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
verify_qm.py - 验证.qm文件格式

不使用GUI,直接检查.qm文件的二进制格式
"""

import struct
from pathlib import Path


PROJECT_ROOT = Path(__file__).parent.parent
TRANSLATIONS_DIR = PROJECT_ROOT / 'translations' / 'compiled'

QM_MAGIC = 0x950412de


def verify_qm_file(qm_file):
    """验证.qm文件格式"""
    print(f"\n验证: {qm_file.name}")
    print(f"  大小: {qm_file.stat().st_size} bytes")

    try:
        with open(qm_file, 'rb') as f:
            # 读取魔数
            magic_bytes = f.read(4)
            if len(magic_bytes) < 4:
                print(f"  ✗ 文件太小,无效的.qm文件")
                return False

            magic = struct.unpack('>I', magic_bytes)[0]

            if magic == QM_MAGIC:
                print(f"  ✓ 魔数正确: 0x{magic:08X}")
            else:
                print(f"  ✗ 魔数错误: 0x{magic:08X} (期望: 0x{QM_MAGIC:08X})")
                return False

            # 读取一些内容以确认文件不是空的
            content = f.read(100)
            if len(content) > 0:
                print(f"  ✓ 文件包含数据 (至少{len(content) + 4} bytes)")
            else:
                print(f"  ⚠ 警告: 文件只有魔数,没有其他数据")

            return True

    except Exception as e:
        print(f"  ✗ 读取文件失败: {e}")
        return False


def main():
    """主函数"""
    print("=" * 60)
    print(".qm文件格式验证")
    print("=" * 60)

    qm_files = list(TRANSLATIONS_DIR.glob('*.qm'))

    if not qm_files:
        print(f"\n✗ 未找到.qm文件: {TRANSLATIONS_DIR}")
        return 1

    print(f"\n找到 {len(qm_files)} 个.qm文件")

    all_valid = True
    for qm_file in sorted(qm_files):
        if not verify_qm_file(qm_file):
            all_valid = False

    print("\n" + "=" * 60)
    if all_valid:
        print("✓ 所有.qm文件格式正确!")
    else:
        print("✗ 部分.qm文件格式有问题")
    print("=" * 60)

    return 0 if all_valid else 1


if __name__ == '__main__':
    import sys
    sys.exit(main())
