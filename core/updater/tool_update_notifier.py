"""
工具更新通知器 - 处理更新通知和对话框
注意：此模块仅处理第三方工具更新通知，不涉及BioNexus本体更新

功能：
1. 显示工具更新对话框
2. 处理用户选择（更新/跳过/静默）
3. 提供各种通知方式
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QScrollArea, QWidget, QFrame, QCheckBox, QTextEdit,
    QButtonGroup, QRadioButton, QGroupBox, QMessageBox
)
from PyQt5.QtCore import Qt, pyqtSignal, QSize
from PyQt5.QtGui import QFont, QPixmap, QIcon
from typing import List, Dict, Any, Optional
from datetime import datetime

from utils.unified_logger import get_logger


class ToolUpdateDialog(QDialog):
    """
    工具更新对话框
    
    显示可用的工具更新，允许用户选择更新策略
    仅用于第三方生物信息工具，不包括BioNexus软件本体
    """
    
    # 信号定义
    updates_accepted = pyqtSignal(list)        # 接受更新（工具名列表）
    update_skipped = pyqtSignal(str, str, bool)  # 跳过更新（工具名，版本，是否永久）
    update_silenced = pyqtSignal(str, str)     # 静默更新（工具名，版本）
    
    def __init__(self, parent=None, updates: List[Dict[str, Any]] = None, is_manual: bool = False):
        super().__init__(parent)
        
        self.updates = updates or []
        self.is_manual = is_manual
        self.logger = get_logger()
        
        # 对话框配置
        self.setWindowTitle(self.tr("Tool Update Notification"))
        self.setModal(True)
        self.setMinimumSize(600, 400)
        self.resize(800, 600)
        
        # 用户选择状态
        self.selected_updates = set()
        self.skipped_tools = {}  # {tool_name: (version, permanent)}
        
        self._setup_ui()
        self._populate_updates()
    
    def _setup_ui(self):
        """设置用户界面"""
        layout = QVBoxLayout(self)
        
        # 标题区域
        title_frame = self._create_title_section()
        layout.addWidget(title_frame)
        
        # 更新列表区域（滚动）
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        self.updates_container = QWidget()
        self.updates_layout = QVBoxLayout(self.updates_container)
        self.updates_layout.setSpacing(10)
        
        scroll_area.setWidget(self.updates_container)
        layout.addWidget(scroll_area, 1)  # 占用剩余空间
        
        # 底部按钮区域
        buttons_frame = self._create_buttons_section()
        layout.addWidget(buttons_frame)
        
        self.logger.log_runtime("工具更新对话框界面初始化完成")
    
    def _create_title_section(self) -> QFrame:
        """创建标题区域"""
        frame = QFrame()
        frame.setFrameStyle(QFrame.StyledPanel)
        layout = QVBoxLayout(frame)
        
        # 主标题
        title_label = QLabel(self.tr("🔧 Tool updates found"))
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        # 说明文字
        info_text = "以下生物信息学工具有新版本可用。请选择要更新的工具："
        info_label = QLabel(info_text)
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #666; margin: 5px 0;")
        layout.addWidget(info_label)
        
        return frame
    
    def _create_buttons_section(self) -> QFrame:
        """创建底部按钮区域"""
        frame = QFrame()
        frame.setFrameStyle(QFrame.StyledPanel)
        layout = QHBoxLayout(frame)
        
        # 左侧：批量操作
        left_layout = QHBoxLayout()
        
        select_all_btn = QPushButton(self.tr("Select All"))
        select_all_btn.clicked.connect(self._select_all_updates)
        left_layout.addWidget(select_all_btn)
        
        deselect_all_btn = QPushButton(self.tr("Deselect All"))
        deselect_all_btn.clicked.connect(self._deselect_all_updates)
        left_layout.addWidget(deselect_all_btn)
        
        left_layout.addStretch()
        layout.addLayout(left_layout)
        
        # 右侧：主要操作按钮
        right_layout = QHBoxLayout()
        
        # 更新按钮
        self.update_btn = QPushButton(self.tr("Update Selected Now"))
        self.update_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px 16px;
                font-weight: bold;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        self.update_btn.clicked.connect(self._handle_update_selected)
        right_layout.addWidget(self.update_btn)
        
        # 稍后按钮
        later_btn = QPushButton(self.tr("Remind Me Later"))
        later_btn.clicked.connect(self.reject)
        right_layout.addWidget(later_btn)
        
        # 关闭按钮
        close_btn = QPushButton(self.tr("Close"))
        close_btn.clicked.connect(self.reject)
        right_layout.addWidget(close_btn)
        
        layout.addLayout(right_layout)
        
        return frame
    
    def _populate_updates(self):
        """填充更新列表"""
        for i, update in enumerate(self.updates):
            update_widget = self._create_update_item(update, i)
            self.updates_layout.addWidget(update_widget)
        
        # 添加弹性空间
        self.updates_layout.addStretch()
        
        # 默认全选
        self._select_all_updates()
    
    def _create_update_item(self, update: Dict[str, Any], index: int) -> QFrame:
        """创建单个更新项"""
        frame = QFrame()
        frame.setFrameStyle(QFrame.StyledPanel)
        frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                margin: 2px;
            }
        """)
        
        layout = QVBoxLayout(frame)
        layout.setSpacing(8)
        
        # 顶部：工具名称和选择框
        header_layout = QHBoxLayout()
        
        # 选择复选框
        checkbox = QCheckBox()
        checkbox.setObjectName(f"update_checkbox_{index}")
        checkbox.stateChanged.connect(lambda state, idx=index: self._on_selection_changed(idx, state))
        header_layout.addWidget(checkbox)
        
        # 工具信息
        tool_name = update.get('tool_name', 'Unknown')
        current_version = update.get('current_version', 'Unknown')
        latest_version = update.get('latest_version', 'Unknown')
        priority = update.get('priority', 'optional')
        
        # 工具名称
        tool_label = QLabel(f"📦 {tool_name}")
        tool_font = QFont()
        tool_font.setPointSize(12)
        tool_font.setBold(True)
        tool_label.setFont(tool_font)
        header_layout.addWidget(tool_label)
        
        # 优先级标识
        priority_colors = {
            'critical': '#dc3545',
            'recommended': '#ffc107',
            'optional': '#6c757d'
        }
        priority_text = {
            'critical': '🔴 重要更新',
            'recommended': '🟡 推荐更新', 
            'optional': '⚪ 可选更新'
        }
        
        priority_label = QLabel(priority_text.get(priority, self.tr('⚪ Optional')))
        priority_label.setStyleSheet(f"color: {priority_colors.get(priority, '#6c757d')}; font-weight: bold;")
        header_layout.addWidget(priority_label)
        
        header_layout.addStretch()
        layout.addLayout(header_layout)
        
        # 版本信息
        version_layout = QHBoxLayout()
        version_text = f"从 v{current_version} 更新到 v{latest_version}"
        version_label = QLabel(version_text)
        version_label.setStyleSheet("color: #495057; margin-left: 20px;")
        version_layout.addWidget(version_label)
        
        # 文件大小
        size = update.get('size', '未知')
        size_label = QLabel(self.tr("Size: {0}").format(size))
        size_label.setStyleSheet("color: #6c757d;")
        version_layout.addWidget(size_label)
        
        version_layout.addStretch()
        layout.addLayout(version_layout)
        
        # 更新说明（如果有）
        changelog = update.get('changelog', '').strip()
        if changelog:
            changelog_label = QLabel(self.tr("Changelog:"))
            changelog_label.setStyleSheet("font-weight: bold; margin-left: 20px; margin-top: 5px;")
            layout.addWidget(changelog_label)
            
            changelog_text = QTextEdit()
            changelog_text.setPlainText(changelog)
            changelog_text.setMaximumHeight(80)
            changelog_text.setReadOnly(True)
            changelog_text.setStyleSheet("margin-left: 20px; background: white; border: 1px solid #ddd;")
            layout.addWidget(changelog_text)
        
        # 底部操作区域
        actions_layout = QHBoxLayout()
        
        # "不再提示"选项（仅手动模式显示）
        if self.is_manual:
            never_remind_cb = QCheckBox(self.tr("Do not remind again for this version"))
            never_remind_cb.setObjectName(f"never_remind_{index}")
            never_remind_cb.setStyleSheet("margin-left: 20px; color: #6c757d;")
            actions_layout.addWidget(never_remind_cb)
        
        actions_layout.addStretch()
        
        # 跳过按钮
        skip_btn = QPushButton(self.tr("Skip this tool"))
        skip_btn.setStyleSheet("color: #dc3545; background: none; border: 1px solid #dc3545; padding: 4px 8px;")
        skip_btn.clicked.connect(lambda checked, idx=index: self._skip_update(idx))
        actions_layout.addWidget(skip_btn)
        
        layout.addLayout(actions_layout)
        
        return frame
    
    def _on_selection_changed(self, index: int, state: int):
        """处理选择状态变化"""
        tool_name = self.updates[index]['tool_name']
        
        if state == Qt.Checked:
            self.selected_updates.add(tool_name)
        else:
            self.selected_updates.discard(tool_name)
        
        # 更新按钮状态
        self.update_btn.setEnabled(len(self.selected_updates) > 0)
    
    def _select_all_updates(self):
        """全选所有更新"""
        for i in range(len(self.updates)):
            checkbox = self.findChild(QCheckBox, f"update_checkbox_{i}")
            if checkbox:
                checkbox.setChecked(True)
    
    def _deselect_all_updates(self):
        """取消全选"""
        for i in range(len(self.updates)):
            checkbox = self.findChild(QCheckBox, f"update_checkbox_{i}")
            if checkbox:
                checkbox.setChecked(False)
    
    def _skip_update(self, index: int):
        """跳过指定更新"""
        update = self.updates[index]
        tool_name = update['tool_name']
        version = update['latest_version']
        
        # 检查是否勾选了"不再提示"
        permanent = False
        if self.is_manual:
            never_remind_cb = self.findChild(QCheckBox, f"never_remind_{index}")
            if never_remind_cb:
                permanent = never_remind_cb.isChecked()
        
        # 发送跳过信号
        self.update_skipped.emit(tool_name, version, permanent)
        
        # 从界面移除
        self._remove_update_item(index)
        
        self.logger.log_runtime(f"用户跳过工具更新: {tool_name} v{version} (永久: {permanent})")
    
    def _remove_update_item(self, index: int):
        """从界面移除更新项"""
        if 0 <= index < self.updates_layout.count():
            item = self.updates_layout.itemAt(index)
            if item:
                widget = item.widget()
                if widget:
                    widget.setVisible(False)
                    self.updates_layout.removeWidget(widget)
                    widget.deleteLater()
        
        # 从数据中移除
        if 0 <= index < len(self.updates):
            tool_name = self.updates[index]['tool_name']
            self.selected_updates.discard(tool_name)
            del self.updates[index]
        
        # 如果没有更新项了，关闭对话框
        if not self.updates:
            self.accept()
    
    def _handle_update_selected(self):
        """处理更新选中项"""
        if not self.selected_updates:
            QMessageBox.warning(self, "提示", "请至少选择一个工具进行更新！")
            return
        
        # 发送更新接受信号
        self.updates_accepted.emit(list(self.selected_updates))
        
        self.accept()
        self.logger.log_runtime(f"用户选择更新工具: {', '.join(self.selected_updates)}")


class ToolUpdateNotifier(object):
    """
    工具更新通知器
    
    管理各种更新通知方式：对话框、状态栏、系统通知等
    仅用于第三方生物信息工具更新通知
    """
    
    # 使用类属性模拟信号
    update_accepted = None
    update_skipped = None  
    update_silenced = None
    
    def __init__(self, parent=None):
        self.parent = parent
        self.logger = get_logger()
        self.current_dialog = None
        
        # 模拟信号系统（简化版本）
        self._callbacks = {
            'update_accepted': [],
            'update_skipped': [],
            'update_silenced': []
        }
    
    def connect_signal(self, signal_name: str, callback):
        """连接信号回调"""
        if signal_name in self._callbacks:
            self._callbacks[signal_name].append(callback)
    
    def emit_signal(self, signal_name: str, *args):
        """发射信号"""
        if signal_name in self._callbacks:
            for callback in self._callbacks[signal_name]:
                try:
                    callback(*args)
                except Exception as e:
                    self.logger.log_error(f"信号回调执行失败 {signal_name}: {e}")
    
    # 兼容pyqtSignal的属性
    @property
    def update_accepted(self):
        class Signal:
            def connect(self, callback):
                self.notifier.connect_signal('update_accepted', callback)
        
        signal = Signal()
        signal.notifier = self
        return signal
    
    @property  
    def update_skipped(self):
        class Signal:
            def connect(self, callback):
                self.notifier.connect_signal('update_skipped', callback)
        
        signal = Signal()
        signal.notifier = self
        return signal
    
    @property
    def update_silenced(self):
        class Signal:
            def connect(self, callback):
                self.notifier.connect_signal('update_silenced', callback)
        
        signal = Signal()
        signal.notifier = self
        return signal
    
    def show_updates_dialog(self, updates: List[Dict[str, Any]], is_manual: bool = False):
        """显示更新对话框"""
        if self.current_dialog:
            self.current_dialog.close()
        
        self.current_dialog = ToolUpdateDialog(self.parent, updates, is_manual)
        
        # 连接信号
        self.current_dialog.updates_accepted.connect(
            lambda tool_names: self.emit_signal('update_accepted', tool_names)
        )
        self.current_dialog.update_skipped.connect(
            lambda tool, ver, perm: self.emit_signal('update_skipped', tool, ver, perm)  
        )
        self.current_dialog.update_silenced.connect(
            lambda tool, ver: self.emit_signal('update_silenced', tool, ver)
        )
        
        # 显示对话框
        result = self.current_dialog.exec_()
        self.current_dialog = None
        
        self.logger.log_runtime(f"工具更新对话框显示完成 (结果: {result})")
        
        return result
    
    def show_status_notification(self, message: str, duration: int = 3000):
        """在状态栏显示通知"""
        if self.parent and hasattr(self.parent, 'statusBar'):
            self.parent.statusBar().showMessage(message, duration)
    
    def show_tray_notification(self, title: str, message: str):
        """显示系统托盘通知（如果支持）"""
        # 这里可以实现系统托盘通知
        # 暂时记录日志
        self.logger.log_runtime(f"托盘通知: {title} - {message}")
