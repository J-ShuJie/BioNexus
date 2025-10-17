#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AutoResizingTextEdit - 自适应高度文本编辑器
==========================================

原项目: https://github.com/cameel/auto-resizing-text-edit
原作者: cameel
许可证: MIT License
集成日期: 2025-09-01

功能说明：
一个基于QTextEdit的PyQt5组件，能够根据文本内容自动调整高度。
特别适合需要显示动态内容且高度自适应的场景，如详情页面、说明文档等。

核心特性：
1. 高度自动适应文本内容
2. 保持字体大小固定不变
3. 支持文本自动换行
4. 与Qt布局系统完美集成
5. 可设置最小显示行数

使用方式：
```python
from vendor.auto_resizing.text_edit import AutoResizingTextEdit

# 创建自适应文本编辑器
editor = AutoResizingTextEdit()
editor.setPlainText("文本内容会自动调整组件高度")

# 设置为只读模式（常用于显示内容）
editor.setReadOnly(True)

# 可选：设置最小行数
editor.setMinimumLines(2)
```
"""

from PyQt5.QtWidgets import QTextEdit, QSizePolicy
from PyQt5.QtCore import QSize, Qt
from PyQt5.QtGui import QFontMetrics


class AutoResizingTextEdit(QTextEdit):
    """
    自适应高度的文本编辑器
    
    这个组件会根据文本内容自动调整高度，同时保持字体大小固定。
    特别适用于需要显示动态内容且要求UI美观的场景。
    
    核心原理：
    1. 重写 hasHeightForWidth() 返回 True，告诉Qt布局系统高度依赖宽度
    2. 重写 heightForWidth() 计算给定宽度下需要的准确高度
    3. 重写 sizeHint() 提供合理的默认尺寸建议
    4. 通过 textChanged 信号自动触发布局更新
    
    技术实现：
    - 使用 QTextDocument 克隆来计算高度（不影响原文档显示）
    - 考虑组件边距、内边距等因素
    - 支持设置最小行数限制
    """
    
    def __init__(self, parent=None):
        """
        初始化自适应文本编辑器
        
        Args:
            parent: 父组件
        """
        super().__init__(parent)
        
        # 设置尺寸策略：水平可扩展，垂直根据内容调整
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        
        # 连接文本变化信号，自动更新几何尺寸
        self.textChanged.connect(self.updateGeometry)
        
        # 最小行数（默认1行）
        self._minimum_lines = 1
        
        # 初始化时触发一次几何更新
        self.updateGeometry()
    
    def hasHeightForWidth(self):
        """
        告诉Qt布局系统：组件的高度依赖于宽度
        
        这是自动调整高度的关键方法。返回True后，Qt会调用heightForWidth()
        来获取特定宽度下的高度需求。
        
        Returns:
            bool: 始终返回True，启用高度宽度关联
        """
        return True
    
    def heightForWidth(self, width):
        """
        计算给定宽度下组件需要的高度
        
        这是自适应高度的核心算法：
        1. 获取组件边距
        2. 计算内容区域宽度
        3. 克隆文档并设置文本宽度
        4. 获取文档高度
        5. 加上边距得到总高度
        6. 应用最小行数限制
        
        Args:
            width (int): 组件可用宽度
            
        Returns:
            int: 需要的组件高度
        """
        # 获取组件的内容边距
        margins = self.contentsMargins()
        
        # 计算文档可用宽度（减去左右边距）
        document_width = max(width - margins.left() - margins.right(), 0)
        
        # 克隆当前文档来计算高度（避免影响原文档）
        document = self.document().clone()
        document.setTextWidth(document_width)
        
        # 计算文档高度
        document_height = document.size().height()
        
        # 计算最小高度（基于最小行数）
        font_metrics = QFontMetrics(self.font())
        line_height = font_metrics.lineSpacing()
        minimum_height = line_height * self._minimum_lines
        
        # 取文档高度和最小高度的较大值
        content_height = max(document_height, minimum_height)
        
        # 返回总高度（内容 + 上下边距）
        total_height = margins.top() + content_height + margins.bottom()
        
        return int(total_height)
    
    def sizeHint(self):
        """
        提供组件的建议尺寸
        
        Qt布局系统会使用这个方法来获取组件的理想尺寸。
        我们返回原始宽度建议，但高度使用heightForWidth计算。
        
        Returns:
            QSize: 建议的组件尺寸
        """
        # 获取父类的原始尺寸建议
        original_hint = super().sizeHint()
        
        # 使用原始宽度，但高度通过heightForWidth计算
        suggested_width = original_hint.width()
        suggested_height = self.heightForWidth(suggested_width)
        
        return QSize(suggested_width, suggested_height)
    
    def setMinimumLines(self, lines):
        """
        设置最小显示行数
        
        即使文本内容很少，组件也会保持至少指定行数的高度。
        这在UI设计中很有用，可以避免组件过小影响美观。
        
        Args:
            lines (int): 最小行数，必须大于0
        """
        if lines > 0:
            self._minimum_lines = lines
            self.updateGeometry()
    
    def minimumLines(self):
        """
        获取当前最小行数设置
        
        Returns:
            int: 最小行数
        """
        return self._minimum_lines
    
    def setPlainText(self, text):
        """
        设置纯文本内容并更新几何尺寸
        
        重写此方法确保设置文本后立即更新组件尺寸。
        
        Args:
            text (str): 要设置的文本内容
        """
        super().setPlainText(text)
        # 文本改变后立即更新几何尺寸
        self.updateGeometry()
    
    def setHtml(self, html):
        """
        设置HTML内容并更新几何尺寸
        
        重写此方法确保设置HTML后立即更新组件尺寸。
        
        Args:
            html (str): 要设置的HTML内容
        """
        super().setHtml(html)
        # 内容改变后立即更新几何尺寸
        self.updateGeometry()


# 便捷创建函数，符合BioNexus项目的命名风格
def create_auto_resizing_text_edit(text="", minimum_lines=1, read_only=False, **kwargs):
    """
    创建配置好的自适应高度文本编辑器
    
    这是一个便捷函数，用于快速创建常用配置的AutoResizingTextEdit。
    
    Args:
        text (str): 初始文本内容
        minimum_lines (int): 最小行数，默认1行
        read_only (bool): 是否只读，默认False
        **kwargs: 其他QTextEdit支持的参数
        
    Returns:
        AutoResizingTextEdit: 配置好的文本编辑器实例
        
    Example:
        ```python
        # 创建只读的内容展示区域
        content_display = create_auto_resizing_text_edit(
            text="这是工具的详细说明...",
            minimum_lines=3,
            read_only=True
        )
        
        # 创建可编辑的输入区域
        user_input = create_auto_resizing_text_edit(
            text="请输入您的配置...",
            minimum_lines=2,
            read_only=False
        )
        ```
    """
    editor = AutoResizingTextEdit(kwargs.get('parent'))
    
    # 设置基本属性
    if text:
        editor.setPlainText(text)
    
    editor.setMinimumLines(minimum_lines)
    editor.setReadOnly(read_only)
    
    # 应用其他属性
    for key, value in kwargs.items():
        if key != 'parent' and hasattr(editor, f'set{key.capitalize()}'):
            getattr(editor, f'set{key.capitalize()}')(value)
    
    return editor


# 为了保持向后兼容，提供原项目的类名
AutoResizingTextEdit.__doc__ += """

原项目信息：
- GitHub: https://github.com/cameel/auto-resizing-text-edit
- 作者: cameel
- 许可证: MIT License
- 集成时间: 2025-09-01

BioNexus集成说明：
- 添加了详细的中文注释
- 增加了便捷创建函数
- 保持了原始API的完全兼容
- 遵循了BioNexus项目的代码规范
"""