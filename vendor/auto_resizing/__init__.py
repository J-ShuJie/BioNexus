"""
AutoResizingTextEdit 包
======================

基于GitHub项目 auto-resizing-text-edit 的PyQt5自适应高度文本编辑器。

功能特性：
- 根据文本内容自动调整高度
- 保持字体大小固定
- 与Qt布局系统完美集成
- 支持文本换行和滚动

使用示例：
```python
from vendor.auto_resizing import AutoResizingTextEdit

# 创建自适应文本编辑器
editor = AutoResizingTextEdit()
editor.setPlainText("这是一个会根据内容自动调整高度的文本编辑器")

# 可选：设置最小行数
editor.setMinimumLines(3)
```

原作者信息：
- 项目: https://github.com/cameel/auto-resizing-text-edit
- 作者: cameel
- 许可证: MIT License
"""

from .text_edit import AutoResizingTextEdit

__all__ = ['AutoResizingTextEdit']
__version__ = '1.0.0'  # 基于原项目master分支
__author__ = 'cameel (原作者), BioNexus Team (集成)'