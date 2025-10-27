#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
立即重置所有工具的使用时间（无需确认）
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
print("重置工具使用时间统计")
print("=" * 60)

print(f"\n找到 {len(tools)} 个工具")

# 重置所有工具
reset_count = 0
for tool in tools:
    tool_name = tool.get('name', '未知')

    # 清零使用时间
    if 'total_runtime' in tool:
        old_runtime = tool['total_runtime']
        tool['total_runtime'] = 0
        if old_runtime > 0:
            hours = old_runtime // 3600
            minutes = (old_runtime % 3600) // 60
            reset_count += 1
            print(f"  ✓ 重置 {tool_name}: {hours}h{minutes}m ({old_runtime}秒) → 0秒")

    # 清除最后使用时间
    if 'last_used' in tool:
        tool['last_used'] = None

# 保存配置
success = config_mgr.save_tools()

if success:
    print(f"\n✓ 成功重置 {reset_count} 个工具的使用统计")
    print(f"✓ 配置已保存到: {config_mgr.tools_file}")
else:
    print("\n✗ 保存失败")
