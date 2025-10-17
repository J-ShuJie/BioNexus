#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能文本显示模块 - BioNexus 1.1.7+
=====================================

解决固定尺寸容器中的字体截断问题
保持外框固定，智能调整内部排版

核心理念：
- 外框尺寸：固定不变（保证布局稳定）
- 字体大小：设计师指定（保证一致性）
- 智能调整：内边距、行高、垂直对齐

主要用于：
1. 筛选侧边栏 - 小窗口时的字体截断问题
2. 未来扩展到工具卡片和其他组件
"""

from PyQt5.QtWidgets import QLabel, QSizePolicy
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QFontMetrics
from typing import Tuple, Dict, Any


class TextRequirements:
    """文本空间需求分析结果"""
    
    def __init__(self, width: int, height: int, line_count: int, requires_wrap: bool):
        self.width = width
        self.height = height
        self.line_count = line_count
        self.requires_wrap = requires_wrap
        self.baseline = 0  # 基线位置
        self.ascent = 0    # 上升高度
        self.descent = 0   # 下降高度


class TextDisplayOptimizer:
    """
    文本显示优化器 - 核心类
    
    解决固定尺寸容器中的字体截断问题
    智能计算最优的内边距和排版参数
    """
    
    # 预设配置 - 针对不同使用场景
    PRESETS = {
        'filter_item': {
            'font_size': 13,
            'line_height': 1.25,
            'min_padding': 2,          # 最小内边距
            'preferred_padding': 6,    # 理想内边距
            'font_family': 'Arial'
        },
        'tool_card_title': {
            'font_size': 14,
            'line_height': 1.3,
            'min_padding': 4,
            'preferred_padding': 8,
            'font_family': 'Arial'
        },
        'detail_title': {
            'font_size': 18,
            'line_height': 1.2,
            'min_padding': 6,
            'preferred_padding': 10,
            'font_family': 'Arial'
        }
    }
    
    @classmethod
    def calculate_text_requirements(cls, text: str, font_size: int, max_width: int, 
                                  font_family: str = 'Arial') -> TextRequirements:
        """
        计算文本真正需要的空间
        
        @param text: 文本内容
        @param font_size: 字体大小
        @param max_width: 最大宽度（用于计算换行）
        @param font_family: 字体族
        @return: TextRequirements 对象
        """
        font = QFont(font_family, font_size)
        metrics = QFontMetrics(font)
        
        # 计算考虑换行的实际高度
        text_rect = metrics.boundingRect(
            0, 0, max_width, 0,
            Qt.TextWordWrap, text
        )
        
        # 获取字体的基本度量信息
        ascent = metrics.ascent()    # 字符上升部分
        descent = metrics.descent()  # 字符下降部分
        leading = metrics.leading()  # 行间距
        
        # 计算行数
        line_count = max(1, text_rect.height() // metrics.height())
        
        # 实际需要的高度（包含行间距）
        actual_height = ascent + descent + (line_count - 1) * (metrics.height() + leading)
        
        requirements = TextRequirements(
            width=text_rect.width(),
            height=actual_height,
            line_count=line_count,
            requires_wrap=text_rect.width() > max_width
        )
        
        requirements.ascent = ascent
        requirements.descent = descent
        requirements.baseline = ascent
        
        return requirements
    
    @classmethod
    def optimize_padding(cls, container_height: int, text_height: int, 
                        min_padding: int = 2, preferred_padding: int = 6) -> Tuple[int, int]:
        """
        在固定容器高度下，智能分配内边距
        
        策略：
        1. 优先满足文本完整显示
        2. 尽量使用理想的内边距
        3. 空间不足时使用最小内边距
        4. 完全不足时返回0边距并警告
        
        @param container_height: 容器总高度
        @param text_height: 文本需要的高度
        @param min_padding: 最小内边距
        @param preferred_padding: 理想内边距
        @return: (top_padding, bottom_padding)
        """
        available_space = container_height - text_height
        
        if available_space >= preferred_padding * 2:
            # 空间充足：使用理想内边距
            top_padding = bottom_padding = preferred_padding
        elif available_space >= min_padding * 2:
            # 空间紧张：均分可用空间
            top_padding = bottom_padding = available_space // 2
        elif available_space >= min_padding:
            # 极度紧张：使用最小边距
            top_padding = bottom_padding = min_padding // 2
        else:
            # 空间不足：不加边距，但确保文本可见
            top_padding = bottom_padding = max(0, available_space // 2)
            
            # 记录警告（未来可以用于调试）
            if available_space < 0:
                print(f"⚠️ 警告：容器高度({container_height}px) < 文本高度({text_height}px)")
        
        return top_padding, bottom_padding
    
    @classmethod
    def create_optimized_label(cls, text: str, container_size: Tuple[int, int], 
                             preset_name: str = 'filter_item', 
                             alignment: Qt.Alignment = Qt.AlignLeft | Qt.AlignVCenter,
                             parent=None) -> 'SmartLabel':
        """
        创建优化的标签组件
        
        @param text: 文本内容
        @param container_size: (width, height) 固定容器尺寸
        @param preset_name: 预设名称
        @param alignment: 文本对齐方式
        @param parent: 父组件
        @return: SmartLabel 实例
        """
        if preset_name not in cls.PRESETS:
            raise ValueError(f"未知的预设: {preset_name}")
        
        preset = cls.PRESETS[preset_name]
        
        return SmartLabel(
            text=text,
            fixed_size=container_size,
            font_size=preset['font_size'],
            font_family=preset['font_family'],
            line_height=preset['line_height'],
            min_padding=preset['min_padding'],
            preferred_padding=preset['preferred_padding'],
            alignment=alignment,
            parent=parent
        )


class SmartLabel(QLabel):
    """
    智能标签组件
    
    特性：
    1. 保持外框固定尺寸
    2. 智能调整内部文本排版
    3. 防止字体截断
    4. 支持自动换行和垂直居中
    """
    
    def __init__(self, text: str = "", fixed_size: Tuple[int, int] = (120, 30),
                 font_size: int = 13, font_family: str = 'Arial',
                 line_height: float = 1.25, min_padding: int = 2,
                 preferred_padding: int = 6, 
                 alignment: Qt.Alignment = Qt.AlignLeft | Qt.AlignVCenter,
                 parent=None):
        super().__init__(text, parent)
        
        # 保存参数
        self.fixed_width, self.fixed_height = fixed_size
        self.font_size = font_size
        self.font_family = font_family
        self.line_height = line_height
        self.min_padding = min_padding
        self.preferred_padding = preferred_padding
        self._alignment = alignment
        
        # 固定外框尺寸（这是关键！）
        self.setFixedSize(self.fixed_width, self.fixed_height)
        
        # 基本设置
        self.setWordWrap(True)
        self.setAlignment(alignment)
        
        # 智能优化显示
        self._optimize_display()
    
    def _optimize_display(self):
        """智能优化文本显示"""
        # 1. 计算文本实际需求
        # 预留左右边距的宽度用于文本
        available_width = self.fixed_width - (self.preferred_padding * 2)
        
        text_req = TextDisplayOptimizer.calculate_text_requirements(
            text=self.text(),
            font_size=self.font_size,
            max_width=available_width,
            font_family=self.font_family
        )
        
        # 2. 优化垂直内边距
        top_pad, bottom_pad = TextDisplayOptimizer.optimize_padding(
            container_height=self.fixed_height,
            text_height=text_req.height,
            min_padding=self.min_padding,
            preferred_padding=self.preferred_padding
        )
        
        # 3. 计算水平内边距
        # 简单策略：使用理想内边距，除非文本过长
        if text_req.width > available_width:
            left_pad = right_pad = self.min_padding
        else:
            left_pad = right_pad = self.preferred_padding
        
        # 4. 生成优化的样式表
        style = f"""
            QLabel {{
                font-family: {self.font_family};
                font-size: {self.font_size}px;
                padding: {top_pad}px {right_pad}px {bottom_pad}px {left_pad}px;
                line-height: {self.line_height};
                border: none;
                background: transparent;
            }}
        """
        
        self.setStyleSheet(style)
        
        # 5. 调试信息（可在发布时移除）
        if __debug__:
            print(f"📝 SmartLabel优化: {self.text()[:20]}...")
            print(f"   容器: {self.fixed_width}x{self.fixed_height}")
            print(f"   文本需求: {text_req.width}x{text_req.height}")
            print(f"   内边距: {top_pad},{right_pad},{bottom_pad},{left_pad}")
            print(f"   行数: {text_req.line_count}")
    
    def setText(self, text: str):
        """重写setText方法，每次更改文本时重新优化"""
        super().setText(text)
        self._optimize_display()
    
    def resizeEvent(self, event):
        """处理尺寸变化事件"""
        super().resizeEvent(event)
        # 如果外框尺寸改变，重新优化
        if event.size().width() != self.fixed_width or event.size().height() != self.fixed_height:
            self.fixed_width = event.size().width()
            self.fixed_height = event.size().height()
            self._optimize_display()


# 便捷函数
def create_smart_filter_label(text: str, width: int, height: int = 32, parent=None) -> SmartLabel:
    """
    创建筛选侧边栏专用的智能标签
    
    @param text: 标签文本
    @param width: 标签宽度（通常是侧边栏宽度）
    @param height: 标签高度（默认32px）
    @param parent: 父组件
    @return: SmartLabel 实例
    """
    return TextDisplayOptimizer.create_optimized_label(
        text=text,
        container_size=(width, height),
        preset_name='filter_item',
        alignment=Qt.AlignLeft | Qt.AlignVCenter,
        parent=parent
    )


def create_smart_title_label(text: str, width: int, height: int = 40, parent=None) -> SmartLabel:
    """
    创建标题专用的智能标签
    
    @param text: 标题文本
    @param width: 标签宽度
    @param height: 标签高度（默认40px）
    @param parent: 父组件
    @return: SmartLabel 实例
    """
    return TextDisplayOptimizer.create_optimized_label(
        text=text,
        container_size=(width, height),
        preset_name='detail_title',
        alignment=Qt.AlignCenter | Qt.AlignVCenter,
        parent=parent
    )


# 模块测试函数（开发时使用）
def test_smart_label():
    """测试智能标签功能"""
    from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout
    import sys
    
    app = QApplication(sys.argv)
    window = QWidget()
    layout = QVBoxLayout(window)
    
    # 测试不同场景
    test_cases = [
        ("短文本", 200, 32),
        ("这是一个比较长的文本，需要换行显示", 150, 50),
        ("Filter Item", 120, 28),
        ("Very Long Filter Name That Needs Wrapping", 100, 40)
    ]
    
    for text, width, height in test_cases:
        label = create_smart_filter_label(text, width, height)
        label.setStyleSheet(label.styleSheet() + "border: 1px solid red;")  # 显示边界
        layout.addWidget(label)
    
    window.show()
    app.exec_()


if __name__ == "__main__":
    test_smart_label()