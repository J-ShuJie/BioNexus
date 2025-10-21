#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Recompile .ts to .qm using subprocess calls to lrelease
"""

import sys
import subprocess
from pathlib import Path


def main():
    PROJECT_ROOT = Path(__file__).parent.parent
    TS_DIR = PROJECT_ROOT / 'translations' / 'source'
    QM_DIR = PROJECT_ROOT / 'translations' / 'compiled'

    print("=" * 60)
    print("Recompiling Translation Files")
    print("=" * 60)

    QM_DIR.mkdir(parents=True, exist_ok=True)

    ts_files = [
        ('bionexus_en_US.ts', 'bionexus_en_US.qm'),
        ('bionexus_zh_CN.ts', 'bionexus_zh_CN.qm'),
    ]

    for ts_name, qm_name in ts_files:
        ts_file = TS_DIR / ts_name
        qm_file = QM_DIR / qm_name

        if not ts_file.exists():
            print(f"\n✗ Source file not found: {ts_file}")
            continue

        print(f"\nCompiling {ts_name}...")

        # Try different lrelease variants
        commands = [
            ['lrelease', str(ts_file), '-qm', str(qm_file)],
            ['lrelease-qt5', str(ts_file), '-qm', str(qm_file)],
            ['pylupdate5', str(ts_file)],  # This won't work for compilation
        ]

        success = False
        for cmd in commands[:2]:  # Only try lrelease variants
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    print(f"✓ Compiled successfully with {cmd[0]}")
                    success = True
                    break
                else:
                    print(f"  {cmd[0]} failed: {result.stderr[:100]}")
            except FileNotFoundError:
                print(f"  {cmd[0]} not found")
            except Exception as e:
                print(f"  {cmd[0]} error: {e}")

        if not success:
            print(f"✗ Failed to compile {ts_name}")
            print("  lrelease tool not available - please install qt5-tools")

    print("\n" + "=" * 60)


if __name__ == '__main__':
    main()
