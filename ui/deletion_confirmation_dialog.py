#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
删除确认对话框
支持依赖环境智能提示和二次确认功能
"""

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QTextEdit, QCheckBox, QFrame,
                             QScrollArea, QWidget, QMessageBox)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QPixmap, QIcon
from typing import List, Dict
import logging

from utils.storage_calculator import get_storage_calculator
from utils.dependency_manager import get_dependency_manager


class DeletionConfirmationDialog(QDialog):
    """
    删除确认对话框
    显示详细的删除信息，包括依赖环境处理
    """
    
    # 信号定义
    deletion_confirmed = pyqtSignal(list, bool)  # tools_to_delete, cleanup_environments
    
    def __init__(self, tools_to_delete: List[str], parent=None):
        super().__init__(parent)
        self.tools_to_delete = tools_to_delete
        self.cleanup_environments = []
        self.logger = logging.getLogger(__name__)
        
        self._init_ui()
        self._analyze_deletion()
    
    def _init_ui(self):
        """初始化界面"""
        self.setWindowTitle(self.tr("确认删除"))
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.setModal(True)
        self.setFixedSize(500, 400)

        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # 警告标题
        title_layout = QHBoxLayout()

        warning_label = QLabel("⚠️")
        warning_label.setFont(QFont("Microsoft YaHei", 24))
        warning_label.setStyleSheet("color: #f39c12;")

        title_text = QLabel(self.tr("确认删除工具"))
        title_text.setFont(QFont("Microsoft YaHei", 14, QFont.Bold))
        title_text.setStyleSheet("color: #e74c3c;")

        title_layout.addWidget(warning_label)
        title_layout.addWidget(title_text)
        title_layout.addStretch()
        
        layout.addLayout(title_layout)
        
        # 分隔线
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line)
        
        # 工具列表
        tools_label = QLabel(self.tr("将删除以下 {0} 个工具：").format(len(self.tools_to_delete)))
        tools_label.setFont(QFont("Microsoft YaHei", 10, QFont.Bold))
        tools_label.setStyleSheet("color: #2c3e50;")
        layout.addWidget(tools_label)

        # 工具列表显示区域
        tools_text = QTextEdit()
        tools_text.setMaximumHeight(100)
        tools_text.setStyleSheet("""
            QTextEdit {
                border: 1px solid #e0e0e0;
                border-radius: 5px;
                background-color: #f8f9fa;
                font-family: 'Microsoft YaHei';
                font-size: 11px;
                padding: 8px;
            }
        """)

        tools_list_text = "\\n".join(f"• {tool}" for tool in self.tools_to_delete)
        tools_text.setPlainText(tools_list_text)
        tools_text.setReadOnly(True)

        layout.addWidget(tools_text)

        # 空间信息
        self.space_info_label = QLabel(self.tr("正在计算节省空间..."))
        self.space_info_label.setStyleSheet("color: #27ae60; font-weight: bold;")
        layout.addWidget(self.space_info_label)
        
        # 依赖环境信息
        self.dependencies_frame = QFrame()
        self.dependencies_frame.setVisible(False)
        self.dependencies_frame.setStyleSheet("""
            QFrame {
                border: 1px solid #f39c12;
                border-radius: 5px;
                background-color: #fef9e7;
                padding: 10px;
            }
        """)
        dependencies_layout = QVBoxLayout(self.dependencies_frame)

        deps_title = QLabel(self.tr("🔗 依赖环境处理"))
        deps_title.setFont(QFont("Microsoft YaHei", 10, QFont.Bold))
        deps_title.setStyleSheet("color: #f39c12;")
        dependencies_layout.addWidget(deps_title)

        self.dependencies_text = QTextEdit()
        self.dependencies_text.setMaximumHeight(80)
        self.dependencies_text.setStyleSheet("""
            QTextEdit {
                border: none;
                background-color: transparent;
                font-family: 'Microsoft YaHei';
                font-size: 11px;
            }
        """)
        self.dependencies_text.setReadOnly(True)
        dependencies_layout.addWidget(self.dependencies_text)

        self.cleanup_checkbox = QCheckBox(self.tr("同时清理不再需要的运行环境"))
        self.cleanup_checkbox.setChecked(True)
        self.cleanup_checkbox.setStyleSheet("font-weight: bold; color: #e74c3c;")
        dependencies_layout.addWidget(self.cleanup_checkbox)

        layout.addWidget(self.dependencies_frame)

        # 确认复选框
        self.confirm_checkbox = QCheckBox(self.tr("我确认删除上述工具，此操作不可撤销"))
        self.confirm_checkbox.setFont(QFont("Microsoft YaHei", 10))
        self.confirm_checkbox.setStyleSheet("color: #e74c3c; font-weight: bold;")
        self.confirm_checkbox.stateChanged.connect(self._on_confirm_changed)
        layout.addWidget(self.confirm_checkbox)
        
        layout.addStretch()
        
        # 按钮布局
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.cancel_btn = QPushButton(self.tr("取消"))
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
        """)
        self.cancel_btn.clicked.connect(self.reject)

        self.delete_btn = QPushButton(self.tr("确认删除"))
        self.delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
            }
        """)
        self.delete_btn.setEnabled(False)
        self.delete_btn.clicked.connect(self._on_delete_confirmed)
        
        button_layout.addWidget(self.cancel_btn)
        button_layout.addWidget(self.delete_btn)
        
        layout.addLayout(button_layout)
    
    def _analyze_deletion(self):
        """分析删除操作的影响"""
        try:
            calc = get_storage_calculator()
            dep_manager = get_dependency_manager()
            
            # 计算节省空间
            deletion_info = calc.calculate_deletion_savings(self.tools_to_delete)
            
            # 更新空间信息
            tools_size = calc.format_size(deletion_info['tools_size'])
            total_savings = calc.format_size(deletion_info['total_savings'])
            
            if deletion_info['environments_size'] > 0:
                env_size = calc.format_size(deletion_info['environments_size'])
                space_text = self.tr("💾 节省空间: 工具 {0} + 环境 {1} = 总计 {2}").format(tools_size, env_size, total_savings)
            else:
                space_text = self.tr("💾 节省空间: {0}").format(tools_size)

            self.space_info_label.setText(space_text)
            
            # 处理依赖环境
            cleanup_candidates = dep_manager.check_cleanup_candidates(self.tools_to_delete)
            
            if cleanup_candidates:
                self.cleanup_environments = [env.name for env in cleanup_candidates]
                self.dependencies_frame.setVisible(True)

                # 构建依赖信息文本
                deps_text = self.tr("删除这些工具后，以下运行环境将不再被其他工具使用：\n")
                for env in cleanup_candidates:
                    size_str = calc.format_size(env.size)
                    deps_text += f"• {env.name} ({size_str}) - {env.description}\\n"

                deps_text += self.tr("\n💡 建议同时清理这些环境以释放更多空间。")
                self.dependencies_text.setPlainText(deps_text)
            else:
                self.dependencies_frame.setVisible(False)
                self.cleanup_environments = []
            
            # 调整窗口大小
            if cleanup_candidates:
                self.setFixedSize(500, 500)
            else:
                self.setFixedSize(500, 350)
            
        except Exception as e:
            self.logger.error(f"分析删除操作失败: {e}")
            self.space_info_label.setText(self.tr("⚠️ 分析失败，请检查系统状态"))
    
    def _on_confirm_changed(self, state):
        """处理确认复选框状态变化"""
        self.delete_btn.setEnabled(state == Qt.Checked)
    
    def _on_delete_confirmed(self):
        """处理删除确认"""
        try:
            # 最后的安全检查
            if len(self.tools_to_delete) > 5:
                reply = QMessageBox.question(
                    self,
                    self.tr("最终确认"),
                    self.tr("您即将删除 {0} 个工具。\n这是一个批量操作，确定继续吗？").format(len(self.tools_to_delete)),
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                
                if reply != QMessageBox.Yes:
                    return
            
            # 确定是否清理环境
            cleanup_environments = (self.cleanup_checkbox.isChecked() 
                                  if self.dependencies_frame.isVisible() else False)
            
            # 发送确认信号
            self.deletion_confirmed.emit(self.tools_to_delete, cleanup_environments)
            self.accept()
            
        except Exception as e:
            self.logger.error(f"删除确认处理失败: {e}")
            QMessageBox.critical(self, self.tr("错误"), self.tr("操作失败: {0}").format(e))
    
    @classmethod
    def confirm_deletion(cls, tools_to_delete: List[str], parent=None) -> tuple:
        """
        静态方法：显示删除确认对话框
        
        Args:
            tools_to_delete: 要删除的工具列表
            parent: 父窗口
            
        Returns:
            tuple: (confirmed, tools_list, cleanup_environments)
        """
        if not tools_to_delete:
            return False, [], False
        
        dialog = cls(tools_to_delete, parent)
        result_data = {'confirmed': False, 'tools': [], 'cleanup': False}
        
        def on_confirmed(tools, cleanup):
            result_data['confirmed'] = True
            result_data['tools'] = tools
            result_data['cleanup'] = cleanup
        
        dialog.deletion_confirmed.connect(on_confirmed)
        
        dialog.exec_()
        
        return (result_data['confirmed'], 
                result_data['tools'], 
                result_data['cleanup'])


class QuickDeleteDialog(QDialog):
    """
    快速删除对话框
    用于单个工具的快速删除确认
    """
    
    def __init__(self, tool_name: str, parent=None):
        super().__init__(parent)
        self.tool_name = tool_name
        self.setWindowTitle(self.tr("确认删除"))
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.setModal(True)
        self.setFixedSize(350, 150)

        self._init_ui()

    def _init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)

        # 询问文本
        question_label = QLabel(self.tr("确定要删除工具 '{0}' 吗？").format(self.tool_name))
        question_label.setFont(QFont("Microsoft YaHei", 12))
        question_label.setStyleSheet("color: #2c3e50;")
        question_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(question_label)

        warning_label = QLabel(self.tr("此操作不可撤销"))
        warning_label.setFont(QFont("Microsoft YaHei", 10))
        warning_label.setStyleSheet("color: #e74c3c;")
        warning_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(warning_label)
        
        # 按钮
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        cancel_btn = QPushButton(self.tr("取消"))
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
        """)
        cancel_btn.clicked.connect(self.reject)

        delete_btn = QPushButton(self.tr("删除"))
        delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        delete_btn.clicked.connect(self.accept)
        
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(delete_btn)
        
        layout.addLayout(button_layout)
    
    @classmethod
    def confirm_quick_delete(cls, tool_name: str, parent=None) -> bool:
        """
        静态方法：显示快速删除确认对话框
        
        Args:
            tool_name: 工具名称
            parent: 父窗口
            
        Returns:
            bool: 是否确认删除
        """
        dialog = cls(tool_name, parent)
        return dialog.exec_() == QDialog.Accepted