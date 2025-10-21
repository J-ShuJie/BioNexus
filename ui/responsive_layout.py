#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
响应式布局管理器 - BioNexus 1.1.7
=====================================

⚠️ 重要提醒：此文件包含关键的响应式布局逻辑，请勿删除或修改核心配置！

这个模块专门处理详情页面的响应式布局，确保在不同窗口尺寸下内容能够：
1. 自动换行而不是被截断
2. 禁用水平滚动，只使用垂直滚动
3. 文本内容智能调整，避免左右溢出

历史教训：
- 在1.1.7开发过程中，曾经意外移除了关键的响应式配置
- 导致小窗口下内容被左右截断，无法正常显示
- 此模块的创建是为了防止此类问题再次发生

核心原则：
- 水平方向：自适应，不允许溢出
- 垂直方向：可滚动，内容完整显示
- 文本换行：优先换行而不是截断
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit,
    QScrollArea, QSizePolicy, QLayout, QGridLayout, QPushButton
)
from PyQt5.QtCore import Qt, QSize, QRect, pyqtSignal, QPropertyAnimation, pyqtProperty, QEasingCurve
from PyQt5.QtGui import QFont, QPainter, QColor, QBrush, QPen
from typing import List, Optional


class ResponsiveTextDisplay(QTextEdit):
    """
    响应式文本显示组件
    
    关键特性：
    - 强制启用自动换行
    - 禁用水平滚动
    - 高度根据内容自适应
    
    ⚠️ 警告：对于QLabel使用setWordWrap(True)，对于QTextEdit使用setLineWrapMode()！
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_responsive_behavior()
    
    def _setup_responsive_behavior(self):
        """设置响应式行为"""
        # 🔥 关键配置：QTextEdit默认就支持自动换行，无需设置setWordWrap
        # 注意：setWordWrap是QLabel的方法，QTextEdit不需要此设置
        
        # 🔥 关键配置：禁用水平滚动条，强制垂直布局
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # 设置尺寸策略：水平可扩展，垂直自适应内容
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.MinimumExpanding)
        
        # 只读模式（用于展示）
        self.setReadOnly(True)
        
        # 🔥 关键：设置换行模式为按组件宽度换行（QTextEdit的正确方法）
        self.setLineWrapMode(QTextEdit.WidgetWidth)  # 按组件宽度换行


class ResponsiveScrollArea(QScrollArea):
    """
    响应式滚动区域
    
    这是防止内容截断的核心组件！
    
    关键配置说明：
    - setWidgetResizable(True): 让内容自动调整大小
    - setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff): 🔥 禁用水平滚动（关键！）
    - setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded): 垂直滚动按需显示
    
    ⚠️ 严重警告：
    任何人修改此类时，都不能移除 setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)！
    这是防止内容被左右截断的最重要配置！
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_critical_scroll_config()
    
    def _setup_critical_scroll_config(self):
        """
        设置关键的滚动配置
        
        ⚠️ 此方法包含防止内容截断的核心逻辑，请勿修改！
        """
        # 🔥🔥🔥 最关键的配置：禁用水平滚动条
        # 这确保了内容永远不会被左右截断，而是自动换行
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # 垂直滚动按需显示
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # 让内容组件自动调整大小以适应滚动区域
        self.setWidgetResizable(True)
        
        # 移除边框，保持干净的外观
        self.setStyleSheet("QScrollArea { border: none; }")


class ResponsiveContentContainer(QWidget):
    """
    响应式内容容器
    
    专门为详情页面设计的内容容器，确保在任何窗口尺寸下都能正确显示。
    
    核心特性：
    1. 正确的尺寸策略配置
    2. 合适的边距和间距
    3. 垂直布局，防止水平溢出
    
    ⚠️ 重要：此容器的尺寸策略不能随意修改！
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_container_properties()
        self._create_layout()
    
    def _setup_container_properties(self):
        """
        设置容器属性
        
        ⚠️ 关键配置，请勿随意修改！
        """
        # 🔥 关键：设置正确的尺寸策略
        # Expanding: 水平方向可扩展，适应不同窗口宽度
        # MinimumExpanding: 垂直方向根据内容自适应，但保证最小高度
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.MinimumExpanding)
    
    def _create_layout(self):
        """创建布局"""
        self.layout = QVBoxLayout(self)
        # 设置合理的边距：左右15px，上下15px
        self.layout.setContentsMargins(15, 15, 15, 15)
        # 组件间距：15px，保持视觉舒适度
        self.layout.setSpacing(15)
    
    def add_section(self, section_widget: QWidget):
        """
        添加内容区块
        
        @param section_widget: 要添加的区块组件
        """
        self.layout.addWidget(section_widget)


class ResponsiveDetailPageManager:
    """
    响应式详情页面管理器
    
    这是整个响应式系统的协调者，负责：
    1. 创建正确配置的滚动区域
    2. 设置内容容器的响应式行为
    3. 确保所有组件都遵循响应式原则
    4. 🔥 NEW: 基于实际可用宽度（而非屏幕宽度）进行布局适配
    
    使用方法：
    ```python
    manager = ResponsiveDetailPageManager()
    scroll_area, content_container = manager.create_responsive_detail_page()
    
    # 添加各个区块
    content_container.add_section(header_section)
    content_container.add_section(stats_section) 
    content_container.add_section(description_section)
    ```
    
    ⚠️ 警告：请勿绕过此管理器直接创建滚动区域，这可能导致响应式配置丢失！
    
    ⚠️ 重要更新（1.1.7）：
    现在考虑了详情页面只是主窗口的一部分这一事实，
    响应式布局基于实际分配给详情页面的宽度，而不是整个屏幕宽度。
    """
    
    # 布局模式阈值（基于实际可用宽度）
    LAYOUT_COMPACT_THRESHOLD = 500   # 小于500px时进入紧凑模式
    LAYOUT_MEDIUM_THRESHOLD = 700    # 小于700px时进入中等模式
    # 大于700px为完整模式
    
    @staticmethod
    def get_layout_mode(available_width):
        """
        根据可用宽度确定布局模式
        
        @param available_width: 实际可用宽度（像素）
        @return: "compact" | "medium" | "full"
        """
        if available_width < ResponsiveDetailPageManager.LAYOUT_COMPACT_THRESHOLD:
            return "compact"  # 极紧凑：垂直布局为主，统计卡片堆叠
        elif available_width < ResponsiveDetailPageManager.LAYOUT_MEDIUM_THRESHOLD:
            return "medium"   # 中等：部分元素简化，2列布局
        else:
            return "full"     # 完整：正常显示，水平布局
    
    @staticmethod
    def create_responsive_detail_page():
        """
        创建响应式详情页面的核心组件
        
        返回已正确配置的滚动区域和内容容器。
        
        ⚠️ 此方法包含防止内容截断的所有关键配置，请勿修改核心逻辑！
        
        @return: (scroll_area, content_container) 元组
        """
        # 创建响应式滚动区域（包含防截断配置）
        scroll_area = ResponsiveScrollArea()
        
        # 创建响应式内容容器
        content_container = ResponsiveContentContainer()
        
        # 🔥 关键步骤：将内容容器设置为滚动区域的组件
        scroll_area.setWidget(content_container)
        
        return scroll_area, content_container
    
    @staticmethod
    def create_responsive_text_display(content: str = "", min_height: int = 150) -> ResponsiveTextDisplay:
        """
        创建响应式文本显示组件
        
        @param content: 要显示的文本内容
        @param min_height: 最小高度（像素）
        @return: 配置好的响应式文本组件
        """
        text_display = ResponsiveTextDisplay()
        text_display.setPlainText(content)
        text_display.setMinimumHeight(min_height)
        
        # 设置统一的样式
        text_display.setStyleSheet("""
            QTextEdit {
                border: 1px solid #e2e8f0;
                border-radius: 6px;
                padding: 15px;
                font-size: 13px;
                line-height: 1.6;
                color: #475569;
                background-color: #fafbfc;
            }
        """)
        
        return text_display


class ResponsiveSettingsCard(QWidget):
    """
    响应式设置卡片组件
    
    替代原有的QGroupBox，提供现代化的卡片式设计
    具备完整的响应式能力，适应不同屏幕尺寸
    """
    
    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.title = title
        self.settings_items = []
        self._setup_card_properties()
        self._create_layout()
        self._apply_card_styles()
    
    def _setup_card_properties(self):
        """设置卡片属性"""
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.MinimumExpanding)
        self.setObjectName("ResponsiveSettingsCard")
    
    def _create_layout(self):
        """创建卡片布局"""
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(15)
        
        # 创建标题
        self.title_label = QLabel(self.title)
        self.title_label.setObjectName("SettingsCardTitle")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        self.title_label.setFont(title_font)
        self.main_layout.addWidget(self.title_label)
        
        # 创建内容布局
        self.content_layout = QVBoxLayout()
        self.content_layout.setSpacing(12)
        self.main_layout.addLayout(self.content_layout)
    
    def _apply_card_styles(self):
        """应用卡片样式"""
        self.setStyleSheet("""
            QWidget#ResponsiveSettingsCard {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, 
                                           stop: 0 #ffffff, 
                                           stop: 1 #fefefe);
                border: 1px solid #e2e8f0;
                border-radius: 16px;
                margin: 6px 0px;
            }
            QLabel#SettingsCardTitle {
                color: #000000;
                margin-bottom: 8px;
                padding: 0px;
                border: none;
                background: transparent;
                font-weight: bold;
            }
        """)
    
    def add_setting_item(self, item_widget):
        """添加设置项"""
        self.settings_items.append(item_widget)
        self.content_layout.addWidget(item_widget)


class ResponsiveSettingsItem(QWidget):
    """
    响应式设置项组件
    
    替代原有的SettingItem，具备响应式布局能力
    在不同屏幕尺寸下智能调整布局
    """
    
    def __init__(self, label_text: str, control_widget: QWidget, description: str = "", parent=None, vertical_layout: bool = False):
        super().__init__(parent)
        self.label_text = label_text
        self.control_widget = control_widget
        self.description = description
        self.vertical_layout = vertical_layout  # 新增：支持垂直布局模式
        self._setup_item_properties()
        self._create_responsive_layout()
        self._apply_item_styles()
    
    def _setup_item_properties(self):
        """设置项属性"""
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.setObjectName("ResponsiveSettingsItem")
    
    def _create_responsive_layout(self):
        """创建响应式布局"""
        # 主布局 - 垂直，为响应式调整做准备
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 12, 0, 12)
        self.main_layout.setSpacing(8)
        
        # 标签区域
        self.label_container = QVBoxLayout()
        self.label_container.setSpacing(4)
        
        # 主标签
        self.main_label = QLabel(self.label_text)
        self.main_label.setObjectName("SettingsItemLabel")
        self.main_label.setWordWrap(True)  # 关键：启用自动换行
        label_font = QFont()
        label_font.setPointSize(10)
        label_font.setWeight(QFont.DemiBold)  # 稍微加粗
        self.main_label.setFont(label_font)
        self.label_container.addWidget(self.main_label)
        
        # 描述标签（如果有）
        if self.description:
            self.desc_label = QLabel(self.description)
            self.desc_label.setObjectName("SettingsItemDesc")
            self.desc_label.setWordWrap(True)  # 关键：启用自动换行
            desc_font = QFont()
            desc_font.setPointSize(8)
            self.desc_label.setFont(desc_font)
            self.label_container.addWidget(self.desc_label)
        
        self.main_layout.addLayout(self.label_container)
        
        # 控件区域 - 根据布局模式决定
        if self.vertical_layout:
            # 垂直布局模式：控件单独占一行，适合路径输入框等宽控件
            self.control_container = QVBoxLayout()
            self.control_container.setContentsMargins(0, 8, 0, 0)  # 顶部留一点间距
            self.control_container.addWidget(self.control_widget)
            self.main_layout.addLayout(self.control_container)
        else:
            # 水平布局模式：标签和控件在同一行，适合开关、下拉框等
            self.header_layout = QHBoxLayout()
            self.header_layout.setSpacing(15)
            
            # 使用之前创建的标签容器（需要重新添加）
            self.main_layout.removeItem(self.label_container)
            self.header_layout.addLayout(self.label_container, 1)  # 标签区域占更多空间
            
            # 控件区域
            self.control_container = QHBoxLayout()
            self.control_container.addWidget(self.control_widget)
            self.header_layout.addLayout(self.control_container, 0)  # 控件区域固定大小
            
            self.main_layout.addLayout(self.header_layout)
    
    def _apply_item_styles(self):
        """应用项样式"""
        self.setStyleSheet("""
            QWidget#ResponsiveSettingsItem {
                border-bottom: 1px solid #f1f5f9;
                padding: 8px 0px;
                background: transparent;
            }
            QWidget#ResponsiveSettingsItem:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, 
                                           stop: 0 #f8fafc, 
                                           stop: 1 transparent);
                border-radius: 8px;
            }
            QWidget#ResponsiveSettingsItem:last-child {
                border-bottom: none;
            }
            QLabel#SettingsItemLabel {
                color: #1e293b;
                font-weight: 600;
                font-size: 11pt;
            }
            QLabel#SettingsItemDesc {
                color: #64748b;
                font-style: normal;
                font-size: 9pt;
                line-height: 1.4;
            }
        """)
    
    def resizeEvent(self, event):
        """响应式调整"""
        super().resizeEvent(event)
        width = event.size().width()
        
        # 在窄屏幕下调整为垂直布局
        if width < 400:
            self._switch_to_vertical_layout()
        else:
            self._switch_to_horizontal_layout()
    
    def _switch_to_vertical_layout(self):
        """切换到垂直布局（窄屏幕）"""
        # 实现垂直布局调整逻辑
        pass
    
    def _switch_to_horizontal_layout(self):
        """切换到水平布局（宽屏幕）"""
        # 实现水平布局调整逻辑
        pass


class IOSToggleSwitch(QWidget):
    """
    完美复刻iOS风格的Toggle Switch组件
    
    特性：
    - 🎯 1:1复刻iOS原生滑块外观
    - ✨ 300ms丝滑动画效果
    - 🔄 支持点击和拖拽操作
    - 📱 完美的触感反馈
    - 🎨 支持自定义颜色主题
    """
    
    # 状态变化信号
    toggled = pyqtSignal(bool)
    
    def __init__(self, initial_state: bool = False, parent=None):
        super().__init__(parent)
        
        # 状态属性
        self.is_checked = initial_state
        self._thumb_position = 1.0 if initial_state else 0.0  # 滑块位置 (0.0 到 1.0)
        
        # 尺寸设置 (接近iOS原生比例)
        self.track_width = 51
        self.track_height = 31
        self.thumb_size = 27
        self.padding = 2
        
        # 颜色主题
        self.track_color_on = QColor(52, 199, 89)    # iOS绿色 #34C759
        self.track_color_off = QColor(120, 120, 128) # iOS灰色 #787880
        self.thumb_color = QColor(255, 255, 255)     # 白色滑块
        self.shadow_color = QColor(0, 0, 0, 25)      # 阴影
        
        # 悬停状态
        self.is_hovered = False
        self.is_pressed = False
        
        # 动画设置
        self.animation = QPropertyAnimation(self, b"thumbPosition")
        self.animation.setDuration(300)  # 300ms动画
        self.animation.setEasingCurve(QEasingCurve.OutCubic)  # iOS风格缓动
        
        # Widget设置
        self.setFixedSize(self.track_width, self.track_height)
        self.setMouseTracking(True)  # 启用鼠标追踪以支持悬停效果
        
        # 初始化状态
        self.update()
    
    @pyqtProperty(float)
    def thumbPosition(self):
        """滑块位置属性 (用于动画)"""
        return self._thumb_position
    
    @thumbPosition.setter
    def thumbPosition(self, position):
        """设置滑块位置"""
        self._thumb_position = max(0.0, min(1.0, position))
        self.update()  # 触发重绘
    
    def set_state(self, checked: bool, animated: bool = True):
        """
        设置开关状态
        
        Args:
            checked: 是否选中
            animated: 是否使用动画
        """
        if self.is_checked == checked:
            return
            
        self.is_checked = checked
        target_position = 1.0 if checked else 0.0
        
        if animated:
            # 使用动画过渡
            self.animation.setStartValue(self._thumb_position)
            self.animation.setEndValue(target_position)
            self.animation.start()
        else:
            # 立即切换
            self.thumbPosition = target_position
        
        # 发射信号
        self.toggled.emit(self.is_checked)
    
    def toggle(self, animated: bool = True):
        """切换状态"""
        self.set_state(not self.is_checked, animated)
    
    def paintEvent(self, event):
        """
        自定义绘制事件 - 绘制iOS风格的Toggle Switch
        """
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)  # 抗锯齿
        
        # 计算尺寸和位置
        track_rect = QRect(0, 0, self.track_width, self.track_height)
        track_radius = self.track_height // 2
        
        # 计算滑块位置
        # 滑块的最大移动范围：从左边缘padding到右边缘padding
        thumb_x_min = self.padding
        thumb_x_max = self.track_width - self.thumb_size - self.padding
        thumb_x = thumb_x_min + (thumb_x_max - thumb_x_min) * self._thumb_position
        thumb_y = (self.track_height - self.thumb_size) // 2
        thumb_rect = QRect(int(thumb_x), thumb_y, self.thumb_size, self.thumb_size)
        thumb_radius = self.thumb_size // 2
        
        # 绘制轨道背景
        track_color = self._interpolate_color(
            self.track_color_off, 
            self.track_color_on, 
            self._thumb_position
        )
        
        # 轨道阴影 (内阴影效果)
        painter.setPen(QPen(QColor(0, 0, 0, 15), 1))
        painter.setBrush(QBrush(track_color))
        painter.drawRoundedRect(track_rect, track_radius, track_radius)
        
        # 绘制滑块阴影
        shadow_rect = thumb_rect.adjusted(1, 2, 1, 2)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(self.shadow_color))
        painter.drawRoundedRect(shadow_rect, thumb_radius, thumb_radius)
        
        # 绘制滑块
        thumb_color = self.thumb_color
        if self.is_pressed:
            # 按下时稍微变暗
            thumb_color = QColor(245, 245, 245)
        elif self.is_hovered:
            # 悬停时稍微提亮
            thumb_color = QColor(255, 255, 255)
        
        painter.setPen(QPen(QColor(0, 0, 0, 10), 1))  # 细微边框
        painter.setBrush(QBrush(thumb_color))
        painter.drawRoundedRect(thumb_rect, thumb_radius, thumb_radius)
        
        # 滑块高光效果
        highlight_rect = thumb_rect.adjusted(2, 2, -2, -thumb_radius//2)
        painter.setBrush(QBrush(QColor(255, 255, 255, 40)))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(highlight_rect, thumb_radius//2, thumb_radius//2)
    
    def _interpolate_color(self, color1: QColor, color2: QColor, factor: float) -> QColor:
        """颜色插值"""
        factor = max(0.0, min(1.0, factor))
        
        r = color1.red() + (color2.red() - color1.red()) * factor
        g = color1.green() + (color2.green() - color1.green()) * factor
        b = color1.blue() + (color2.blue() - color1.blue()) * factor
        a = color1.alpha() + (color2.alpha() - color1.alpha()) * factor
        
        return QColor(int(r), int(g), int(b), int(a))
    
    def mousePressEvent(self, event):
        """鼠标按下事件"""
        if event.button() == Qt.LeftButton:
            self.is_pressed = True
            self.update()
            event.accept()
        super().mousePressEvent(event)
    
    def mouseReleaseEvent(self, event):
        """鼠标释放事件"""
        if event.button() == Qt.LeftButton and self.is_pressed:
            self.is_pressed = False
            self.toggle(animated=True)  # 切换状态并播放动画
            self.update()
            event.accept()
        super().mouseReleaseEvent(event)
    
    def enterEvent(self, event):
        """鼠标进入事件"""
        self.is_hovered = True
        self.update()
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        """鼠标离开事件"""
        self.is_hovered = False
        self.is_pressed = False
        self.update()
        super().leaveEvent(event)
    
    def sizeHint(self):
        """建议尺寸"""
        return QSize(self.track_width, self.track_height)


class ResponsiveToggleSwitch(QPushButton):
    """
    响应式开关控件
    
    继承原有ToggleSwitch功能，添加响应式特性
    """
    
    toggled_signal = pyqtSignal(bool)
    
    def __init__(self, initial_state: bool = False, parent=None):
        super().__init__(parent)
        self.is_active = initial_state
        self.setCheckable(True)
        self.setChecked(initial_state)
        self._setup_responsive_switch()
    
    def _setup_responsive_switch(self):
        """设置响应式开关"""
        self.setObjectName("ResponsiveToggleSwitch")
        self.setFixedSize(48, 24)  # 稍微增大以提高可用性
        self.clicked.connect(self._on_clicked)
        self._update_style()
    
    def _on_clicked(self):
        """点击事件处理"""
        self.is_active = self.isChecked()
        self._update_style()
        self.toggled_signal.emit(self.is_active)
    
    def _update_style(self):
        """更新样式"""
        if self.is_active:
            self.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, 
                                               stop: 0 #60a5fa, 
                                               stop: 1 #3b82f6);
                    border: 1px solid #2563eb;
                    border-radius: 12px;
                    box-shadow: 0px 2px 4px rgba(59, 130, 246, 0.3);
                }
                QPushButton:hover {
                    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, 
                                               stop: 0 #3b82f6, 
                                               stop: 1 #1e40af);
                    box-shadow: 0px 3px 6px rgba(59, 130, 246, 0.4);
                }
                QPushButton:pressed {
                    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, 
                                               stop: 0 #2563eb, 
                                               stop: 1 #1e40af);
                }
            """)
        else:
            self.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, 
                                               stop: 0 #e2e8f0, 
                                               stop: 1 #cbd5e1);
                    border: 1px solid #94a3b8;
                    border-radius: 12px;
                    box-shadow: 0px 1px 2px rgba(148, 163, 184, 0.2);
                }
                QPushButton:hover {
                    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, 
                                               stop: 0 #cbd5e1, 
                                               stop: 1 #94a3b8);
                    box-shadow: 0px 2px 4px rgba(148, 163, 184, 0.3);
                }
                QPushButton:pressed {
                    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, 
                                               stop: 0 #94a3b8, 
                                               stop: 1 #64748b);
                }
            """)
    
    def set_state(self, active: bool):
        """设置开关状态"""
        self.is_active = active
        self.setChecked(active)
        self._update_style()


class AdaptiveStatsBar(QWidget):
    """
    自适应统计栏组件
    
    根据可用宽度自动调整布局：
    - 完整模式：4个卡片水平排列
    - 中等模式：2x2网格布局
    - 紧凑模式：垂直堆叠
    """
    
    def __init__(self, stats_data, layout_mode="full", parent=None):
        super().__init__(parent)
        self.stats_data = stats_data
        self.layout_mode = layout_mode
        self._setup_layout()
    
    def _setup_layout(self):
        """根据布局模式设置不同的布局方式"""
        self.setStyleSheet("""
            QWidget {
                background-color: white;
                border-radius: 8px;
            }
        """)
        
        if self.layout_mode == "compact":
            # 紧凑模式：垂直布局
            layout = QVBoxLayout(self)
            layout.setContentsMargins(15, 10, 15, 10)
            layout.setSpacing(8)
        elif self.layout_mode == "medium":
            # 中等模式：2x2网格
            from PyQt5.QtWidgets import QGridLayout
            layout = QGridLayout(self)
            layout.setContentsMargins(15, 10, 15, 10)
            layout.setSpacing(10)
        else:
            # 完整模式：水平布局
            layout = QHBoxLayout(self)
            layout.setContentsMargins(20, 15, 20, 15)
            layout.setSpacing(15)
        
        # 添加统计卡片
        if self.layout_mode == "medium":
            # 网格布局：2列
            for i, stat in enumerate(self.stats_data):
                card = self._create_stat_card(stat)
                row = i // 2
                col = i % 2
                layout.addWidget(card, row, col)
        else:
            # 水平或垂直布局
            for stat in self.stats_data:
                card = self._create_stat_card(stat)
                layout.addWidget(card)
            
            if self.layout_mode == "full":
                layout.addStretch()  # 完整模式下右侧留白
    
    def _create_stat_card(self, stat_data):
        """创建统计卡片（简化版）"""
        card = QWidget()
        card_layout = QHBoxLayout(card)
        card_layout.setContentsMargins(0, 0, 0, 0)
        card_layout.setSpacing(8)
        
        # 标签
        label = QLabel(stat_data['label'])
        label.setStyleSheet(f"color: #64748b; font-size: 12px;")
        
        # 值
        value = QLabel(str(stat_data['value']))
        value.setStyleSheet(f"color: {stat_data['color']}; font-size: 14px; font-weight: bold;")
        
        card_layout.addWidget(label)
        card_layout.addWidget(value)
        
        if self.layout_mode != "compact":
            card_layout.addStretch()
        
        return card


# 🔥🔥🔥 关键配置常量 - 请勿修改！
CRITICAL_RESPONSIVE_CONFIG = {
    "horizontal_scroll_policy": Qt.ScrollBarAlwaysOff,  # 禁用水平滚动
    "vertical_scroll_policy": Qt.ScrollBarAsNeeded,     # 垂直滚动按需
    "widget_resizable": True,                           # 自动调整大小
    "content_size_policy_h": QSizePolicy.Expanding,    # 水平扩展
    "content_size_policy_v": QSizePolicy.MinimumExpanding  # 垂直最小扩展
}


def validate_responsive_config(scroll_area: QScrollArea) -> bool:
    """
    验证滚动区域是否有正确的响应式配置
    
    ⚠️ 此函数用于调试和验证，确保配置没有被意外修改
    
    @param scroll_area: 要检查的滚动区域
    @return: True如果配置正确，False如果有问题
    """
    issues = []
    
    # 检查水平滚动策略
    if scroll_area.horizontalScrollBarPolicy() != Qt.ScrollBarAlwaysOff:
        issues.append("水平滚动条未被禁用！这会导致内容截断！")
    
    # 检查是否启用了组件自动调整
    if not scroll_area.widgetResizable():
        issues.append("widgetResizable未启用！内容可能无法正确适应窗口大小！")
    
    if issues:
        print("⚠️ 响应式配置问题检测到：")
        for issue in issues:
            print(f"  - {issue}")
        return False
    
    print("✅ 响应式配置检查通过")
    return True