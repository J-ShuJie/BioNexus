"""
路径迁移确认对话框
用于软件位置变更后，提示用户选择保留原路径还是使用新路径
"""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFrame, QRadioButton, QButtonGroup
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QIcon
from pathlib import Path


class PathMigrationDialog(QDialog):
    """路径迁移确认对话框"""
    
    def __init__(self, old_path: str, new_path: str, setting_name: str, parent=None):
        super().__init__(parent)
        self.old_path = old_path
        self.new_path = new_path
        self.setting_name = setting_name
        self.selected_choice = None  # 用户选择：'keep' 或 'migrate'
        
        self.init_ui()
    
    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle(self.tr("路径迁移确认"))
        self.setMinimumWidth(550)
        self.setWindowFlags(Qt.Dialog | Qt.WindowCloseButtonHint)

        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)

        # 标题
        title_label = QLabel(self.tr("检测到软件位置已变更"))
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)

        # 说明文字
        desc_label = QLabel(
            self.tr("您之前为 <b>{0}</b> 手动设置了路径，但软件位置已发生变更。\n\n请选择如何处理此路径：").format(self._get_setting_display_name())
        )
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #64748b; font-size: 12px; line-height: 1.6;")
        layout.addWidget(desc_label)
        
        # 分隔线
        line1 = QFrame()
        line1.setFrameShape(QFrame.HLine)
        line1.setStyleSheet("background-color: #e5e7eb;")
        layout.addWidget(line1)
        
        # 选项组
        self.button_group = QButtonGroup(self)
        
        # 选项1：保留旧路径
        option1_container = self._create_option_widget(
            self.tr("保留原路径（绝对路径）"),
            self.tr("继续使用: {0}").format(self.old_path),
            "keep",
            recommended=False
        )
        layout.addWidget(option1_container)

        # 选项2：迁移到新路径
        option2_container = self._create_option_widget(
            self.tr("使用新的默认路径（推荐）"),
            self.tr("自动更新为: {0}").format(self.new_path),
            "migrate",
            recommended=True
        )
        layout.addWidget(option2_container)
        
        # 分隔线
        line2 = QFrame()
        line2.setFrameShape(QFrame.HLine)
        line2.setStyleSheet("background-color: #e5e7eb;")
        layout.addWidget(line2)
        
        # 提示信息
        hint_label = QLabel(
            self.tr("💡 提示：选择 \"使用新的默认路径\" 可以让软件路径随版本自动更新，避免每次升级都需要手动调整。")
        )
        hint_label.setWordWrap(True)
        hint_label.setStyleSheet("""
            QLabel {
                background-color: #eff6ff;
                color: #1e40af;
                padding: 12px;
                border-radius: 6px;
                border-left: 3px solid #3b82f6;
                font-size: 11px;
            }
        """)
        layout.addWidget(hint_label)

        # 按钮
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        confirm_btn = QPushButton(self.tr("确认"))
        confirm_btn.setStyleSheet("""
            QPushButton {
                background-color: #3b82f6;
                color: white;
                border: none;
                padding: 10px 24px;
                border-radius: 6px;
                font-size: 13px;
                font-weight: bold;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #2563eb;
            }
            QPushButton:pressed {
                background-color: #1d4ed8;
            }
        """)
        confirm_btn.clicked.connect(self.accept)
        button_layout.addWidget(confirm_btn)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
        # 默认选中推荐选项
        self.button_group.buttons()[1].setChecked(True)
    
    def _create_option_widget(self, title: str, description: str, choice: str, recommended: bool = False):
        """创建选项控件"""
        container = QFrame()
        container.setStyleSheet("""
            QFrame {
                background-color: #f9fafb;
                border: 2px solid #e5e7eb;
                border-radius: 8px;
                padding: 16px;
            }
            QFrame:hover {
                border-color: #3b82f6;
                background-color: #f0f9ff;
            }
        """)
        
        layout = QVBoxLayout()
        layout.setSpacing(8)
        layout.setContentsMargins(12, 12, 12, 12)
        
        # 标题行（单选按钮 + 标题 + 推荐标签）
        title_layout = QHBoxLayout()
        
        radio = QRadioButton()
        radio.setStyleSheet("QRadioButton { font-size: 13px; }")
        radio.setProperty("choice", choice)
        self.button_group.addButton(radio)
        title_layout.addWidget(radio)
        
        title_label = QLabel(title)
        title_label.setStyleSheet("font-weight: bold; font-size: 13px; color: #1f2937;")
        title_layout.addWidget(title_label)
        
        if recommended:
            badge = QLabel(self.tr("推荐"))
            badge.setStyleSheet("""
                QLabel {
                    background-color: #10b981;
                    color: white;
                    padding: 2px 8px;
                    border-radius: 10px;
                    font-size: 10px;
                    font-weight: bold;
                }
            """)
            title_layout.addWidget(badge)
        
        title_layout.addStretch()
        layout.addLayout(title_layout)
        
        # 描述文字
        desc_label = QLabel(description)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("""
            QLabel {
                color: #6b7280;
                font-size: 11px;
                padding-left: 24px;
                font-family: 'Consolas', 'Monaco', monospace;
            }
        """)
        layout.addWidget(desc_label)
        
        container.setLayout(layout)
        
        # 点击整个容器也能选中
        container.mousePressEvent = lambda event: radio.setChecked(True)
        
        return container
    
    def _get_setting_display_name(self) -> str:
        """获取设置项的显示名称"""
        names = {
            "default_install_dir": self.tr("默认安装目录"),
            "conda_env_path": self.tr("Conda环境路径")
        }
        return names.get(self.setting_name, self.setting_name)
    
    def get_user_choice(self) -> str:
        """获取用户选择"""
        checked_button = self.button_group.checkedButton()
        if checked_button:
            return checked_button.property("choice")
        return "migrate"  # 默认迁移
