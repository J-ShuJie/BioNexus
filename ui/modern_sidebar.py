"""
现代化侧边栏组件 - 基于 paintEvent 自绘实现
===============================================
采用 macOS Big Sur 风格的现代化设计
- 微妙渐变背景
- 圆角按钮和毛玻璃效果  
- 平滑动画过渡
- 图标 + 文字的组合设计
- 完全自绘，高性能渲染
"""

from PyQt5.QtWidgets import QWidget, QLineEdit, QVBoxLayout
from PyQt5.QtCore import Qt, pyqtSignal, QRect, QRectF, QPoint, QPropertyAnimation, QEasingCurve, pyqtProperty, QTimer
from PyQt5.QtGui import (
    QPainter, QLinearGradient, QColor, QBrush, QPen, 
    QFont, QFontMetrics, QPainterPath, QPolygon
)
import math

class ModernSidebar(QWidget):
    """
    现代化侧边栏主组件
    基于 paintEvent 完全自绘，实现 macOS Big Sur 风格
    """
    
    # 信号定义
    search_changed = pyqtSignal(str)        # 搜索内容变化
    view_changed = pyqtSignal(str)          # 视图切换
    recent_tool_clicked = pyqtSignal(str)   # 最近工具点击
    
    def __init__(self, parent=None):
        super().__init__(parent)

        # 状态变量
        self.current_view = "all-tools"
        self.recent_tools = []
        self.hover_item = None
        self.animation_progress = 0.0

        # 布局区域
        self.search_rect = QRect()
        self.nav_rects = {}  # view_name -> QRect
        self.recent_rects = {}  # tool_name -> QRect

        # 颜色主题
        self.colors = {
            'bg_start': QColor(250, 251, 252),      # #fafbfc
            'bg_end': QColor(241, 245, 249),        # #f1f5f9
            'button_normal': QColor(255, 255, 255, 180),  # 半透明白
            'button_hover': QColor(59, 130, 246, 25),     # 淡蓝悬停
            'button_active': QColor(59, 130, 246),        # 蓝色激活
            'text_primary': QColor(30, 41, 59),           # #1e293b
            'text_secondary': QColor(100, 116, 139),      # #64748b
            'border': QColor(226, 232, 240),              # #e2e8f0
            'status_installed': QColor(16, 185, 129),     # #10b981
            'status_available': QColor(245, 158, 11),     # #f59e0b
        }

        # 动画设置
        self.hover_animation = QPropertyAnimation(self, b"animationProgress")
        self.hover_animation.setDuration(200)
        self.hover_animation.setEasingCurve(QEasingCurve.OutCubic)

        self._setup_widget()
        self._create_search_input()

        # Connect to language change signal
        self._connect_language_change()
    
    def _setup_widget(self):
        """设置控件属性"""
        self.setFixedWidth(250)
        self.setMouseTracking(True)  # 启用鼠标跟踪
        self.setAttribute(Qt.WA_StyledBackground, True)
        
        # 设置最小高度
        self.setMinimumHeight(600)
    
    def _create_search_input(self):
        """创建搜索输入框（仍使用 QLineEdit，但样式通过 paintEvent 绘制）"""
        self.search_input = QLineEdit(self)
        self.search_input.setPlaceholderText(self.tr("Search bioinformatics tools..."))
        
        # 设置透明背景，我们通过 paintEvent 绘制外观
        self.search_input.setStyleSheet("""
            QLineEdit {
                background: transparent;
                border: none;
                color: #1e293b;
                font-size: 12px;
                padding-left: 30px;  /* 为图标留出空间 */
                selection-background-color: #3b82f6;
            }
        """)
        
        # 连接信号
        self.search_input.textChanged.connect(self.search_changed.emit)
        
        # 初始位置设置（在 resizeEvent 中会重新调整）
        self.search_input.setGeometry(15, 20, 220, 32)
    
    @pyqtProperty(float)
    def animationProgress(self):
        return self.animation_progress
    
    @animationProgress.setter
    def animationProgress(self, value):
        self.animation_progress = value
        self.update()  # 触发重绘
    
    def paintEvent(self, event):
        """主绘制方法"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 绘制背景渐变
        self._draw_background(painter)
        
        # 绘制搜索框
        self._draw_search_box(painter)
        
        # 绘制导航菜单
        self._draw_navigation(painter)
        
        # 绘制最近使用工具
        self._draw_recent_tools(painter)
    
    def _draw_background(self, painter):
        """绘制渐变背景"""
        gradient = QLinearGradient(0, 0, 0, self.height())
        gradient.setColorAt(0, self.colors['bg_start'])
        gradient.setColorAt(1, self.colors['bg_end'])
        
        painter.fillRect(self.rect(), QBrush(gradient))
        
        # 绘制右边框
        pen = QPen(self.colors['border'])
        pen.setWidth(1)
        painter.setPen(pen)
        painter.drawLine(self.width() - 1, 0, self.width() - 1, self.height())
    
    def _draw_search_box(self, painter):
        """绘制搜索框外观"""
        search_rect = QRect(15, 20, 220, 32)
        self.search_rect = search_rect
        
        # 绘制背景
        path = QPainterPath()
        path.addRoundedRect(QRectF(search_rect), 16, 16)  # 圆角搜索框
        
        # 白色背景 + 微妙阴影效果
        painter.fillPath(path, QBrush(QColor(255, 255, 255, 200)))
        
        # 绘制边框（聚焦时变蓝色）
        is_focused = self.search_input.hasFocus()
        border_color = self.colors['button_active'] if is_focused else self.colors['border']
        pen = QPen(border_color)
        pen.setWidth(2 if is_focused else 1)
        painter.setPen(pen)
        painter.drawPath(path)
        
        # 绘制搜索图标
        self._draw_search_icon(painter, search_rect)
    
    def _draw_search_icon(self, painter, search_rect):
        """绘制搜索图标"""
        icon_size = 14
        icon_x = search_rect.x() + 10
        icon_y = search_rect.y() + (search_rect.height() - icon_size) // 2
        
        painter.setPen(QPen(self.colors['text_secondary'], 1.5))
        painter.setBrush(Qt.NoBrush)
        
        # 绘制放大镜
        circle_rect = QRect(icon_x, icon_y, 8, 8)
        painter.drawEllipse(circle_rect)
        
        # 绘制手柄
        painter.drawLine(icon_x + 6, icon_y + 6, icon_x + 10, icon_y + 10)
    
    def _draw_navigation(self, painter):
        """绘制导航菜单"""
        nav_items = [
            ("all-tools", "📋", self.tr("All Tools")),
            ("my-tools", "⭐", self.tr("My Tools")),
            ("settings", "⚙️", self.tr("Settings"))
        ]
        
        y_offset = 70  # 搜索框下方
        self.nav_rects.clear()
        
        for i, (view_name, icon, text) in enumerate(nav_items):
            item_rect = QRect(15, y_offset + i * 40, 220, 32)
            self.nav_rects[view_name] = item_rect
            
            # 判断状态
            is_active = view_name == self.current_view
            is_hover = self.hover_item == view_name
            
            self._draw_nav_button(painter, item_rect, icon, text, is_active, is_hover)
    
    def _draw_nav_button(self, painter, rect, icon, text, is_active, is_hover):
        """绘制单个导航按钮"""
        # 创建圆角路径
        path = QPainterPath()
        path.addRoundedRect(QRectF(rect), 8, 8)
        
        # 背景颜色
        if is_active:
            bg_color = self.colors['button_active']
        elif is_hover:
            bg_color = self.colors['button_hover']
        else:
            bg_color = QColor(0, 0, 0, 0)  # 透明
        
        # 动画效果
        if is_hover and not is_active:
            opacity = int(25 + self.animation_progress * 30)  # 25-55 的透明度变化
            bg_color.setAlpha(opacity)
        
        painter.fillPath(path, QBrush(bg_color))
        
        # 绘制图标和文字
        font = QFont()
        font.setPointSize(11)
        font.setWeight(QFont.Medium)
        painter.setFont(font)
        
        text_color = QColor(255, 255, 255) if is_active else self.colors['text_primary']
        painter.setPen(QPen(text_color))
        
        # 图标位置
        icon_x = rect.x() + 12
        icon_y = rect.y() + (rect.height() - 16) // 2
        
        # 绘制 emoji 图标
        icon_font = QFont()
        icon_font.setPointSize(13)
        painter.setFont(icon_font)
        painter.drawText(icon_x, icon_y + 12, icon)
        
        # 绘制文字
        painter.setFont(font)
        text_x = icon_x + 24
        text_y = rect.y() + (rect.height() + QFontMetrics(font).height()) // 2 - 1
        painter.drawText(text_x, text_y, text)
    
    def _draw_recent_tools(self, painter):
        """绘制最近使用工具区域"""
        if not self.recent_tools:
            return
        
        # 分割线
        separator_y = 205
        painter.setPen(QPen(self.colors['border'], 1))
        painter.drawLine(15, separator_y, 235, separator_y)
        
        # 标题
        title_y = separator_y + 20
        font = QFont()
        font.setPointSize(10)
        font.setWeight(QFont.DemiBold)
        painter.setFont(font)
        painter.setPen(QPen(self.colors['text_secondary']))
        painter.drawText(15, title_y, self.tr("🕒 Recently Used"))
        
        # 工具列表
        y_offset = title_y + 15
        self.recent_rects.clear()
        
        for i, tool_data in enumerate(self.recent_tools[:5]):  # 最多显示5个
            tool_name = tool_data.get('name', '') if isinstance(tool_data, dict) else tool_data
            is_installed = tool_data.get('installed', True) if isinstance(tool_data, dict) else True
            
            item_rect = QRect(15, y_offset + i * 28, 220, 24)
            self.recent_rects[tool_name] = item_rect
            
            is_hover = self.hover_item == f"recent_{tool_name}"
            self._draw_recent_item(painter, item_rect, tool_name, is_installed, is_hover)
    
    def _draw_recent_item(self, painter, rect, tool_name, is_installed, is_hover):
        """绘制单个最近使用工具项"""
        if is_hover:
            # 悬停背景
            path = QPainterPath()
            path.addRoundedRect(QRectF(rect), 4, 4)
            hover_color = QColor(self.colors['button_hover'])
            hover_color.setAlpha(50)
            painter.fillPath(path, QBrush(hover_color))
        
        # 工具名称
        font = QFont()
        font.setPointSize(10)
        painter.setFont(font)
        painter.setPen(QPen(self.colors['text_primary']))
        
        # 截断过长的文本
        fm = QFontMetrics(font)
        available_width = rect.width() - 25  # 为状态点预留空间
        elided_text = fm.elidedText(tool_name, Qt.ElideRight, available_width)
        
        text_y = rect.y() + (rect.height() + fm.height()) // 2 - 1
        painter.drawText(rect.x() + 8, text_y, elided_text)
        
        # 状态指示点
        dot_x = rect.right() - 12
        dot_y = rect.y() + rect.height() // 2
        dot_color = self.colors['status_installed'] if is_installed else self.colors['status_available']
        
        painter.setBrush(QBrush(dot_color))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(dot_x - 2, dot_y - 2, 4, 4)
    
    def mouseMoveEvent(self, event):
        """鼠标移动事件 - 处理悬停效果"""
        pos = event.pos()
        old_hover = self.hover_item
        new_hover = None
        
        # 检查导航按钮
        for view_name, rect in self.nav_rects.items():
            if rect.contains(pos):
                new_hover = view_name
                break
        
        # 检查最近工具
        if not new_hover:
            for tool_name, rect in self.recent_rects.items():
                if rect.contains(pos):
                    new_hover = f"recent_{tool_name}"
                    break
        
        # 更新悬停状态
        if new_hover != old_hover:
            self.hover_item = new_hover
            self._animate_hover()
            self.update()
        
        super().mouseMoveEvent(event)
    
    def mousePressEvent(self, event):
        """鼠标点击事件"""
        if event.button() != Qt.LeftButton:
            return
        
        pos = event.pos()
        
        # 检查导航按钮点击
        for view_name, rect in self.nav_rects.items():
            if rect.contains(pos):
                self.set_active_view(view_name)
                self.view_changed.emit(view_name)
                return
        
        # 检查最近工具点击
        for tool_name, rect in self.recent_rects.items():
            if rect.contains(pos):
                self.recent_tool_clicked.emit(tool_name)
                return
        
        super().mousePressEvent(event)
    
    def leaveEvent(self, event):
        """鼠标离开事件 - 清除悬停状态"""
        if self.hover_item:
            self.hover_item = None
            self.update()
        super().leaveEvent(event)
    
    def resizeEvent(self, event):
        """窗口大小变化事件 - 调整搜索框位置"""
        super().resizeEvent(event)
        if hasattr(self, 'search_input'):
            self.search_input.setGeometry(15, 20, self.width() - 30, 32)
    
    def _animate_hover(self):
        """启动悬停动画"""
        if self.hover_animation.state() == QPropertyAnimation.Running:
            self.hover_animation.stop()
        
        if self.hover_item:
            self.hover_animation.setStartValue(0.0)
            self.hover_animation.setEndValue(1.0)
        else:
            self.hover_animation.setStartValue(1.0)
            self.hover_animation.setEndValue(0.0)
        
        self.hover_animation.start()
    
    def set_active_view(self, view_name):
        """设置当前活跃视图"""
        if self.current_view != view_name:
            self.current_view = view_name
            self.update()
    
    def update_recent_tools(self, tools_data):
        """更新最近使用工具列表"""
        self.recent_tools = tools_data[:5]  # 最多保留5个
        self.update()
    
    def clear_search(self):
        """清除搜索内容"""
        self.search_input.clear()
    
    def get_search_text(self):
        """获取搜索文本"""
        return self.search_input.text()

    def _connect_language_change(self):
        """Connect to language change signal"""
        try:
            from utils.translator import get_translator
            translator = get_translator()
            translator.languageChanged.connect(self.retranslateUi)
        except Exception as e:
            print(f"Warning: Could not connect language change signal in ModernSidebar: {e}")

    def retranslateUi(self):
        """Update all translatable text - called when language changes"""
        # Update search box placeholder
        if hasattr(self, 'search_input'):
            self.search_input.setPlaceholderText(self.tr("Search bioinformatics tools..."))

        # Trigger repaint to update all painted text (nav items, recent tools title)
        self.update()