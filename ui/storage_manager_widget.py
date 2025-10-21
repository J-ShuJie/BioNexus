#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
存储管理组件
提供工具存储空间管理、批量删除、依赖清理等功能
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QTableWidget, QTableWidgetItem, QHeaderView,
                             QPushButton, QCheckBox, QProgressBar, QFrame,
                             QSplitter, QGroupBox, QTextEdit, QApplication)
from PyQt5.QtCore import Qt, pyqtSignal, QThread, pyqtSlot
from PyQt5.QtGui import QFont, QPalette, QColor, QIcon
from typing import List, Dict, Any
import logging

from utils.storage_calculator import get_storage_calculator, ToolStorageInfo
from utils.dependency_manager import get_dependency_manager


class StorageAnalysisThread(QThread):
    """存储分析线程，避免界面冻结"""
    
    analysis_finished = pyqtSignal(list, dict)  # tools_info, summary
    progress_updated = pyqtSignal(int, str)     # progress, status
    
    def run(self):
        """在后台线程中执行存储分析"""
        try:
            self.progress_updated.emit(10, self.tr("Scanning installed tools..."))
            calc = get_storage_calculator()

            self.progress_updated.emit(40, self.tr("Calculating tool sizes..."))
            tools_info = calc.get_all_tools_storage_info()

            self.progress_updated.emit(70, self.tr("Analyzing storage usage..."))
            summary = calc.get_storage_summary()

            self.progress_updated.emit(100, self.tr("Analysis Complete"))
            self.analysis_finished.emit(tools_info, summary)
            
        except Exception as e:
            logging.error(f"存储分析失败: {e}")
            self.analysis_finished.emit([], {})




class ToolsTableWidget(QTableWidget):
    """工具列表表格组件"""
    
    tools_selection_changed = pyqtSignal(list)  # 选中的工具名列表
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_table()
        self.tools_data = []
    
    def _init_table(self):
        """初始化表格"""
        # 设置列
        headers = [self.tr(""), self.tr("Tool Name"), self.tr("Size"), self.tr("Path"), self.tr("Dependencies")]
        self.setColumnCount(len(headers))
        self.setHorizontalHeaderLabels(headers)
        
        # 设置表格样式
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QTableWidget.SelectRows)
        self.setStyleSheet("""
            QTableWidget {
                gridline-color: #e0e0e0;
                background-color: white;
                alternate-background-color: #f8f8f8;
            }
            QTableWidget::item {
                padding: 8px;
                border: none;
            }
            QHeaderView::section {
                background-color: #f0f0f0;
                border: 1px solid #e0e0e0;
                padding: 8px;
                font-weight: bold;
            }
        """)
        
        # 调整列宽
        header = self.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Fixed)  # 复选框列
        header.setSectionResizeMode(1, QHeaderView.Stretch)  # 工具名
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # 大小
        header.setSectionResizeMode(3, QHeaderView.Stretch)  # 路径
        header.setSectionResizeMode(4, QHeaderView.Stretch)  # 依赖
        
        self.setColumnWidth(0, 30)
    
    def load_tools(self, tools_info: List[ToolStorageInfo]):
        """加载工具数据"""
        self.tools_data = tools_info
        self.setRowCount(len(tools_info))
        
        calc = get_storage_calculator()
        
        for row, tool in enumerate(tools_info):
            # 复选框
            checkbox = QCheckBox()
            checkbox.stateChanged.connect(self._on_selection_changed)
            self.setCellWidget(row, 0, checkbox)
            
            # 工具名称
            self.setItem(row, 1, QTableWidgetItem(tool.name))
            
            # 大小
            size_item = QTableWidgetItem(calc.format_size(tool.size))
            size_item.setData(Qt.UserRole, tool.size)  # 存储原始字节数用于排序
            self.setItem(row, 2, size_item)
            
            # 路径
            self.setItem(row, 3, QTableWidgetItem(tool.path))
            
            # 依赖环境
            deps_text = ", ".join(tool.dependencies) if tool.dependencies else self.tr("None")
            self.setItem(row, 4, QTableWidgetItem(deps_text))
        
        # 默认按大小排序（降序）
        self.sortItems(2, Qt.DescendingOrder)
    
    def _on_selection_changed(self):
        """处理选择变化"""
        selected_tools = []
        for row in range(self.rowCount()):
            checkbox = self.cellWidget(row, 0)
            if checkbox.isChecked():
                tool_name = self.item(row, 1).text()
                selected_tools.append(tool_name)
        
        self.tools_selection_changed.emit(selected_tools)
    
    def get_selected_tools(self) -> List[str]:
        """获取选中的工具名列表"""
        selected_tools = []
        for row in range(self.rowCount()):
            checkbox = self.cellWidget(row, 0)
            if checkbox.isChecked():
                tool_name = self.item(row, 1).text()
                selected_tools.append(tool_name)
        return selected_tools
    
    def select_all_tools(self, select: bool = True):
        """全选/取消全选工具"""
        for row in range(self.rowCount()):
            checkbox = self.cellWidget(row, 0)
            checkbox.setChecked(select)



class StorageManagerWidget(QWidget):
    """存储管理主组件"""
    
    # 信号定义
    delete_tools_requested = pyqtSignal(list)  # 请求删除工具
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        self._init_ui()
        self._setup_connections()
        
        # 分析线程
        self.analysis_thread = None
        
        # 开始加载数据
        self.refresh_data()
    
    def _init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        # 进度条（需要时显示）
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #bdc3c7;
                border-radius: 5px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #3498db;
                border-radius: 4px;
            }
        """)
        layout.addWidget(self.progress_bar)
        
        # 存储概览和操作按钮融合布局
        header_layout = QHBoxLayout()
        header_layout.setSpacing(20)
        
        # 存储概览信息（左侧）
        self.overview_info_label = QLabel(self.tr("Loading..."))
        self.overview_info_label.setFont(QFont("Microsoft YaHei", 11, QFont.Bold))
        self.overview_info_label.setStyleSheet("color: #2c3e50;")
        header_layout.addWidget(self.overview_info_label)

        header_layout.addStretch()

        # 操作按钮组（右侧）
        self.select_all_btn = QPushButton(self.tr("Select All"))
        self.select_none_btn = QPushButton(self.tr("Cancel"))
        self.refresh_btn = QPushButton(self.tr("Refresh"))
        self.delete_selected_btn = QPushButton(self.tr("Delete"))
        
        # 按钮样式
        button_style = """
            QPushButton {
                padding: 5px 10px;
                border: 1px solid #bdc3c7;
                border-radius: 3px;
                background-color: white;
            }
            QPushButton:hover {
                background-color: #ecf0f1;
            }
        """
        self.select_all_btn.setStyleSheet(button_style)
        self.select_none_btn.setStyleSheet(button_style)
        self.refresh_btn.setStyleSheet("""
            QPushButton {
                padding: 5px 10px;
                border: 1px solid #3498db;
                border-radius: 3px;
                background-color: #3498db;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        self.delete_selected_btn.setStyleSheet("""
            QPushButton {
                padding: 5px 10px;
                border: 1px solid #e74c3c;
                border-radius: 3px;
                background-color: #e74c3c;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
                border-color: #95a5a6;
            }
        """)
        self.delete_selected_btn.setEnabled(False)
        
        # 创建按钮容器，设置更紧凑的间距
        buttons_widget = QWidget()
        buttons_layout = QHBoxLayout(buttons_widget)
        buttons_layout.setContentsMargins(0, 0, 0, 0)
        buttons_layout.setSpacing(8)  # 紧凑间距
        
        buttons_layout.addWidget(self.select_all_btn)
        buttons_layout.addWidget(self.select_none_btn)
        buttons_layout.addWidget(self.refresh_btn)
        buttons_layout.addWidget(self.delete_selected_btn)
        
        header_layout.addWidget(buttons_widget)
        
        layout.addLayout(header_layout)
        
        # 工具表格（占据剩余空间）
        self.tools_table = ToolsTableWidget()
        layout.addWidget(self.tools_table)
    
    def _setup_connections(self):
        """设置信号连接"""
        self.refresh_btn.clicked.connect(self.refresh_data)
        self.select_all_btn.clicked.connect(lambda: self.tools_table.select_all_tools(True))
        self.select_none_btn.clicked.connect(lambda: self.tools_table.select_all_tools(False))
        self.delete_selected_btn.clicked.connect(self._on_delete_requested)
        
        self.tools_table.tools_selection_changed.connect(self._on_tools_selection_changed)
    
    def refresh_data(self):
        """刷新数据"""
        if self.analysis_thread and self.analysis_thread.isRunning():
            return
        
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.refresh_btn.setEnabled(False)
        
        self.analysis_thread = StorageAnalysisThread()
        self.analysis_thread.analysis_finished.connect(self._on_analysis_finished)
        self.analysis_thread.progress_updated.connect(self._on_progress_updated)
        self.analysis_thread.start()
    
    @pyqtSlot(int, str)
    def _on_progress_updated(self, progress: int, status: str):
        """更新进度"""
        self.progress_bar.setValue(progress)
        self.progress_bar.setFormat(f"{status} ({progress}%)")
    
    @pyqtSlot(list, dict)
    def _on_analysis_finished(self, tools_info: List[ToolStorageInfo], summary: Dict):
        """分析完成处理"""
        self.progress_bar.setVisible(False)
        self.refresh_btn.setEnabled(True)
        
        # 更新界面
        self.tools_table.load_tools(tools_info)
        self._update_overview_info(summary)
        
        self.logger.info(f"存储分析完成，发现 {len(tools_info)} 个已安装工具")
    
    def _update_overview_info(self, summary: Dict):
        """更新概览信息显示"""
        try:
            calc = get_storage_calculator()
            
            # 格式化概览信息（精简版）
            system_free = calc.format_size(summary['system_free'])
            tools_count = summary['tools_count']
            tools_size = calc.format_size(summary['tools_size'])
            bionexus_total = calc.format_size(summary['bionexus_total'])
            
            # 组合显示文本（精简版，删除总计部分）
            overview_text = self.tr("Remaining: {0} | Tools using: {1}/{2}").format(system_free, tools_count, tools_size)

            self.overview_info_label.setText(overview_text)

        except Exception as e:
            self.logger.error(f"更新概览信息失败: {e}")
            self.overview_info_label.setText(self.tr("Failed to update overview information"))
    
    def _on_tools_selection_changed(self, selected_tools: List[str]):
        """处理工具选择变化"""
        self.delete_selected_btn.setEnabled(len(selected_tools) > 0)
    
    def _on_delete_requested(self):
        """处理删除请求"""
        selected_tools = self.tools_table.get_selected_tools()
        if selected_tools:
            self.delete_tools_requested.emit(selected_tools)
    
    def get_selected_tools(self) -> List[str]:
        """获取选中的工具列表"""
        return self.tools_table.get_selected_tools()