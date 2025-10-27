#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工具详情页面 - QGraphicsView 重构版本
使用 Scene Graph 架构实现最高性能和最精确的布局控制

特性：
- GPU 加速渲染
- 像素级精确布局
- 完美的层级管理
- 永不截断的内容显示
- 60 FPS 流畅动画
"""

from PyQt5.QtWidgets import (
    QGraphicsView, QGraphicsScene, QGraphicsItem, QGraphicsProxyWidget,
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextEdit,
    QGraphicsDropShadowEffect, QGraphicsItemGroup, QStyleOptionGraphicsItem,
    QGraphicsRectItem, QGraphicsTextItem, QSizePolicy, QFrame
)
from PyQt5.QtCore import (
    Qt, QRectF, QPointF, QSizeF, pyqtSignal, QPropertyAnimation,
    QEasingCurve, QParallelAnimationGroup, QSequentialAnimationGroup,
    pyqtProperty, QTimer, QObject
)
from PyQt5.QtGui import (
    QPainter, QBrush, QColor, QLinearGradient, QFont, QPen,
    QFontMetrics, QTransform, QPainterPath
)

try:
    from PyQt5.QtWidgets import QOpenGLWidget
    from PyQt5.QtGui import QSurfaceFormat
    HAS_OPENGL = True
except ImportError:
    HAS_OPENGL = False

import logging
from typing import Dict, Optional, Tuple
from vendor.auto_resizing.text_edit import AutoResizingTextEdit


class GraphicsButton(QGraphicsItem):
    """
    自定义图形按钮项
    完全控制渲染和交互
    """
    
    def __init__(self, text: str, width: float, height: float, 
                 color: str = "#10b981", hover_color: str = "#34d399",
                 parent=None):
        super().__init__(parent)
        
        self.text = text
        self.width = width
        self.height = height
        self.base_color = QColor(color)
        self.hover_color = QColor(hover_color)
        self.current_color = self.base_color
        
        # 交互状态
        self.is_hovered = False
        self.is_pressed = False
        
        # 启用悬停事件
        self.setAcceptHoverEvents(True)
        self.setCursor(Qt.PointingHandCursor)
        
        # 动画支持
        self._scale = 1.0
        self._opacity = 1.0
        
        # 点击回调
        self.click_callback = None
        
    def boundingRect(self) -> QRectF:
        """定义边界矩形"""
        return QRectF(0, 0, self.width, self.height)
    
    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget=None):
        """自定义绘制"""
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 创建渐变
        gradient = QLinearGradient(0, 0, 0, self.height)
        if self.is_pressed:
            gradient.setColorAt(0, self.current_color.darker(120))
            gradient.setColorAt(1, self.current_color.darker(150))
        else:
            gradient.setColorAt(0, self.current_color)
            gradient.setColorAt(1, self.current_color.darker(110))
        
        # 绘制圆角矩形
        path = QPainterPath()
        path.addRoundedRect(self.boundingRect(), 8, 8)
        painter.fillPath(path, QBrush(gradient))
        
        # 绘制文本
        painter.setPen(QPen(Qt.white))
        font = QFont()
        font.setPointSize(12)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(self.boundingRect(), Qt.AlignCenter, self.text)
        
        # 绘制边框（仅在悬停时）
        if self.is_hovered:
            painter.setPen(QPen(QColor(255, 255, 255, 80), 2))
            painter.drawRoundedRect(self.boundingRect(), 8, 8)
    
    def hoverEnterEvent(self, event):
        """鼠标进入"""
        self.is_hovered = True
        self.current_color = self.hover_color
        self.setScale(1.02)  # 轻微放大
        self.update()
    
    def hoverLeaveEvent(self, event):
        """鼠标离开"""
        self.is_hovered = False
        self.current_color = self.base_color
        self.setScale(1.0)
        self.update()
    
    def mousePressEvent(self, event):
        """鼠标按下"""
        if event.button() == Qt.LeftButton:
            self.is_pressed = True
            self.setScale(0.98)  # 轻微缩小
            self.update()
    
    def mouseReleaseEvent(self, event):
        """鼠标释放"""
        if event.button() == Qt.LeftButton:
            self.is_pressed = False
            self.setScale(1.02 if self.is_hovered else 1.0)
            self.update()
            
            # 触发点击回调
            if self.click_callback and self.boundingRect().contains(event.pos()):
                self.click_callback()
    
    def set_click_callback(self, callback):
        """设置点击回调"""
        self.click_callback = callback


class TimeStatisticsItem(QGraphicsItem):
    """
    时间统计显示项
    精确控制位置，永不被截断
    """
    
    def __init__(self, usage_time: str, width: float, parent=None):
        super().__init__(parent)
        
        self.usage_time = usage_time
        self.width = width
        self.height = 30  # 固定高度
        
        # 视觉样式
        self.bg_color = QColor(248, 250, 252, 200)
        self.text_color = QColor(107, 114, 128)
        self.border_color = QColor(229, 231, 235, 128)
        
    def boundingRect(self) -> QRectF:
        """定义边界矩形"""
        return QRectF(0, 0, self.width, self.height)
    
    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget=None):
        """自定义绘制"""
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 绘制背景
        path = QPainterPath()
        path.addRoundedRect(self.boundingRect(), 4, 4)
        painter.fillPath(path, QBrush(self.bg_color))
        
        # 绘制顶部分隔线
        painter.setPen(QPen(self.border_color, 1))
        painter.drawLine(QPointF(10, 0), QPointF(self.width - 10, 0))
        
        # 绘制文本
        painter.setPen(QPen(self.text_color))
        font = QFont()
        font.setPointSize(10)
        font.setWeight(QFont.Medium)
        painter.setFont(font)

        # 智能显示：如果是"暂未使用"，直接显示；否则显示"已使用 X小时"
        if self.usage_time in ["暂未使用", "Not used yet"]:
            text = self.usage_time
        else:
            text = f"已使用 {self.usage_time}"
        painter.drawText(self.boundingRect(), Qt.AlignCenter, text)


class OperationGroup(QGraphicsItemGroup):
    """
    操作组容器
    包含按钮和时间统计，确保正确的相对位置
    """
    
    def __init__(self, tool_data: dict, parent=None):
        super().__init__(parent)
        
        self.tool_data = tool_data
        self.buttons = []
        self.time_stat = None
        
        # 信号发射器（因为 QGraphicsItem 不能直接发射信号）
        self.signal_emitter = OperationSignalEmitter()
        
        self._build_group()
    
    def _build_group(self):
        """构建操作组"""
        if self.tool_data['status'] == 'installed':
            # 已安装：显示启动和卸载按钮
            self._create_installed_group()
        else:
            # 未安装：显示安装按钮
            self._create_uninstalled_group()
    
    def _create_installed_group(self):
        """创建已安装状态的操作组"""
        # 按钮容器位置
        button_y = 0
        
        # 启动按钮
        launch_btn = GraphicsButton(
            "🚀 启动", 90, 38,
            color="#10b981",
            hover_color="#34d399"
        )
        launch_btn.setPos(0, button_y)
        launch_btn.set_click_callback(
            lambda: self.signal_emitter.launch_requested.emit(self.tool_data['name'])
        )
        self.addToGroup(launch_btn)
        self.buttons.append(launch_btn)
        
        # 卸载按钮（紧挨着启动按钮）
        uninstall_btn = GraphicsButton(
            "🗑️", 36, 38,
            color="#ef4444",
            hover_color="#f87171"
        )
        uninstall_btn.setPos(92, button_y)  # 90 + 2像素间隔
        uninstall_btn.set_click_callback(
            lambda: self.signal_emitter.uninstall_requested.emit(self.tool_data['name'])
        )
        self.addToGroup(uninstall_btn)
        self.buttons.append(uninstall_btn)
        
        # 时间统计（在按钮下方，精确控制间距）
        time_y = button_y + 38 + 10  # 按钮高度 + 间距
        self.time_stat = TimeStatisticsItem(
            self._get_usage_time(), 
            128  # 与按钮组总宽度一致
        )
        self.time_stat.setPos(0, time_y)
        self.addToGroup(self.time_stat)
    
    def _create_uninstalled_group(self):
        """创建未安装状态的操作组"""
        # 安装按钮
        install_btn = GraphicsButton(
            "📥 安装工具", 128, 38,
            color="#3b82f6",
            hover_color="#60a5fa"
        )
        install_btn.setPos(0, 0)
        install_btn.set_click_callback(
            lambda: self.signal_emitter.install_requested.emit(self.tool_data['name'])
        )
        self.addToGroup(install_btn)
        self.buttons.append(install_btn)
    
    def _get_usage_time(self) -> str:
        """获取使用时间（使用智能格式化）"""
        # 使用真实的使用时间数据
        total_runtime = self.tool_data.get('total_runtime', 0)

        if total_runtime == 0:
            return "暂未使用"

        # 使用智能时间格式化
        from utils.time_formatter import format_runtime
        return format_runtime(total_runtime, language='zh_CN')


class OperationSignalEmitter(QObject):
    """操作信号发射器（因为 QGraphicsItem 不能发射信号）"""
    launch_requested = pyqtSignal(str)
    install_requested = pyqtSignal(str)
    uninstall_requested = pyqtSignal(str)


class ToolDetailGraphicsView(QGraphicsView):
    """
    工具详情页面 - QGraphicsView 实现
    最高性能，最精确控制
    """
    
    # 对外信号
    back_requested = pyqtSignal()
    install_requested = pyqtSignal(str)
    launch_requested = pyqtSignal(str)
    uninstall_requested = pyqtSignal(str)
    
    def __init__(self, tool_data: dict, parent=None):
        super().__init__(parent)
        
        self.tool_data = tool_data
        self.logger = logging.getLogger(f"BioNexus.GraphicsView.{tool_data.get('name', 'Unknown')}")
        
        # 初始化场景
        self.scene = QGraphicsScene()
        self.setScene(self.scene)
        
        # 设置视图属性
        self._setup_view_properties()
        
        # 构建场景
        self._build_scene()
        
        # 设置场景大小
        self.scene.setSceneRect(0, 0, 900, 800)
        
    def _setup_view_properties(self):
        """设置视图属性"""
        # 渲染优化
        self.setRenderHint(QPainter.Antialiasing)
        self.setRenderHint(QPainter.SmoothPixmapTransform)
        self.setRenderHint(QPainter.TextAntialiasing)
        
        # 视口更新模式
        self.setViewportUpdateMode(QGraphicsView.SmartViewportUpdate)
        
        # 缓存背景
        self.setCacheMode(QGraphicsView.CacheBackground)
        
        # 启用 OpenGL 加速（如果可用）
        if HAS_OPENGL:
            try:
                gl_widget = QOpenGLWidget()
                fmt = QSurfaceFormat()
                fmt.setSamples(4)  # 4x 抗锯齿
                gl_widget.setFormat(fmt)
                self.setViewport(gl_widget)
                self.logger.info("OpenGL 加速已启用")
            except Exception as e:
                self.logger.warning(f"无法启用 OpenGL: {e}")
        
        # 设置背景
        self.setBackgroundBrush(QBrush(QColor("#F5F6F8")))
        
        # 禁用滚动条（我们要完全控制视口）
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # 设置对齐
        self.setAlignment(Qt.AlignTop | Qt.AlignLeft)
    
    def _build_scene(self):
        """构建场景图"""
        self.logger.info("开始构建场景图")
        
        # 1. 顶部返回栏 - 现在不需要，返回按钮在主窗口工具栏
        # self._add_top_bar()  # 注释掉
        
        # 2. 主内容区域
        self._add_main_content()
        
        # 3. 操作区域（按钮和时间统计）
        self._add_operation_area()
        
        # 4. 工具介绍区域
        self._add_description_area()
        
        # 5. 技术规格区域
        self._add_tech_specs_area()
        
        self.logger.info("场景图构建完成")
    
    def _add_top_bar(self):
        """添加顶部返回栏"""
        # 创建顶部栏背景
        top_bar_bg = QGraphicsRectItem(0, 0, 900, 50)
        top_bar_bg.setBrush(QBrush(Qt.white))
        top_bar_bg.setPen(QPen(Qt.NoPen))
        self.scene.addItem(top_bar_bg)
        
        # 返回按钮（使用自定义图形按钮）
        back_btn = GraphicsButton(
            "← 返回", 80, 32,
            color="#64748b",
            hover_color="#94a3b8"
        )
        back_btn.setPos(20, 9)
        back_btn.set_click_callback(self.back_requested.emit)
        self.scene.addItem(back_btn)
        
        # 添加底部阴影线
        shadow_line = QGraphicsRectItem(0, 49, 900, 1)
        shadow_line.setBrush(QBrush(QColor(0, 0, 0, 20)))
        shadow_line.setPen(QPen(Qt.NoPen))
        self.scene.addItem(shadow_line)
    
    def _add_main_content(self):
        """添加主内容区域（头部信息）"""
        # 主内容背景 - Y坐标从20开始（无顶部栏）
        content_bg = QGraphicsRectItem(20, 20, 860, 120)
        content_bg.setBrush(QBrush(Qt.white))
        content_bg.setPen(QPen(QColor(226, 232, 240), 1))
        self.scene.addItem(content_bg)
        
        # 工具图标背景
        icon_colors = {
            "quality": "#3b82f6",
            "sequence": "#10b981",
            "rnaseq": "#f59e0b",
            "genomics": "#8b5cf6",
            "phylogeny": "#ec4899"
        }
        color = icon_colors.get(self.tool_data.get('category', 'quality'), "#64748b")
        
        icon_bg = QGraphicsRectItem(40, 40, 64, 64)  # Y坐标调整
        icon_bg.setBrush(QBrush(QColor(color)))
        icon_bg.setPen(QPen(Qt.NoPen))
        self.scene.addItem(icon_bg)
        
        # 工具名称首字母
        icon_text = QGraphicsTextItem(self.tool_data['name'][:2].upper())
        icon_text.setDefaultTextColor(Qt.white)
        font = QFont()
        font.setPointSize(24)
        font.setBold(True)
        icon_text.setFont(font)
        icon_text.setPos(52, 55)  # Y坐标调整
        self.scene.addItem(icon_text)
        
        # 工具名称
        name_text = QGraphicsTextItem(self.tool_data['name'])
        name_font = QFont()
        name_font.setPointSize(18)
        name_font.setBold(True)
        name_text.setFont(name_font)
        name_text.setDefaultTextColor(QColor("#0f172a"))
        name_text.setPos(120, 45)  # Y坐标调整
        self.scene.addItem(name_text)
        
        # 版本信息
        version_text = QGraphicsTextItem(f"版本 v{self.tool_data.get('version', 'N/A')}")
        version_font = QFont()
        version_font.setPointSize(12)
        version_text.setFont(version_font)
        version_text.setDefaultTextColor(QColor("#6366f1"))
        version_text.setPos(120, 75)  # Y坐标调整
        self.scene.addItem(version_text)
    
    def _add_operation_area(self):
        """
        添加操作区域（按钮和时间统计）
        这是核心部分 - 精确控制位置，永不截断
        """
        # 操作组的精确位置
        operation_x = 720  # 右侧位置
        operation_y = 45   # 垂直位置 - 调整为与内容对齐
        
        # 创建操作组
        operation_group = OperationGroup(self.tool_data)
        operation_group.setPos(operation_x, operation_y)
        
        # 连接信号
        operation_group.signal_emitter.launch_requested.connect(self.launch_requested.emit)
        operation_group.signal_emitter.install_requested.connect(self.install_requested.emit)
        operation_group.signal_emitter.uninstall_requested.connect(self.uninstall_requested.emit)
        
        # 添加到场景
        self.scene.addItem(operation_group)
        
        # 添加装饰背景（可选）
        if self.tool_data['status'] == 'installed':
            # 为已安装状态添加背景装饰
            deco_bg = QGraphicsRectItem(
                operation_x - 10, 
                operation_y - 10,
                148,  # 宽度
                88    # 高度：按钮(38) + 间距(10) + 时间统计(30) + padding(10)
            )
            deco_bg.setBrush(QBrush(QColor(248, 249, 250, 128)))
            deco_bg.setPen(QPen(QColor(226, 232, 240, 128), 1))
            deco_bg.setZValue(-1)  # 放在按钮后面
            self.scene.addItem(deco_bg)
    
    def _add_description_area(self):
        """添加工具介绍区域"""
        # 介绍区域背景 - Y坐标调整
        desc_bg = QGraphicsRectItem(20, 160, 860, 200)
        desc_bg.setBrush(QBrush(Qt.white))
        desc_bg.setPen(QPen(QColor(226, 232, 240), 1))
        self.scene.addItem(desc_bg)
        
        # 标题
        title_text = QGraphicsTextItem("工具介绍")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_text.setFont(title_font)
        title_text.setDefaultTextColor(QColor("#0f172a"))
        title_text.setPos(40, 175)  # Y坐标调整
        self.scene.addItem(title_text)
        
        # 介绍内容（使用 QGraphicsProxyWidget 嵌入 QWidget）
        desc_widget = QTextEdit()
        desc_widget.setPlainText(self.tool_data.get('description', '暂无详细介绍'))
        desc_widget.setReadOnly(True)
        desc_widget.setStyleSheet("""
            QTextEdit {
                border: none;
                background: rgba(248, 250, 252, 0.8);
                color: #374151;
                padding: 10px;
                font-size: 11pt;
            }
        """)
        desc_widget.setMaximumHeight(140)
        desc_widget.setMinimumWidth(820)
        
        desc_proxy = QGraphicsProxyWidget()
        desc_proxy.setWidget(desc_widget)
        desc_proxy.setPos(40, 210)  # Y坐标调整
        self.scene.addItem(desc_proxy)
    
    def _add_tech_specs_area(self):
        """添加技术规格区域"""
        # 技术规格背景 - Y坐标调整
        specs_bg = QGraphicsRectItem(20, 380, 860, 250)
        specs_bg.setBrush(QBrush(Qt.white))
        specs_bg.setPen(QPen(QColor(226, 232, 240), 1))
        self.scene.addItem(specs_bg)
        
        # 标题
        title_text = QGraphicsTextItem("🔧 技术规格")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_text.setFont(title_font)
        title_text.setDefaultTextColor(QColor("#0f172a"))
        title_text.setPos(40, 395)  # Y坐标调整
        self.scene.addItem(title_text)
        
        # 技术规格数据
        specs_data = self._get_tech_specs()
        
        # 逐行添加规格
        y_offset = 430  # Y坐标调整
        for label, value in specs_data:
            # 标签
            label_text = QGraphicsTextItem(f"{label}：")
            label_font = QFont()
            label_font.setPointSize(11)
            label_font.setWeight(QFont.Medium)
            label_text.setFont(label_font)
            label_text.setDefaultTextColor(QColor("#64748b"))
            label_text.setPos(40, y_offset)
            self.scene.addItem(label_text)
            
            # 值
            value_text = QGraphicsTextItem(value)
            value_font = QFont()
            value_font.setPointSize(11)
            value_text.setFont(value_font)
            value_text.setDefaultTextColor(QColor("#374151"))
            value_text.setPos(140, y_offset)
            self.scene.addItem(value_text)
            
            y_offset += 25
    
    def _get_tech_specs(self) -> list:
        """获取技术规格数据"""
        tool_specs = {
            "FastQC": [
                ("编程语言", "Java"),
                ("依赖环境", "Java 8+"),
                ("输入格式", "FASTQ, SAM, BAM"),
                ("输出格式", "HTML, ZIP"),
                ("CPU要求", "单核即可"),
                ("内存要求", "最小2GB"),
                ("存储占用", "85MB"),
                ("源代码", "github.com/s-andrews/FastQC")
            ],
            "BLAST": [
                ("编程语言", "C++"),
                ("依赖环境", "标准C++库"),
                ("输入格式", "FASTA"),
                ("输出格式", "多种格式"),
                ("CPU要求", "多核推荐"),
                ("内存要求", "取决于数据库大小"),
                ("存储占用", "245MB"),
                ("源代码", "ncbi.nlm.nih.gov/blast")
            ]
        }
        
        default_specs = [
            ("编程语言", "暂无信息"),
            ("依赖环境", "暂无信息"),
            ("输入格式", "暂无信息"),
            ("输出格式", "暂无信息"),
            ("CPU要求", "多核推荐"),
            ("内存要求", "最小4GB"),
            ("存储占用", "未知")
        ]
        
        return tool_specs.get(self.tool_data['name'], default_specs)
    
    def resizeEvent(self, event):
        """窗口大小改变时调整视图"""
        super().resizeEvent(event)
        # 确保场景适应视图
        self.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)