"""
下载状态通知面板
右上角的下载状态侧边栏，显示所有正在进行和已完成的下载任务
提供实时进度更新和状态通知功能
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFrame, QScrollArea, QProgressBar
)
from PyQt5.QtCore import pyqtSignal, Qt, QTimer, pyqtSlot
from PyQt5.QtGui import QFont, QFontMetrics
from typing import Dict, List
from datetime import datetime


class DownloadItem(QWidget):
    """
    单个下载任务项
    显示工具名、进度条、状态文本和时间
    """
    
    remove_requested = pyqtSignal(str)  # 请求移除项目
    
    def __init__(self, tool_name: str, parent=None):
        super().__init__(parent)
        self.tool_name = tool_name
        self.start_time = datetime.now()
        self.is_completed = False
        self.init_ui()
    
    def init_ui(self):
        """初始化UI"""
        self.setObjectName("DownloadItem")
        self.setAttribute(Qt.WA_StyledBackground, True)
        
        # 设置卡片式下载项样式（参考详情页面风格）
        self.setStyleSheet("""
            QWidget#DownloadItem {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 white, stop:1 #fdfdfd);
                border: 1px solid #e0e0e0;
                border-radius: 12px;
                margin: 6px 12px;
                padding: 4px;
            }
            QWidget#DownloadItem[completed="true"] {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #f0fdf4, stop:1 #dcfce7);
                border: 2px solid #22c55e;
            }
            QWidget#DownloadItem[failed="true"] {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #fef2f2, stop:1 #fee2e2);
                border: 2px solid #ef4444;
            }
        """)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(8)
        
        # 顶部：工具名和关闭按钮
        top_layout = QHBoxLayout()
        top_layout.setContentsMargins(0, 0, 0, 0)
        
        # 工具图标（参考详情页面渐变风格）
        icon_label = QLabel()
        icon_label.setFixedSize(32, 32)  # 比详情页面小一些
        icon_label.setStyleSheet(f"""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 #3b82f6, stop:1 #1d4ed8);
            border-radius: 8px;
            color: white;
            font-size: 12px;
            font-weight: bold;
            border: 1px solid rgba(255, 255, 255, 0.2);
        """)
        icon_label.setText(self.tool_name[:2].upper())
        icon_label.setAlignment(Qt.AlignCenter)
        top_layout.addWidget(icon_label)
        
        # 工具名和状态信息
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)
        info_layout.setContentsMargins(0, 0, 0, 0)
        
        self.tool_label = QLabel(self.tool_name)
        self.tool_label.setObjectName("ToolName")
        font = QFont()
        font.setBold(True)
        font.setPointSize(10)
        self.tool_label.setFont(font)
        info_layout.addWidget(self.tool_label)
        
        # 添加到顶部布局
        top_layout.addLayout(info_layout)
        
        top_layout.addStretch()
        
        # 关闭按钮（仅在完成后显示）
        self.close_btn = QPushButton("×")
        self.close_btn.setObjectName("CloseBtn")
        self.close_btn.setFixedSize(24, 24)
        self.close_btn.clicked.connect(lambda: self.remove_requested.emit(self.tool_name))
        # 现代化小关闭按钮样式
        self.close_btn.setStyleSheet("""
            QPushButton#CloseBtn {
                background: rgba(156, 163, 175, 0.2);
                color: #6b7280;
                border: 1px solid rgba(156, 163, 175, 0.3);
                border-radius: 12px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton#CloseBtn:hover {
                background: rgba(239, 68, 68, 0.2);
                color: #ef4444;
                border: 1px solid rgba(239, 68, 68, 0.5);
            }
            QPushButton#CloseBtn:pressed {
                background: rgba(239, 68, 68, 0.3);
            }
        """)
        self.close_btn.hide()  # 初始隐藏
        top_layout.addWidget(self.close_btn)
        
        layout.addLayout(top_layout)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setObjectName("ProgressBar")
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        # 现代化进度条样式（参考详情页面风格）
        self.progress_bar.setStyleSheet("""
            QProgressBar#ProgressBar {
                border: none;
                border-radius: 10px;
                background: #f1f5f9;
                text-align: center;
                color: #1e293b;
                font-weight: 600;
                font-size: 11px;
                min-height: 20px;
                padding: 2px;
            }
            QProgressBar#ProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #22c55e, stop:1 #16a34a);
                border-radius: 10px;
                margin: 1px;
            }
        """)
        layout.addWidget(self.progress_bar)
        
        # 状态文本
        self.status_label = QLabel("准备下载...")
        self.status_label.setObjectName("StatusText")
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)
        
        # 时间标签
        self.time_label = QLabel(self.start_time.strftime("%H:%M:%S"))
        self.time_label.setObjectName("TimeLabel")
        layout.addWidget(self.time_label)
        
        self.setLayout(layout)
    
    def update_progress(self, progress: int, status_text: str):
        """更新进度和状态"""
        self.progress_bar.setValue(progress)
        
        # 添加进度图标到状态文本
        if progress < 100 and not ("完成" in status_text or "成功" in status_text):
            if "下载" in status_text:
                icon_text = "⬇️ " + status_text
            elif "解压" in status_text or "安装" in status_text:
                icon_text = "📦 " + status_text
            elif "验证" in status_text:
                icon_text = "🔍 " + status_text
            else:
                icon_text = "🔄 " + status_text
            self.status_label.setText(icon_text)
        else:
            self.status_label.setText(status_text)
        
        # 如果进度达到100%或状态显示完成，标记为完成
        if progress == 100 or "完成" in status_text or "成功" in status_text:
            self.mark_completed()
    
    def mark_completed(self):
        """标记为完成状态"""
        if not self.is_completed:
            self.is_completed = True
            self.progress_bar.setValue(100)
            self.close_btn.show()
            
            # 更新状态文本，添加完成图标
            self.status_label.setText("✅ 安装完成")
            
            # 更新样式
            self.setProperty("completed", True)
            self.style().unpolish(self)
            self.style().polish(self)
    
    def mark_failed(self, error_message: str):
        """标记为失败状态"""
        self.progress_bar.setValue(0)
        self.status_label.setText(f"❌ {error_message}")
        self.close_btn.show()
        
        # 更新样式
        self.setProperty("failed", True)
        self.style().unpolish(self)
        self.style().polish(self)


class DownloadStatusPanel(QWidget):
    """
    下载状态面板主组件
    管理所有下载任务的显示和更新
    """
    
    panel_closed = pyqtSignal()  # 面板关闭信号
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.download_items: Dict[str, DownloadItem] = {}
        self.init_ui()
        self.setup_connections()
    
    def init_ui(self):
        """初始化UI"""
        self.setObjectName("DownloadStatusPanel")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setProperty("class", "DownloadStatusPanel")
        
        # 固定宽度320px，添加现代化样式
        self.setFixedWidth(320)
        
        # 设置现代化面板样式 - 使用!important确保优先级
        self.setStyleSheet("""
            QWidget#DownloadStatusPanel {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #ffffff, stop:1 #f8fafc) !important;
                border: 1px solid #e2e8f0 !important;
                border-radius: 16px !important;
                margin: 8px !important;
            }
            
            /* 确保完全覆盖任何外部样式 */
            QWidget#DownloadStatusPanel[class="DownloadStatusPanel"] {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #ffffff, stop:1 #f8fafc) !important;
                border: 1px solid #e2e8f0 !important;
                border-radius: 16px !important;
            }
        """)
        
        # 确保面板能正确显示圆角（重要：设置窗口标志）
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        
        # 使用日志系统而不是print，确保输出被记录
        import logging
        logger = logging.getLogger('BioNexus.ui_operations')
        logger.info(f"[下载面板] 样式设置完成，objectName: {self.objectName()}")
        
        # 主布局
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 标题栏
        header = self._create_header()
        main_layout.addWidget(header)
        
        # 内容区域（可滚动）
        self.scroll_area = QScrollArea()
        self.scroll_area.setObjectName("DownloadScrollArea")
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # 滚动内容容器
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout()
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(2)
        self.content_layout.addStretch()  # 推送项目到顶部
        
        self.content_widget.setLayout(self.content_layout)
        self.scroll_area.setWidget(self.content_widget)
        main_layout.addWidget(self.scroll_area)
        
        # 空状态提示
        self.empty_label = QLabel("暂无下载任务")
        self.empty_label.setObjectName("EmptyLabel")
        self.empty_label.setAlignment(Qt.AlignCenter)
        self.content_layout.insertWidget(0, self.empty_label)
        
        self.setLayout(main_layout)
    
    def _create_header(self) -> QWidget:
        """创建标题栏"""
        header = QWidget()
        header.setObjectName("DownloadPanelHeader")
        
        # 设置现代化标题栏样式
        header.setStyleSheet("""
            QWidget#DownloadPanelHeader {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #3b82f6, stop:1 #1d4ed8);
                border-radius: 16px 16px 0px 0px;
                padding: 2px;
            }
        """)
        
        layout = QHBoxLayout()
        layout.setContentsMargins(20, 16, 20, 16)
        
        # 标题
        title = QLabel("下载状态")
        title.setObjectName("PanelTitle")
        font = QFont()
        font.setBold(True)
        font.setPointSize(12)
        title.setFont(font)
        # 白色文字，现代化样式
        title.setStyleSheet("""
            QLabel#PanelTitle {
                color: white;
                font-weight: 600;
                font-size: 14px;
            }
        """)
        layout.addWidget(title)
        
        layout.addStretch()
        
        # 清空按钮
        self.clear_btn = QPushButton("清空")
        self.clear_btn.setObjectName("ClearBtn")
        self.clear_btn.clicked.connect(self.clear_completed)
        # 现代化按钮样式
        self.clear_btn.setStyleSheet("""
            QPushButton#ClearBtn {
                background: rgba(255, 255, 255, 0.2);
                color: white;
                border: 1px solid rgba(255, 255, 255, 0.3);
                border-radius: 8px;
                padding: 8px 16px;
                font-weight: 500;
                font-size: 12px;
            }
            QPushButton#ClearBtn:hover {
                background: rgba(255, 255, 255, 0.3);
                border: 1px solid rgba(255, 255, 255, 0.5);
            }
            QPushButton#ClearBtn:pressed {
                background: rgba(255, 255, 255, 0.1);
            }
        """)
        layout.addWidget(self.clear_btn)
        
        # 关闭按钮
        self.close_btn = QPushButton("×")
        self.close_btn.setObjectName("ClosePanelBtn")
        self.close_btn.setFixedSize(28, 28)
        self.close_btn.clicked.connect(self.panel_closed.emit)
        # 现代化关闭按钮样式
        self.close_btn.setStyleSheet("""
            QPushButton#ClosePanelBtn {
                background: rgba(255, 255, 255, 0.2);
                color: white;
                border: 1px solid rgba(255, 255, 255, 0.3);
                border-radius: 14px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton#ClosePanelBtn:hover {
                background: rgba(239, 68, 68, 0.8);
                border: 1px solid rgba(239, 68, 68, 1);
            }
            QPushButton#ClosePanelBtn:pressed {
                background: rgba(220, 38, 38, 0.9);
            }
        """)
        layout.addWidget(self.close_btn)
        
        header.setLayout(layout)
        return header
    
    def setup_connections(self):
        """设置信号连接"""
        pass
    
    @pyqtSlot(str, int, str)
    def add_or_update_download(self, tool_name: str, progress: int, status_text: str):
        """添加或更新下载任务"""
        if tool_name in self.download_items:
            # 更新现有项目
            self.download_items[tool_name].update_progress(progress, status_text)
        else:
            # 创建新项目
            item = DownloadItem(tool_name)
            item.update_progress(progress, status_text)
            item.remove_requested.connect(self.remove_download)
            
            self.download_items[tool_name] = item
            
            # 插入到内容布局中（在stretch之前）
            insert_index = self.content_layout.count() - 1
            self.content_layout.insertWidget(insert_index, item)
            
            # 隐藏空状态提示
            self.empty_label.hide()
    
    @pyqtSlot(str, str)
    def mark_download_failed(self, tool_name: str, error_message: str):
        """标记下载失败"""
        if tool_name in self.download_items:
            self.download_items[tool_name].mark_failed(error_message)
    
    @pyqtSlot(str)
    def remove_download(self, tool_name: str):
        """移除下载项目"""
        if tool_name in self.download_items:
            item = self.download_items[tool_name]
            self.content_layout.removeWidget(item)
            item.deleteLater()
            del self.download_items[tool_name]
            
            # 如果没有项目了，显示空状态提示
            if not self.download_items:
                self.empty_label.show()
    
    @pyqtSlot()
    def clear_completed(self):
        """清空所有已完成的下载"""
        completed_items = []
        for tool_name, item in self.download_items.items():
            if item.is_completed or item.property("failed"):
                completed_items.append(tool_name)
        
        for tool_name in completed_items:
            self.remove_download(tool_name)
    
    def has_active_downloads(self) -> bool:
        """检查是否有活动的下载"""
        return any(not item.is_completed and not item.property("failed") 
                  for item in self.download_items.values())
    
    def get_download_count(self) -> tuple:
        """获取下载计数 (活动, 总数)"""
        active = sum(1 for item in self.download_items.values() 
                    if not item.is_completed and not item.property("failed"))
        total = len(self.download_items)
        return active, total
    
    def add_update_history_item(self, tool_name: str, from_version: str, to_version: str, success: bool):
        """
        添加工具更新历史项
        专门用于显示工具版本更新记录
        """
        update_name = f"{tool_name} 更新"
        if success:
            status_text = f"✅ 从 v{from_version} 更新到 v{to_version}"
            self.add_or_update_download(update_name, 100, status_text)
        else:
            status_text = f"❌ 从 v{from_version} 更新到 v{to_version} 失败"
            self.add_or_update_download(update_name, -1, status_text)
    
    def add_update_check_result(self, found_count: int, is_manual: bool = False):
        """
        添加更新检查结果
        显示检查到的更新数量
        """
        if found_count > 0:
            status_text = f"🔍 发现 {found_count} 个工具更新"
            check_name = "更新检查" + ("（手动）" if is_manual else "")
        else:
            status_text = "🔍 所有工具都是最新版本"
            check_name = "更新检查" + ("（手动）" if is_manual else "")
        
        self.add_or_update_download(check_name, 100, status_text)
    
    def clear_old_history(self, keep_count: int = 20):
        """
        清理旧的历史记录
        保留最近的 keep_count 个记录
        """
        if len(self.download_items) <= keep_count:
            return
        
        # 按时间排序，移除最旧的记录
        items_with_time = [(name, item, item.start_time) 
                          for name, item in self.download_items.items()]
        items_with_time.sort(key=lambda x: x[2], reverse=True)
        
        # 保留最新的 keep_count 个，移除其余的
        for name, item, _ in items_with_time[keep_count:]:
            self.remove_download(name)
    
    def get_update_history_summary(self) -> dict:
        """
        获取更新历史摘要
        返回统计信息
        """
        total_items = len(self.download_items)
        completed_items = sum(1 for item in self.download_items.values() if item.is_completed)
        failed_items = sum(1 for item in self.download_items.values() 
                          if item.property("failed"))
        update_items = sum(1 for name in self.download_items.keys() 
                          if "更新" in name)
        
        return {
            'total_items': total_items,
            'completed_items': completed_items, 
            'failed_items': failed_items,
            'update_items': update_items
        }