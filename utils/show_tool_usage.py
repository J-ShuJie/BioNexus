#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
显示工具使用时间统计
"""
import sys
from pathlib import Path

project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from data.config import ConfigManager

config_mgr = ConfigManager()
tools = config_mgr.tools

print("=" * 60)
print("当前工具使用时间统计")
print("=" * 60)
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
