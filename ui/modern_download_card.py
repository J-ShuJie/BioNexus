"""
现代化下载状态悬浮卡片 - 全新精美设计
=====================================
垂直列表式下载状态显示，支持滚动和实时进度更新
采用现代化的卡片式设计，每个下载项独立显示
统一圆角、现代进度条、状态色彩系统

⚠️  铁律：禁止使用 QLabel 和 QText 系列组件！
🚫 IRON RULE: NEVER USE QLabel, QTextEdit, QTextBrowser, QPlainTextEdit
✅ 替代方案: 使用 smart_text_module.py 中的智能文本组件
📋 原因: QLabel/QText 存在文字截断、字体渲染、DPI适配等问题
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QScrollArea, QFrame, QProgressBar,
    QGraphicsDropShadowEffect, QSizePolicy
)
from PyQt5.QtCore import (
    Qt, pyqtSignal, pyqtSlot, QRect, QRectF, QPropertyAnimation, 
    QEasingCurve, pyqtProperty, QTimer, QPoint, QParallelAnimationGroup
)
from PyQt5.QtGui import (
    QPainter, QLinearGradient, QColor, QBrush, QPen,
    QFont, QFontMetrics, QPainterPath
)
from datetime import datetime
from typing import Dict, List
from collections import OrderedDict
import json
import os


class ModernProgressBar(QProgressBar):
    """
    现代化进度条 - 圆角渐变设计
    支持流畅动画和状态色彩
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(8)
        self.setTextVisible(False)
        
        # 动画属性
        self.animated_value = 0
        self.target_value = 0
        
        # 设置动画
        self.animation = QPropertyAnimation(self, b"animated_value")
        self.animation.setDuration(800)
        self.animation.setEasingCurve(QEasingCurve.OutCubic)
        self.animation.valueChanged.connect(self.update)
        
    def setValue(self, value):
        """设置值并启动动画"""
        super().setValue(value)
        self.target_value = value
        
        # 启动动画
        self.animation.setStartValue(self.animated_value)
        self.animation.setEndValue(value)
        self.animation.start()
    
    @pyqtProperty(float)
    def animated_value(self):
        return self._animated_value
    
    @animated_value.setter
    def animated_value(self, value):
        self._animated_value = value
        self.update()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._animated_value = 0
        self.setFixedHeight(8)
        self.setTextVisible(False)
        self.target_value = 0
        
        # 设置动画
        self.animation = QPropertyAnimation(self, b"animated_value")
        self.animation.setDuration(800)
        self.animation.setEasingCurve(QEasingCurve.OutCubic)
    
    def paintEvent(self, event):
        """自定义绘制 - 现代化圆角进度条"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 背景
        bg_rect = QRect(0, 2, self.width(), 4)
        painter.setBrush(QBrush(QColor(229, 231, 235)))  # #e5e7eb
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(bg_rect, 2, 2)
        
        # 进度条
        if self._animated_value > 0:
            progress_width = int(self.width() * (self._animated_value / 100.0))
            progress_rect = QRect(0, 2, progress_width, 4)
            
            # 渐变色进度条
            gradient = QLinearGradient(0, 0, progress_width, 0)
            gradient.setColorAt(0, QColor(59, 130, 246))   # #3b82f6
            gradient.setColorAt(1, QColor(29, 78, 216))    # #1d4ed8
            
            painter.setBrush(QBrush(gradient))
            painter.drawRoundedRect(progress_rect, 2, 2)


class StatusIcon(QLabel):
    """
    状态图标组件 - 支持动画和颜色变化
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(24, 24)
        self.setAlignment(Qt.AlignCenter)
        self.current_status = "downloading"
        
        # 旋转动画（用于下载状态）
        self.rotation_animation = QPropertyAnimation(self, b"rotation")
        self.rotation_animation.setDuration(2000)
        self.rotation_animation.setLoopCount(-1)  # 无限循环
        self.rotation_animation.setStartValue(0)
        self.rotation_animation.setEndValue(360)
        
        self._update_icon()
    
    def set_status(self, status):
        """设置状态"""
        if self.current_status != status:
            self.current_status = status
            self._update_icon()
    
    def _update_icon(self):
        """更新图标"""
        if self.current_status == "downloading":
            self.setText("⬇️")
            self.setStyleSheet("""
                background-color: #3b82f6;
                color: white;
                border-radius: 12px;
                font-size: 12px;
            """)
            self.rotation_animation.start()
            
        elif self.current_status == "completed":
            self.setText("✅")
            self.setStyleSheet("""
                background-color: #22c55e;
                color: white;
                border-radius: 12px;
                font-size: 12px;
            """)
            self.rotation_animation.stop()
            
        elif self.current_status == "failed":
            self.setText("❌")
            self.setStyleSheet("""
                background-color: #ef4444;
                color: white;
                border-radius: 12px;
                font-size: 12px;
            """)
            self.rotation_animation.stop()
            
        else:  # waiting
            self.setText("⏳")
            self.setStyleSheet("""
                background-color: #f59e0b;
                color: white;
                border-radius: 12px;
                font-size: 12px;
            """)
            self.rotation_animation.stop()
    
    @pyqtProperty(float)
    def rotation(self):
        return getattr(self, '_rotation', 0)
    
    @rotation.setter
    def rotation(self, value):
        self._rotation = value


class ModernDownloadItem(QWidget):
    """
    现代化单个下载任务项 - 全新卡片设计
    采用圆角卡片、现代进度条、状态图标
    """
    
    remove_requested = pyqtSignal(str)  # 请求移除项目
    
    def __init__(self, tool_name: str, parent=None):
        super().__init__(parent)
        self.tool_name = tool_name
        self.start_time = datetime.now()
        self.is_completed = False
        self.is_failed = False
        self.progress_value = 0
        
        # 解析任务类型和显示格式（多语言支持）
        # 支持识别 "(卸载)", "(Uninstall)", "(Deinstallieren)" 后缀
        uninstall_markers = [" (卸载)", " (Uninstall)", " (Deinstallieren)"]
        is_uninstall = any(m in tool_name for m in uninstall_markers)
        if is_uninstall:
            # 清理后缀，得到纯工具名
            self.clean_name = tool_name
            for m in uninstall_markers:
                self.clean_name = self.clean_name.replace(m, "")
            self.task_type = "uninstall"
            self.display_title = self.tr("Uninstall: {0}").format(self.clean_name)
        else:
            self.task_type = "install"
            self.clean_name = tool_name
            self.display_title = self.tr("Install: {0}").format(self.clean_name)
        
        print(f"🎨 [UI格式] 任务显示: {self.display_title} (原始: {tool_name})")
        
        # 颜色主题 - 现代化色彩系统
        self.colors = {
            'bg_normal': QColor(255, 255, 255),
            'bg_hover': QColor(248, 250, 252),        # #f8fafc
            'bg_completed': QColor(240, 253, 244),    # #f0fdf4 绿色背景
            'bg_failed': QColor(254, 242, 242),       # #fef2f2 红色背景
            'bg_downloading': QColor(239, 246, 255),  # #eff6ff 蓝色背景
            'text_primary': QColor(17, 24, 39),       # #111827
            'text_secondary': QColor(107, 114, 128),  # #6b7280
            'text_success': QColor(21, 128, 61),      # #15803d
            'text_error': QColor(220, 38, 38),        # #dc2626
            'text_info': QColor(59, 130, 246),        # #3b82f6
            'border': QColor(229, 231, 235),          # #e5e7eb
            'border_success': QColor(34, 197, 94),    # #22c55e
            'border_error': QColor(239, 68, 68),      # #ef4444
            'border_info': QColor(59, 130, 246),      # #3b82f6
        }
        
        self._init_ui()
        self._setup_animations()
        self.setMouseTracking(True)

        # 连接语言切换信号，支持运行时切换
        try:
            from utils.translator import get_translator
            get_translator().languageChanged.connect(self.retranslateUi)
        except Exception:
            pass
        
    def _init_ui(self):
        """初始化UI - 现代卡片设计"""
        self.setFixedHeight(90)  # 稍微增加高度容纳更多内容
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        
        # 卡片样式 - 圆角卡片 + 边框（分隔线样式已注释保留）
        self.setStyleSheet("""
            ModernDownloadItem {
                background-color: white;
                border: 1px solid #e5e7eb;
                border-radius: 8px;
                margin: 4px 2px;
                padding: 2px;
            }
            ModernDownloadItem:hover {
                background-color: #f8fafc;
                border-color: #d1d5db;
            }
        """)
        
        # 分隔线样式备用（已注释，未来可切换）
        """
        self.setStyleSheet('''
            ModernDownloadItem {
                background-color: white;
                border: none;
                border-bottom: 1px solid #e5e7eb;
                border-radius: 0px;
                margin: 0px;
                padding: 8px 0px;
            }
            ModernDownloadItem:hover {
                background-color: #f8fafc;
                border-bottom: 1px solid #d1d5db;
            }
            ModernDownloadItem:last-child {
                border-bottom: none;
            }
        ''')
        """
        
        # 主布局
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(16, 12, 16, 12)
        main_layout.setSpacing(8)
        
        # 顶部：工具名和状态图标
        top_layout = QHBoxLayout()
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(12)
        
        # 状态图标
        self.status_icon = StatusIcon()
        top_layout.addWidget(self.status_icon)
        
        # 工具信息区域
        info_layout = QVBoxLayout()
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(4)
        
        # 工具名行（包含名称和时间戳）
        name_row_layout = QHBoxLayout()
        name_row_layout.setContentsMargins(0, 0, 0, 0)
        name_row_layout.setSpacing(8)
        
        # 工具名 - 使用简洁的"安装：软件名"格式
        self.tool_label = QLabel(self.display_title)
        self.tool_label.setStyleSheet("""
            font-size: 14px;
            font-weight: 600;
            color: #111827;
        """)
        name_row_layout.addWidget(self.tool_label)
        
        # 时间戳标签（显示开始时间）
        self.timestamp_label = QLabel()
        self.timestamp_label.setStyleSheet("""
            font-size: 11px;
            color: #9ca3af;
            font-weight: 400;
        """)
        self.timestamp_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        
        # 初始显示开始时间
        self._update_timestamp_display()
        
        name_row_layout.addWidget(self.timestamp_label)
        
        info_layout.addLayout(name_row_layout)
        
        # 状态文本
        self.status_label = QLabel(self.tr("Preparing..."))
        self.status_label.setStyleSheet("""
            font-size: 12px;
            color: #6b7280;
        """)
        info_layout.addWidget(self.status_label)
        
        top_layout.addLayout(info_layout)
        top_layout.addStretch()
        
        # 操作按钮区域
        actions_layout = QHBoxLayout()
        actions_layout.setContentsMargins(0, 0, 0, 0)
        actions_layout.setSpacing(8)
        
        # 暂停/继续按钮
        self.pause_btn = QPushButton("⏸️")
        self.pause_btn.setFixedSize(28, 28)
        self.pause_btn.setStyleSheet("""
            QPushButton {
                background-color: #f3f4f6;
                border: none;
                border-radius: 14px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #e5e7eb;
            }
        """)
        actions_layout.addWidget(self.pause_btn)
        
        # 移除按钮
        self.remove_btn = QPushButton("🗑️")
        self.remove_btn.setFixedSize(28, 28)
        self.remove_btn.setStyleSheet("""
            QPushButton {
                background-color: #fef2f2;
                border: none;
                border-radius: 14px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #fee2e2;
            }
        """)
        self.remove_btn.clicked.connect(lambda: self.remove_requested.emit(self.tool_name))
        actions_layout.addWidget(self.remove_btn)
        
        top_layout.addLayout(actions_layout)
        main_layout.addLayout(top_layout)
        
        # 进度条区域
        progress_layout = QHBoxLayout()
        progress_layout.setContentsMargins(36, 0, 0, 0)  # 与状态图标对齐
        progress_layout.setSpacing(12)
        
        # 现代化进度条
        self.progress_bar = ModernProgressBar()
        progress_layout.addWidget(self.progress_bar)
        
        # 进度百分比
        self.progress_label = QLabel("0%")
        self.progress_label.setFixedWidth(40)
        self.progress_label.setStyleSheet("""
            font-size: 11px;
            color: #6b7280;
            font-weight: 500;
        """)
        self.progress_label.setAlignment(Qt.AlignRight)
        progress_layout.addWidget(self.progress_label)
        
        main_layout.addLayout(progress_layout)
        self.setLayout(main_layout)
        
    def _setup_animations(self):
        """设置动画"""
        # 状态变化动画
        self.state_animation = QPropertyAnimation(self, b"geometry")
        self.state_animation.setDuration(300)
        self.state_animation.setEasingCurve(QEasingCurve.OutCubic)
        
        # 背景色动画
        self.bg_animation = QParallelAnimationGroup()
        
    def update_progress(self, progress: int, status: str = None):
        """更新进度"""
        self.progress_value = progress
        self.progress_bar.setValue(progress)
        self.progress_label.setText(f"{progress}%")
        
        # 更新状态
        if status:
            self.update_status(status)
    
    def update_status(self, status: str):
        """更新状态"""
        self.status_label.setText(status)
        
        # 根据状态更新图标和卡片样式
        if "完成" in status or "成功" in status:
            self.is_completed = True
            self.is_failed = False
            self.status_icon.set_status("completed")
            self._update_card_appearance("completed")
            self._hide_progress_controls()  # 隐藏进度条和控制按钮
            
        elif "失败" in status or "错误" in status:
            self.is_failed = True
            self.is_completed = False
            self.status_icon.set_status("failed")
            self._update_card_appearance("failed")
            self._hide_progress_controls()  # 失败也隐藏进度控制
            
        elif "下载" in status or "安装" in status or "卸载" in status or "删除" in status or "清理" in status:
            self.is_completed = False
            self.is_failed = False
            self.status_icon.set_status("downloading")
            self._update_card_appearance("downloading")
            self._show_progress_controls()  # 显示进度控制
            
        else:
            self.status_icon.set_status("waiting")
            self._update_card_appearance("normal")
            self._show_progress_controls()  # 等待状态也显示控制
    
    def _update_card_appearance(self, state):
        """更新卡片外观"""
        # 注释掉旧的样式覆盖，使用初始化时设置的统一样式
        # 保留颜色状态变化的逻辑，但不改变边框和圆角
        pass
        
        # 旧的样式代码（已注释，避免覆盖初始样式）
        """
        if state == "completed":
            self.setStyleSheet('''
                ModernDownloadItem {
                    background-color: #f0fdf4;
                    border: 2px solid #22c55e;
                    border-radius: 12px;
                    margin: 2px;
                }
            ''')
        elif state == "failed":
            self.setStyleSheet('''
                ModernDownloadItem {
                    background-color: #fef2f2;
                    border: 2px solid #ef4444;
                    border-radius: 12px;
                    margin: 2px;
                }
            ''')
        elif state == "downloading":
            self.setStyleSheet('''
                ModernDownloadItem {
                    background-color: #eff6ff;
                    border: 2px solid #3b82f6;
                    border-radius: 12px;
                    margin: 2px;
                }
            ''')
        else:
            self.setStyleSheet('''
                ModernDownloadItem {
                    background-color: white;
                    border: 2px solid #e5e7eb;
                    border-radius: 12px;
                    margin: 2px;
                }
                ModernDownloadItem:hover {
                    border-color: #d1d5db;
                    background-color: #f8fafc;
                }
            ''')
        """
    
    def _show_progress_controls(self):
        """显示进度条和控制按钮 - 进行中的任务"""
        if hasattr(self, 'progress_bar'):
            self.progress_bar.setVisible(True)
        if hasattr(self, 'progress_label'):
            self.progress_label.setVisible(True)
        if hasattr(self, 'pause_btn'):
            self.pause_btn.setVisible(True)
    
    def _hide_progress_controls(self):
        """隐藏进度条和控制按钮 - 已完成的任务"""
        if hasattr(self, 'progress_bar'):
            self.progress_bar.setVisible(False)
        if hasattr(self, 'progress_label'):
            self.progress_label.setVisible(False)
        if hasattr(self, 'pause_btn'):
            self.pause_btn.setVisible(False)
        
        # 完成或失败时更新时间戳
        if self.is_completed or self.is_failed:
            # 记录完成时间
            if not hasattr(self, 'end_time'):
                self.end_time = datetime.now()
            self._update_timestamp_display()
    
    def mark_completed(self):
        """标记为完成"""
        self.is_completed = True
        self.progress_bar.setValue(100)
        self.progress_label.setText("100%")
        self.update_status(f"{self.task_type}完成")
        self._hide_progress_controls()  # 隐藏进度控件并显示时间戳
        
    def mark_failed(self, error_msg: str):
        """标记为失败"""
        self.is_failed = True
        self.update_status(f"{self.task_type}失败: {error_msg}")
        self._hide_progress_controls()  # 隐藏进度控件并显示时间戳
    
    def _update_timestamp_display(self):
        """更新时间戳显示 - 根据任务状态显示不同时间"""
        if self.is_completed or self.is_failed:
            # 已完成/失败：显示完成时间
            if hasattr(self, 'end_time'):
                display_time = self.end_time.strftime("%H:%M")
            else:
                # 如果没有记录结束时间，使用当前时间
                display_time = datetime.now().strftime("%H:%M")
        else:
            # 进行中：显示开始时间
            display_time = self.start_time.strftime("%H:%M")
        
        self.timestamp_label.setText(display_time)

    def retranslateUi(self, locale: str = None):
        """语言变更时，更新标题等可见文本"""
        try:
            title = (self.tr("Uninstall: {0}") if getattr(self, 'task_type', '') == 'uninstall'
                     else self.tr("Install: {0}")).format(self.clean_name)
            if hasattr(self, 'tool_label'):
                self.tool_label.setText(title)
        except Exception:
            pass


class EmptyStateWidget(QWidget):
    """
    空状态组件 - 没有下载任务时显示
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
    
    def _init_ui(self):
        """初始化空状态UI"""
        layout = QVBoxLayout()
        layout.setContentsMargins(40, 60, 40, 60)
        layout.setSpacing(16)
        layout.setAlignment(Qt.AlignCenter)
        
        # 空状态图标
        icon_label = QLabel("📥")
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setStyleSheet("""
            font-size: 48px;
            color: #d1d5db;
        """)
        layout.addWidget(icon_label)
        
        # 空状态文字
        title_label = QLabel(self.tr("No download tasks"))
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("""
            font-size: 16px;
            font-weight: 600;
            color: #6b7280;
            margin-bottom: 8px;
        """)
        layout.addWidget(title_label)
        
        desc_label = QLabel(self.tr("Download progress will appear when installing tools"))
        desc_label.setAlignment(Qt.AlignCenter)
        desc_label.setStyleSheet("""
            font-size: 14px;
            color: #9ca3af;
        """)
        layout.addWidget(desc_label)
        
        self.setLayout(layout)


class ModernDownloadCard(QWidget):
    """
    现代化下载状态悬浮卡片 - 全新精美设计
    完整圆角、现代进度条、状态色彩系统
    """
    
    card_closed = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 下载项管理 - 使用OrderedDict保持时序
        self.download_items: OrderedDict[str, ModernDownloadItem] = OrderedDict()
        self.items_layout = None
        
        # 持久化文件路径
        self.tasks_file = os.path.join(os.path.dirname(__file__), '..', 'logs', 'download_tasks.json')
        
        self._setup_widget()
        self._init_ui()
        
        # 连接语言切换
        try:
            from utils.translator import get_translator
            get_translator().languageChanged.connect(self.retranslateUi)
        except Exception:
            pass

        # 加载历史任务记录
        self._load_tasks_from_file()

    def retranslateUi(self, locale: str = None):
        """语言变更时更新可见文本"""
        try:
            if hasattr(self, 'header_title'):
                self.header_title.setText(self.tr("Download Manager"))
            if not self.download_items:
                if hasattr(self, 'status_label'):
                    self.status_label.setText(self.tr("No download tasks"))
                # 重建空态内容
                if hasattr(self, 'content_layout'):
                    self._show_empty_state()
            if hasattr(self, 'stats_label'):
                total = len(self.download_items)
                self.stats_label.setText(self.tr("Total: {0} tasks").format(total))
            for item in self.download_items.values():
                if hasattr(item, 'retranslateUi'):
                    item.retranslateUi(locale)
        except Exception:
            pass
    
    def _setup_widget(self):
        """设置控件属性"""
        # 窗口标志 - 支持圆角透明
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        
        # 优化的阴影效果
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 30))
        shadow.setOffset(0, 8)
        self.setGraphicsEffect(shadow)
        
        # 🎯 动态高度设计：宽度固定400px，高度根据内容自适应
        self.setFixedWidth(400)
        self.setMinimumHeight(200)  # 最小高度保证
        self.setMaximumHeight(600)  # 最大高度限制，防止超出屏幕
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.MinimumExpanding)
    
    def _init_ui(self):
        """初始化UI - 动态高度版本"""
        # 🎯 主布局：设置16px边距，从 paintEvent 背景边缘开始计算
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(16, 16, 16, 16)  # 🎯 真正的16px边距！
        main_layout.setSpacing(0)
        
        # 🎯 动态内容容器 - 无边距，纯内容
        self.card_widget = QWidget()
        self.card_widget.setObjectName("DownloadCard")
        # 🎯 完全透明，背景由 paintEvent 绘制
        self.card_widget.setStyleSheet("background-color: transparent;")
        
        card_layout = QVBoxLayout()
        card_layout.setContentsMargins(0, 0, 0, 0)  # 🎯 无边距，纯内容
        card_layout.setSpacing(12)  # 组件间距
        
        # 标题栏
        header = self._create_header()
        card_layout.addWidget(header)
        
        # 🎯 动态高度设计：移除分割线，统一背景
        
        # 滚动内容区域
        self.scroll_area = self._create_scroll_content()
        card_layout.addWidget(self.scroll_area)
        
        # 底部状态栏
        footer = self._create_footer()
        card_layout.addWidget(footer)
        
        self.card_widget.setLayout(card_layout)
        main_layout.addWidget(self.card_widget)
        self.setLayout(main_layout)
    
    def paintEvent(self, event):
        """🎯 绘制统一的卡片背景和圆角 - 与筛选面板一致"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 绘制圆角背景 - 现代化卡片设计
        bg_color = QColor(255, 255, 255)  # 白色背景
        border_color = QColor(229, 231, 235, 180)  # #e5e7eb 边框，半透明
        
        # 设置画笔和画刷
        painter.setPen(QPen(border_color, 1))
        painter.setBrush(QBrush(bg_color))
        
        # 绘制圆角矩形 - 整个卡片的背景，现代化圆角
        rect = self.rect().adjusted(1, 1, -1, -1)  # 调整避免边框被裁切
        painter.drawRoundedRect(rect, 12, 12)  # 12px 圆角，现代化设计
        
        # 绘制微妙的内阴影效果（可选）
        inner_shadow_color = QColor(0, 0, 0, 8)  # 极淡的内阴影
        painter.setPen(QPen(inner_shadow_color, 1))
        painter.setBrush(Qt.NoBrush)
        inner_rect = self.rect().adjusted(2, 2, -2, -2)
        painter.drawRoundedRect(inner_rect, 11, 11)
    
    def _create_header(self):
        """🎯 创建标题栏 - 动态高度版本"""
        header = QWidget()
        header.setFixedHeight(50)  # 降低高度，更紧凑
        # 🎯 完全透明，背景由 paintEvent 统一绘制
        header.setStyleSheet("background-color: transparent;")
        
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 8, 0, 8)  # 🎯 移除独立边距，由外层统一控制
        layout.setSpacing(12)
        
        # 图标
        icon_label = QLabel("⬇️")
        icon_label.setFont(QFont("", 18))
        layout.addWidget(icon_label)
        
        # 标题和描述
        title_layout = QVBoxLayout()
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(2)
        
        title = QLabel(self.tr("Download Manager"))
        title.setStyleSheet("""
            font-size: 16px;
            font-weight: 600;
            color: #111827;
        """)
        title_layout.addWidget(self.header_title)
        
        # 状态计数
        self.status_label = QLabel(self.tr("No download tasks"))
        self.status_label.setStyleSheet("""
            font-size: 12px;
            color: #6b7280;
        """)
        title_layout.addWidget(self.status_label)
        
        layout.addLayout(title_layout)
        layout.addStretch()
        
        # 关闭按钮
        close_btn = QPushButton("×")
        close_btn.setFixedSize(28, 28)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #f3f4f6;
                color: #6b7280;
                border: none;
                border-radius: 14px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e5e7eb;
                color: #374151;
            }
            QPushButton:pressed {
                background-color: #d1d5db;
            }
        """)
        close_btn.clicked.connect(self._on_close_clicked)
        layout.addWidget(close_btn)
        
        header.setLayout(layout)
        return header
    
    def _create_scroll_content(self):
        """创建滚动内容区域"""
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: white;
            }
            QScrollBar:vertical {
                border: none;
                background-color: #f8fafc;
                width: 6px;
                border-radius: 3px;
            }
            QScrollBar::handle:vertical {
                background-color: #cbd5e1;
                border-radius: 3px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #94a3b8;
            }
        """)
        
        # 滚动内容容器
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout()
        self.content_layout.setContentsMargins(12, 12, 12, 12)
        self.content_layout.setSpacing(8)
        
        # 初始显示空状态
        self._show_empty_state()
        
        self.content_widget.setLayout(self.content_layout)
        scroll_area.setWidget(self.content_widget)
        
        return scroll_area
    
    def _create_footer(self):
        """创建底部状态栏"""
        footer = QWidget()
        footer.setFixedHeight(50)
        footer.setStyleSheet("""
            background-color: #f9fafb;
            border-top: 1px solid #f3f4f6;
            border-bottom-left-radius: 12px;
            border-bottom-right-radius: 12px;
        """)
        
        layout = QHBoxLayout()
        layout.setContentsMargins(20, 12, 20, 12)
        
        # 总体统计信息
        self.stats_label = QLabel(self.tr("Total: 0 tasks"))
        self.stats_label.setStyleSheet("""
            font-size: 12px;
            color: #6b7280;
        """)
        layout.addWidget(self.stats_label)
        
        layout.addStretch()
        
        # 清空按钮
        clear_btn = QPushButton(self.tr("Clear Completed"))
        clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #f3f4f6;
                color: #6b7280;
                border: none;
                border-radius: 6px;
                padding: 6px 12px;
                font-size: 12px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #e5e7eb;
                color: #374151;
            }
        """)
        clear_btn.clicked.connect(self._clear_completed)
        layout.addWidget(clear_btn)
        
        footer.setLayout(layout)
        return footer
    
    def _show_empty_state(self):
        """显示空状态"""
        # 清除现有内容
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            if item.widget():
                item.widget().setParent(None)
        
        # 添加空状态
        empty_widget = EmptyStateWidget()
        self.content_layout.addWidget(empty_widget)
        self.content_layout.addStretch()
    
    def _show_download_list(self):
        """显示下载列表"""
        # 清除空状态
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            if item.widget():
                item.widget().setParent(None)
        
        # 添加下载项
        for item in self.download_items.values():
            self.content_layout.addWidget(item)
        
        self.content_layout.addStretch()
    
    def _generate_task_key(self, tool_name: str, status: str):
        """生成任务键 - 同一操作流程使用相同键，不同操作创建新键"""
        # 识别任务类型（多语言关键字 + 工具名后缀）
        name_markers = [" (卸载)", " (Uninstall)", " (Deinstallieren)"]
        status_keywords = [
            "卸载","删除","清理","停止",
            "Uninstall","Delete","Remove","Cleanup","Stop",
            "Deinstallieren","Löschen","Entfernen","Bereinigen","Anhalten"
        ]
        is_uninstall = any(m in tool_name for m in name_markers) or any(k in (status or '') for k in status_keywords)
        base_key = f"{tool_name} (卸载)" if is_uninstall else tool_name
        
        # 检查是否已存在相同类型的任务
        if base_key not in self.download_items:
            print(f"🆕 [任务键] 新任务类型: {base_key}")
            return base_key
        
        # 如果已存在相同类型的任务
        existing_item = self.download_items[base_key]
        if existing_item.is_completed or existing_item.is_failed:
            # 上一个任务已完成，创建新的带时间戳的任务
            timestamp = datetime.now().strftime("%H:%M")
            new_key = f"{base_key} ({timestamp})"
            print(f"🔄 [任务键] 上次任务已完成，创建新任务: {new_key}")
            return new_key
        else:
            # 上一个任务还在进行中，复用键（更新进度）
            print(f"♻️  [任务键] 复用进行中的任务: {base_key}")
            return base_key
    
    def add_or_update_download(self, tool_name: str, progress: int, status: str):
        """添加或更新下载项 - 保持时序，立即显示"""
        # 生成唯一任务键 - 避免相同工具的不同操作互相覆盖
        task_key = self._generate_task_key(tool_name, status)
        is_new_task = task_key not in self.download_items
        
        if is_new_task:
            print(f"🆕 [下载卡片] 创建新任务: {tool_name} (键: {task_key})")
            # 创建新的下载项
            item = ModernDownloadItem(tool_name)
            item.remove_requested.connect(lambda name: self._remove_download_item(task_key))
            # 存储时使用唯一键，但显示时使用原始工具名
            item.task_key = task_key  # 保存键用于删除
            self.download_items[task_key] = item
            
            # 如果是第一个项目，切换到列表视图
            if len(self.download_items) == 1:
                self._show_download_list()
            else:
                # 直接插入到列表顶部（最新的在上面）- 时序排序！
                # 移除stretch，添加新item，重新添加stretch
                if self.content_layout.count() > 0:
                    stretch_item = self.content_layout.takeAt(self.content_layout.count() - 1)
                self.content_layout.insertWidget(0, item)  # 插入到顶部
                if stretch_item:
                    self.content_layout.addItem(stretch_item)
                    
            print(f"✅ [下载卡片] 任务已添加到UI: {tool_name}")
        
        # 更新进度
        self.download_items[task_key].update_progress(progress, status)
        self._update_stats()
        
        # 保存到持久化存储
        self._save_tasks_to_file()
    
    def _remove_download_item(self, task_key: str):
        """移除下载项"""
        if task_key in self.download_items:
            item = self.download_items[task_key]
            self.content_layout.removeWidget(item)
            item.setParent(None)
            del self.download_items[task_key]
            
            # 如果没有项目了，显示空状态
            if not self.download_items:
                self._show_empty_state()
            
            self._update_stats()
    
    def _clear_completed(self):
        """清空已完成的任务 - 用户控制的清理"""
        completed_items = [key for key, item in self.download_items.items() 
                          if item.is_completed]
        
        if completed_items:
            print(f"🗑️ [清理] 用户清理已完成任务: {len(completed_items)} 个")
            
            for task_key in completed_items:
                self._remove_download_item(task_key)
            
            # 更新持久化文件
            self._save_tasks_to_file()
        else:
            print("ℹ️ [清理] 没有已完成的任务需要清理")
    
    def _update_stats(self):
        """更新统计信息"""
        total = len(self.download_items)
        active = sum(1 for item in self.download_items.values() 
                    if not item.is_completed and not item.is_failed)
        completed = sum(1 for item in self.download_items.values() 
                       if item.is_completed)
        failed = sum(1 for item in self.download_items.values() 
                    if item.is_failed)
        
        if total == 0:
            self.status_label.setText(self.tr("No download tasks"))
            self.stats_label.setText(self.tr("Total: 0 tasks"))
        else:
            status_parts = []
            if active > 0:
                status_parts.append(self.tr("{0} in progress").format(active))
            if completed > 0:
                status_parts.append(self.tr("{0} completed").format(completed))
            if failed > 0:
                status_parts.append(self.tr("{0} failed").format(failed))
            
            self.status_label.setText(" • ".join(status_parts) if status_parts else self.tr("All tasks completed"))
            self.stats_label.setText(self.tr("Total: {0} tasks").format(total))
    
    def _on_close_clicked(self):
        """关闭卡片"""
        self.hide()
        self.card_closed.emit()
    
    def has_active_downloads(self) -> bool:
        """检查是否有活跃的下载"""
        return any(not item.is_completed and not item.is_failed 
                  for item in self.download_items.values())
    
    def get_download_count(self) -> tuple:
        """获取下载计数 (活动, 总数)"""
        active = sum(1 for item in self.download_items.values() 
                    if not item.is_completed and not item.is_failed)
        total = len(self.download_items)
        return active, total
    
    def show_aligned_to_toolbar(self, toolbar_bottom, button_rect, window_rect):
        """
        🎯 动态高度版本 - 智能定位显示下载卡片
        根据实际内容高度自适应定位，紧贴工具栏分界线
        """
        print(f"【DEBUG】动态高度版本 - 智能定位下载卡片: toolbar_bottom={toolbar_bottom}")
        
        # 🎯 先显示以确定实际高度，然后定位
        self.show()
        self.adjustSize()  # 根据内容调整到合适大小
        
        actual_height = self.height()
        actual_width = self.width()  # 应该是400px
        print(f"【DEBUG】下载卡片动态尺寸: {actual_width}x{actual_height}")
        
        # 垂直位置：紧贴工具栏底部，但要确保不超出屏幕
        y = toolbar_bottom
        window_height = window_rect.height()
        if y + actual_height > window_height:
            y = window_height - actual_height - 10  # 留10px底部边距
            print(f"【DEBUG】调整Y位置防止超出屏幕: y={y}")
        
        # 水平位置：靠右对齐
        margin = 2
        window_width = window_rect.width()
        x = window_width - actual_width - margin
        
        final_pos = QPoint(x, y)
        print(f"【DEBUG】下载卡片动态高度最终位置: {final_pos}")
        
        self.raise_()
        
        # 滑入动画：从稍高的位置滑入
        start_y = y - 15
        self.move(x, start_y)
        
        # 创建位置动画
        if not hasattr(self, 'slide_animation'):
            self.slide_animation = QPropertyAnimation(self, b"pos")
            self.slide_animation.setDuration(250)
            self.slide_animation.setEasingCurve(QEasingCurve.OutCubic)
        
        self.slide_animation.setStartValue(QPoint(x, start_y))
        self.slide_animation.setEndValue(final_pos)
        self.slide_animation.start()
        
        self.activateWindow()
    
    def _save_tasks_to_file(self):
        """保存任务到文件 - 持久化存储"""
        try:
            # 确保日志目录存在
            os.makedirs(os.path.dirname(self.tasks_file), exist_ok=True)
            
            # 构建保存数据 - 只保存已完成或失败的任务
            tasks_data = []
            for task_key, item in self.download_items.items():
                # 只保存已完成或失败的任务，跳过未完成的任务
                if not item.is_completed and not item.is_failed:
                    continue
                    
                task_data = {
                    'tool_name': item.tool_name,  # 保存原始工具名
                    'task_key': task_key,         # 也保存键用于恢复
                    'progress': item.progress_value,
                    'status': item.status_label.text() if hasattr(item, 'status_label') else self.tr('Unknown'),
                    'is_completed': item.is_completed,
                    'is_failed': item.is_failed,
                    'start_time': item.start_time.isoformat() if hasattr(item, 'start_time') else datetime.now().isoformat()
                }
                tasks_data.append(task_data)
            
            # 写入文件
            with open(self.tasks_file, 'w', encoding='utf-8') as f:
                json.dump(tasks_data, f, ensure_ascii=False, indent=2)
            
            print(f"💾 [持久化] 任务已保存到文件: {len(tasks_data)} 个任务")
        except Exception as e:
            print(f"❌ [持久化] 保存任务失败: {e}")
    
    def _load_tasks_from_file(self):
        """从文件加载任务 - 恢复历史记录"""
        try:
            if not os.path.exists(self.tasks_file):
                print("📝 [持久化] 未找到历史任务文件，首次启动")
                return
            
            with open(self.tasks_file, 'r', encoding='utf-8') as f:
                tasks_data = json.load(f)
            
            print(f"📖 [持久化] 从文件加载 {len(tasks_data)} 个历史任务")
            
            # 过滤：只加载已完成或失败的任务，跳过未完成的中断任务
            filtered_tasks = []
            skipped_count = 0
            
            for task_data in tasks_data:
                is_completed = task_data.get('is_completed', True)
                is_failed = task_data.get('is_failed', False)
                
                # 跳过未完成且未失败的任务（中断任务）
                if not is_completed and not is_failed:
                    skipped_count += 1
                    continue
                
                filtered_tasks.append(task_data)
            
            if skipped_count > 0:
                print(f"🧹 [持久化] 跳过 {skipped_count} 个未完成的历史任务")
            
            print(f"✨ [持久化] 实际加载 {len(filtered_tasks)} 个已完成任务")
            
            # 重建任务项
            for task_data in filtered_tasks:
                tool_name = task_data['tool_name']
                task_key = task_data.get('task_key', tool_name)  # 向后兼容旧数据
                progress = task_data.get('progress', 100)
                status = task_data.get('status', self.tr('Completed'))
                is_completed = task_data.get('is_completed', True)
                is_failed = task_data.get('is_failed', False)
                
                # 创建任务项
                item = ModernDownloadItem(tool_name)
                item.remove_requested.connect(lambda name, key=task_key: self._remove_download_item(key))
                item.task_key = task_key
                item.progress_value = progress
                item.is_completed = is_completed
                item.is_failed = is_failed
                
                # 恢复开始时间
                if 'start_time' in task_data:
                    try:
                        item.start_time = datetime.fromisoformat(task_data['start_time'])
                    except:
                        item.start_time = datetime.now()
                
                # 如果是已完成/失败的任务，设置结束时间为开始时间（历史任务）
                if is_completed or is_failed:
                    item.end_time = item.start_time
                
                # 更新UI状态
                item.update_progress(progress, status)
                
                # 添加到字典（OrderedDict保持顺序）
                self.download_items[task_key] = item
            
            # 如果有任务，显示列表
            if self.download_items:
                self._show_download_list()
                print(f"✅ [持久化] 历史任务已恢复到UI")
            
        except Exception as e:
            print(f"❌ [持久化] 加载任务失败: {e}")
    
    def clear_all_tasks(self):
        """清空所有任务（包括持久化文件）"""
        try:
            # 清空UI
            while self.content_layout.count():
                item = self.content_layout.takeAt(0)
                if item.widget():
                    item.widget().setParent(None)
            
            # 清空数据
            self.download_items.clear()
            
            # 删除持久化文件
            if os.path.exists(self.tasks_file):
                os.remove(self.tasks_file)
            
            # 显示空状态
            self._show_empty_state()
            
            print("🗑️ [持久化] 所有任务已清空（包括历史记录）")
            
        except Exception as e:
            print(f"❌ [持久化] 清空任务失败: {e}")
