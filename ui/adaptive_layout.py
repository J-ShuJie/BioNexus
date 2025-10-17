#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能自适应布局管理器
自动识别最优布局方案，无需定义固定断点
基于内容尺寸和可用空间动态计算
"""

from PyQt5.QtWidgets import QLayout, QWidget, QSizePolicy, QVBoxLayout, QHBoxLayout, QWidgetItem
from PyQt5.QtCore import QRect, QSize, Qt, QPoint
from typing import List, Tuple, Optional


class AdaptiveFlowLayout(QLayout):
    """
    自适应流式布局
    自动计算最优列数和行数，支持自动换行
    """
    
    def __init__(self, parent=None, margin=0, spacing=10):
        super().__init__(parent)
        self.setContentsMargins(margin, margin, margin, margin)
        self.setSpacing(spacing)
        self.item_list: List = []
        
    def addItem(self, item):
        """添加布局项"""
        self.item_list.append(item)
        
    def addWidget(self, widget: QWidget):
        """添加组件"""
        self.addChildWidget(widget)
        self.addItem(QWidgetItem(widget))
        
    def count(self) -> int:
        """返回项目数量"""
        return len(self.item_list)
        
    def itemAt(self, index: int):
        """获取指定索引的项目"""
        if 0 <= index < len(self.item_list):
            return self.item_list[index]
        return None
        
    def takeAt(self, index: int):
        """移除并返回指定索引的项目"""
        if 0 <= index < len(self.item_list):
            return self.item_list.pop(index)
        return None
        
    def expandingDirections(self) -> Qt.Orientations:
        """返回扩展方向"""
        return Qt.Horizontal
        
    def hasHeightForWidth(self) -> bool:
        """支持基于宽度的高度计算"""
        return True
        
    def heightForWidth(self, width: int) -> int:
        """根据宽度计算高度"""
        return self._calculate_layout(QRect(0, 0, width, 0), True)[1]
        
    def setGeometry(self, rect: QRect):
        """设置几何尺寸"""
        super().setGeometry(rect)
        self._calculate_layout(rect, False)
        
    def sizeHint(self) -> QSize:
        """返回建议尺寸"""
        return self.minimumSize()
        
    def minimumSize(self) -> QSize:
        """返回最小尺寸"""
        size = QSize()
        for item in self.item_list:
            item_size = item.minimumSize()
            size = size.expandedTo(item_size)
        
        margin = self.contentsMargins()
        size += QSize(margin.left() + margin.right(), margin.top() + margin.bottom())
        return size
        
    def _calculate_optimal_columns(self, available_width: int) -> int:
        """自动计算最优列数"""
        if not self.item_list:
            return 1
            
        # 获取单个项目的平均宽度
        total_width = sum(item.sizeHint().width() for item in self.item_list)
        avg_item_width = total_width / len(self.item_list)
        
        # 计算理论最大列数
        spacing = self.spacing()
        max_cols = max(1, (available_width + spacing) // int(avg_item_width + spacing))
        
        # 限制在合理范围内
        return min(max_cols, len(self.item_list), 6)  # 最多6列
        
    def _calculate_layout(self, rect: QRect, test_only: bool = False) -> Tuple[int, int]:
        """计算并应用布局"""
        if not self.item_list:
            return rect.width(), rect.height()
            
        margin = self.contentsMargins()
        available_rect = rect.adjusted(margin.left(), margin.top(), -margin.right(), -margin.bottom())
        
        # 自动计算最优列数
        cols = self._calculate_optimal_columns(available_rect.width())
        
        x = available_rect.x()
        y = available_rect.y()
        line_height = 0
        current_col = 0
        
        for i, item in enumerate(self.item_list):
            item_size = item.sizeHint()
            
            # 检查是否需要换行
            if current_col >= cols and cols > 1:
                x = available_rect.x()
                y += line_height + self.spacing()
                line_height = 0
                current_col = 0
                
            # 检查宽度是否超出（动态调整）
            next_x = x + item_size.width()
            if next_x > available_rect.right() and current_col > 0:
                x = available_rect.x()
                y += line_height + self.spacing()
                line_height = 0
                current_col = 0
                
            if not test_only:
                item.setGeometry(QRect(QPoint(x, y), item_size))
                
            x += item_size.width() + self.spacing()
            line_height = max(line_height, item_size.height())
            current_col += 1
            
        return rect.width(), y + line_height - rect.y()


class SmartResponsiveContainer(QWidget):
    """
    智能响应式容器
    自动在水平和垂直布局之间切换
    """
    
    def __init__(self, main_widget: QWidget, sidebar_widget: QWidget, parent=None):
        super().__init__(parent)
        
        self.main_widget = main_widget
        self.sidebar_widget = sidebar_widget
        
        # 布局状态
        self.current_layout = None
        self.is_vertical_layout = False
        
        # 初始化为水平布局
        self._setup_horizontal_layout()
        
    def _setup_horizontal_layout(self):
        """设置水平布局"""
        if self.current_layout:
            self.current_layout.removeWidget(self.main_widget)
            self.current_layout.removeWidget(self.sidebar_widget)
            self.current_layout.deleteLater()
            
        self.current_layout = QHBoxLayout(self)
        self.current_layout.setContentsMargins(0, 0, 0, 0)
        self.current_layout.setSpacing(20)
        
        # 主内容区占据更多空间
        self.current_layout.addWidget(self.main_widget, 3)
        self.current_layout.addWidget(self.sidebar_widget, 1)
        
        # 设置侧边栏固定宽度
        self.sidebar_widget.setFixedWidth(240)
        self.sidebar_widget.setMaximumWidth(240)
        
        self.is_vertical_layout = False
        
    def _setup_vertical_layout(self):
        """设置垂直布局"""
        if self.current_layout:
            self.current_layout.removeWidget(self.main_widget)
            self.current_layout.removeWidget(self.sidebar_widget)
            self.current_layout.deleteLater()
            
        self.current_layout = QVBoxLayout(self)
        self.current_layout.setContentsMargins(0, 0, 0, 0)
        self.current_layout.setSpacing(20)
        
        # 主内容在上，侧边栏在下
        self.current_layout.addWidget(self.main_widget, 0)  # 不拉伸，保持内容高度
        self.current_layout.addWidget(self.sidebar_widget, 0)  # 不拉伸，保持侧边栏高度
        
        # 侧边栏占满宽度
        self.sidebar_widget.setMaximumWidth(16777215)
        self.sidebar_widget.setMinimumWidth(200)
        
        # 确保容器本身可以扩展
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.MinimumExpanding)
        
        self.is_vertical_layout = True
        
    def _calculate_optimal_layout(self) -> bool:
        """计算最优布局方式"""
        available_width = self.width()
        
        # 获取主内容和侧边栏的最小宽度需求
        main_min_width = self.main_widget.minimumWidth() or 400
        sidebar_min_width = 240
        spacing = 20
        
        # 计算水平布局所需的最小宽度
        horizontal_min_width = main_min_width + sidebar_min_width + spacing
        
        # 如果可用宽度不足，使用垂直布局
        return available_width < horizontal_min_width
        
    def update_layout(self):
        """更新布局"""
        should_be_vertical = self._calculate_optimal_layout()
        
        if should_be_vertical != self.is_vertical_layout:
            if should_be_vertical:
                self._setup_vertical_layout()
            else:
                self._setup_horizontal_layout()
                
            # 布局改变后强制更新几何尺寸
            self.updateGeometry()
            if self.parent():
                self.parent().updateGeometry()
                
    def resizeEvent(self, event):
        """窗口大小改变事件"""
        super().resizeEvent(event)
        # 延迟更新布局，避免频繁切换
        from PyQt5.QtCore import QTimer
        QTimer.singleShot(10, self.update_layout)


class AdaptiveStatsBar(QWidget):
    """
    自适应统计信息栏
    自动调整卡片排列方式
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 动态高度，不设固定最小高度
        self.stat_cards = []
        
        # 使用自适应流式布局
        self.layout = AdaptiveFlowLayout(self, margin=0, spacing=15)
        self.layout.setContentsMargins(0, 10, 0, 10)
        
        # 设置尺寸策略：宽度扩展，高度适应内容
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.MinimumExpanding)
        
    def add_stat_card(self, card: QWidget):
        """添加统计卡片"""
        self.stat_cards.append(card)
        self.layout.addWidget(card)
        
    def clear_cards(self):
        """清空所有卡片"""
        for card in self.stat_cards:
            card.deleteLater()
        self.stat_cards.clear()
        
    def update_layout_and_size(self):
        """更新布局和尺寸"""
        if not self.stat_cards:
            return
            
        # 让布局重新计算
        self.layout.invalidate()
        self.updateGeometry()
        
        # 触发父组件更新
        if self.parent():
            self.parent().updateGeometry()
                
    def resizeEvent(self, event):
        """窗口大小改变事件"""
        super().resizeEvent(event)
        # 延迟更新，确保布局稳定
        from PyQt5.QtCore import QTimer
        QTimer.singleShot(0, self.update_layout_and_size)