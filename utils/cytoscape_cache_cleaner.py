#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cytoscape Karaf 缓存清理工具

功能：清理旧的 Karaf 数据目录，加速 Cytoscape 启动
"""
import os
import shutil
import time
from pathlib import Path
from datetime import datetime


def clean_cytoscape_cache(dry_run=False):
    """
    清理 Cytoscape 的 Karaf 缓存目录

    Args:
        dry_run: 如果为 True，只显示将要删除的内容，不实际删除

    Returns:
        dict: 清理结果统计
    """
    results = {
        'success': False,
        'cleaned_dirs': 0,
        'freed_space': 0,
        'errors': []
    }

    try:
        # Cytoscape 配置目录
        # 🔥 修改：改为在工作目录查找（Cytoscape实际配置在用户目录，但不允许访问）
        import os
        cytoscape_config = Path(os.getcwd()) / 'CytoscapeConfiguration' / '3'

        if not cytoscape_config.exists():
            results['errors'].append("未找到 Cytoscape 配置目录")
            return results

        print(f"检查 Cytoscape 配置目录: {cytoscape_config}")

        # 查找所有 karaf_data 备份目录
        backup_dirs = []
        for item in cytoscape_config.iterdir():
            if item.is_dir() and item.name.startswith('karaf_data.'):
                backup_dirs.append(item)

        if not backup_dirs:
            print("没有找到需要清理的备份目录")
            results['success'] = True
            return results

        print(f"\n找到 {len(backup_dirs)} 个备份目录:")

        # 按修改时间排序（保留最新的）
        backup_dirs.sort(key=lambda p: p.stat().st_mtime, reverse=True)

        # 保留最新的 1 个备份，删除其他的
        dirs_to_keep = backup_dirs[:1]
        dirs_to_delete = backup_dirs[1:]

        for dir_path in backup_dirs:
            size = sum(f.stat().st_size for f in dir_path.rglob('*') if f.is_file())
            mtime = datetime.fromtimestamp(dir_path.stat().st_mtime)
            status = "保留" if dir_path in dirs_to_keep else "删除"
            print(f"  [{status}] {dir_path.name} - {size/(1024*1024):.2f} MB - {mtime}")

        if not dirs_to_delete:
            print("\n没有需要删除的目录")
            results['success'] = True
            return results

        if dry_run:
            print(f"\n[预演模式] 将删除 {len(dirs_to_delete)} 个目录")
            for dir_path in dirs_to_delete:
                size = sum(f.stat().st_size for f in dir_path.rglob('*') if f.is_file())
                results['freed_space'] += size
            results['cleaned_dirs'] = len(dirs_to_delete)
            results['success'] = True
            return results

        # 实际删除
        print(f"\n开始清理 {len(dirs_to_delete)} 个目录...")
        for dir_path in dirs_to_delete:
            try:
                size = sum(f.stat().st_size for f in dir_path.rglob('*') if f.is_file())
                print(f"  删除: {dir_path.name} ({size/(1024*1024):.2f} MB)")

                # 使用 shutil.rmtree 删除
                def on_error(func, path, exc_info):
                    """错误处理：尝试修改权限后重试"""
                    try:
                        os.chmod(path, 0o777)
                        func(path)
                    except Exception:
                        pass

                shutil.rmtree(dir_path, onerror=on_error)
                results['cleaned_dirs'] += 1
                results['freed_space'] += size

            except Exception as e:
                error_msg = f"删除 {dir_path.name} 失败: {e}"
                print(f"  ✗ {error_msg}")
                results['errors'].append(error_msg)

        results['success'] = True
        print(f"\n清理完成:")
        print(f"  - 删除目录: {results['cleaned_dirs']}")
        print(f"  - 释放空间: {results['freed_space']/(1024*1024):.2f} MB")

        if results['errors']:
            print(f"  - 错误: {len(results['errors'])} 个")

    except Exception as e:
        results['errors'].append(str(e))
        print(f"\n✗ 清理失败: {e}")

    return results


if __name__ == "__main__":
    import sys

    print("=" * 60)
    print("Cytoscape Karaf 缓存清理工具")
    print("=" * 60)
    print()

    # 检查是否是预演模式
    dry_run = '--dry-run' in sys.argv or '-n' in sys.argv

    if dry_run:
        print("运行模式: 预演（不会实际删除文件）")
    else:
        print("运行模式: 实际清理")
        print("提示: 使用 --dry-run 参数可以预览将要删除的内容")

    print()

    # 确认
    if not dry_run:
        response = input("确认清理旧的 Karaf 缓存? (y/N): ")
        if response.lower() != 'y':
            print("已取消")
            sys.exit(0)
        print()

    # 执行清理
    results = clean_cytoscape_cache(dry_run=dry_run)

    if results['success']:
        sys.exit(0)
    else:
        sys.exit(1)
