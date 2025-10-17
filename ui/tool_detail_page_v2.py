#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工具详情页面 V2 - 智能选择器
根据配置自动选择使用 QGraphicsView 或传统 Widget 实现

使用方法：
1. 默认使用 QGraphicsView 版本（性能最优）
2. 可通过环境变量 BIONEXUS_USE_LEGACY_DETAIL=1 切换到传统版本
3. 自动检测系统性能，选择最适合的实现
"""

import os
import sys
from PyQt5.QtCore import pyqtSignal, QObject
from PyQt5.QtWidgets import QWidget, QVBoxLayout
import logging

# 检测是否强制使用传统版本
USE_LEGACY = os.environ.get('BIONEXUS_USE_LEGACY_DETAIL', '0') == '1'

# 检测是否支持 OpenGL
try:
    from PyQt5.QtWidgets import QOpenGLWidget
    HAS_OPENGL = True
except ImportError:
    HAS_OPENGL = False


class ToolDetailPage(QWidget):
    """
    工具详情页面 - 智能版本
    自动选择最佳实现
    """
    
    # 统一的对外信号接口
    back_requested = pyqtSignal()
    install_requested = pyqtSignal(str)
    launch_requested = pyqtSignal(str)
    uninstall_requested = pyqtSignal(str)
    
    def __init__(self, tool_data: dict, parent=None):
        super().__init__(parent)
        
        self.tool_data = tool_data
        self.logger = logging.getLogger(f"BioNexus.DetailPage.{tool_data.get('name', 'Unknown')}")
        
        # 选择实现版本
        self._implementation = None
        self._select_implementation()
        
        # 初始化UI
        self._init_ui()
        
    def _select_implementation(self):
        """选择最佳实现版本"""
        if USE_LEGACY:
            self.logger.info("使用传统 Widget 版本（用户配置）")
            self._use_legacy_version()
        else:
            # 尝试使用 GraphicsView 版本
            try:
                from .tool_detail_graphics_view import ToolDetailGraphicsView
                self.logger.info("使用 QGraphicsView 版本（最优性能）")
                self._implementation = 'graphics'
            except ImportError as e:
                self.logger.warning(f"无法加载 GraphicsView 版本，回退到传统版本: {e}")
                self._use_legacy_version()
    
    def _use_legacy_version(self):
        """使用传统版本"""
        self._implementation = 'legacy'
    
    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        if self._implementation == 'graphics':
            # 使用 GraphicsView 版本
            from .tool_detail_graphics_view import ToolDetailGraphicsView
            
            self.detail_view = ToolDetailGraphicsView(self.tool_data, self)
            
            # 连接信号
            self.detail_view.back_requested.connect(self.back_requested.emit)
            self.detail_view.install_requested.connect(self.install_requested.emit)
            self.detail_view.launch_requested.connect(self.launch_requested.emit)
            self.detail_view.uninstall_requested.connect(self.uninstall_requested.emit)
            
            layout.addWidget(self.detail_view)
            
            self.logger.info("GraphicsView 详情页面初始化成功")
            
        else:
            # 使用传统 Widget 版本
            from .tool_detail_page import ToolDetailPage as LegacyDetailPage
            
            # 避免命名冲突，创建传统版本实例
            self.detail_view = LegacyDetailPage(self.tool_data, self)
            
            # 连接信号
            self.detail_view.back_requested.connect(self.back_requested.emit)
            self.detail_view.install_requested.connect(self.install_requested.emit)
            self.detail_view.launch_requested.connect(self.launch_requested.emit)
            self.detail_view.uninstall_requested.connect(self.uninstall_requested.emit)
            
            layout.addWidget(self.detail_view)
            
            self.logger.info("传统 Widget 详情页面初始化成功")
    
    def get_implementation_info(self) -> str:
        """获取当前实现版本信息"""
        if self._implementation == 'graphics':
            return "QGraphicsView (GPU加速，最优性能)"
        else:
            return "传统Widget (兼容模式)"


def get_detail_page_class():
    """
    获取详情页面类
    这是给外部调用的工厂函数
    """
    return ToolDetailPage


# 为了兼容性，也可以直接导入具体实现
def get_graphics_view_implementation():
    """获取 GraphicsView 实现"""
    from .tool_detail_graphics_view import ToolDetailGraphicsView
    return ToolDetailGraphicsView


def get_legacy_implementation():
    """获取传统实现"""
    from .tool_detail_page import ToolDetailPage as LegacyDetailPage
    return LegacyDetailPage