#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
重置工具使用时间统计

将所有工具的使用时间和最后使用时间清零
"""
import sys
import json
from pathlib import Path

# 确保项目根目录在 sys.path 中
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from data.config import ConfigManager


def reset_all_tool_usage():
    """重置所有工具的使用统计"""
    print("=" * 60)
    print("重置工具使用时间统计")
    print("=" * 60)

    # 初始化配置管理器
    config_mgr = ConfigManager()

    # 获取工具列表
    tools = config_mgr.tools

    print(f"\n找到 {len(tools)} 个工具")
    print("\n当前使用统计:")
    print("-" * 60)

    # 显示当前统计
    for tool in tools:
        tool_name = tool.get('name', '未知')
        total_runtime = tool.get('total_runtime', 0)
        last_used = tool.get('last_used', '从未使用')

        if total_runtime > 0:
            hours = total_runtime // 3600
            minutes = (total_runtime % 3600) // 60
            seconds = total_runtime % 60
            time_str = f"{hours}小时{minutes}分钟{seconds}秒"
        else:
            time_str = "0秒"

        print(f"  {tool_name}:")
        print(f"    - 总使用时间: {time_str} ({total_runtime}秒)")
        print(f"    - 最后使用: {last_used}")

    print("-" * 60)

    # 确认重置
    print("\n⚠️  警告：此操作将清零所有工具的使用时间统计！")
    response = input("\n确认重置? (yes/no): ").strip().lower()

    if response not in ['yes', 'y']:
        print("\n已取消")
        return False

    print("\n开始重置...")

    # 重置所有工具
    reset_count = 0
    for tool in tools:
        tool_name = tool.get('name', '未知')

        # 清零使用时间
        if 'total_runtime' in tool:
            old_runtime = tool['total_runtime']
            tool['total_runtime'] = 0
            if old_runtime > 0:
                reset_count += 1
                print(f"  ✓ 重置 {tool_name}: {old_runtime}秒 → 0秒")

        # 清除最后使用时间
        if 'last_used' in tool:
            tool['last_used'] = None

    # 保存配置
    success = config_mgr.save_tools()

    if success:
        print(f"\n✓ 成功重置 {reset_count} 个工具的使用统计")
        print(f"✓ 配置已保存到: {config_mgr.tools_file}")

        # 显示配置文件路径
        print(f"\n配置文件位置:")
        print(f"  {config_mgr.tools_file}")

        return True
    else:
        print("\n✗ 保存失败")
        return False


def show_current_stats():
    """仅显示当前统计（不重置）"""
    print("=" * 60)
    print("当前工具使用时间统计")
    print("=" * 60)

    # 初始化配置管理器
    config_mgr = ConfigManager()
    tools = config_mgr.tools

    print(f"\n找到 {len(tools)} 个工具\n")

    total_usage = 0

    for tool in tools:
        tool_name = tool.get('name', '未知')
        total_runtime = tool.get('total_runtime', 0)
        last_used = tool.get('last_used', '从未使用')

        if total_runtime > 0:
            hours = total_runtime // 3600
            minutes = (total_runtime % 3600) // 60
            time_str = f"{hours}小时{minutes}分钟"
            total_usage += total_runtime

            print(f"📊 {tool_name}:")
            print(f"   总使用: {time_str} ({total_runtime}秒)")
            print(f"   最后使用: {last_used}")
            print()

    if total_usage > 0:
        total_hours = total_usage // 3600
        total_minutes = (total_usage % 3600) // 60
        print("-" * 60)
        print(f"所有工具累计使用: {total_hours}小时{total_minutes}分钟 ({total_usage}秒)")
    else:
        print("所有工具使用时间均为0")

    print(f"\n配置文件: {config_mgr.tools_file}")


def main():
    """主函数"""
    print("\n工具使用时间管理")
    print()
    print("选择操作:")
    print("1. 查看当前统计")
    print("2. 重置所有工具使用时间")
    print()

    choice = input("请选择 (1/2): ").strip()

    if choice == '1':
        show_current_stats()
    elif choice == '2':
        reset_all_tool_usage()
    else:
        print("无效选择")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n操作已取消")
    except Exception as e:
        print(f"\n✗ 操作失败: {e}")
        import traceback
        traceback.print_exc()
