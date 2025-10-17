"""
响应式设置面板组件 v1.2.1
==============================
🚀 全新响应式设计，适配所有屏幕尺寸

基于DetailPage的响应式系统重构，提供：
- 🎨 现代化卡片式界面设计  
- 📱 完美的多设备适配体验
- 🔧 智能的布局调整算法
- ✨ 流畅的视觉过渡效果

技术栈：ResponsiveDetailPageManager + ResponsiveSettingsCard
确保在任何窗口尺寸下都能完美显示，杜绝内容截断问题。
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QScrollArea, QFrame,
    QFileDialog, QMessageBox, QComboBox, QProgressBar,
    QListWidget, QListWidgetItem, QTextEdit, QSplitter, QSpinBox,
    QLineEdit, QSizePolicy
)
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QFont
from data.config import ConfigManager, Settings
from .responsive_layout import (
    ResponsiveDetailPageManager,
    ResponsiveSettingsCard,
    ResponsiveSettingsItem,
    ResponsiveToggleSwitch,
    IOSToggleSwitch,
    validate_responsive_config
)


class ToggleSwitch(QPushButton):
    """
    自定义开关控件
    模拟iOS/Android的切换开关
    对应HTML中的toggle-switch设计
    """
    
    toggled_signal = pyqtSignal(bool)  # 状态切换信号
    
    def __init__(self, initial_state: bool = False, parent=None):
        super().__init__(parent)
        self.is_active = initial_state
        self.setCheckable(True)
        self.setChecked(initial_state)
        self.init_ui()
    
    def init_ui(self):
        """初始化开关UI"""
        self.setObjectName("ToggleSwitch")
        self.setProperty("class", "ToggleSwitch")
        
        # 设置固定尺寸，对应CSS中的40px x 20px
        self.setFixedSize(40, 20)
        
        # 连接点击事件
        self.clicked.connect(self._on_clicked)
        
        # 更新样式
        self._update_style()
    
    def _on_clicked(self):
        """点击事件处理"""
        self.is_active = self.isChecked()
        self._update_style()
        self.toggled_signal.emit(self.is_active)
    
    def _update_style(self):
        """更新开关样式"""
        if self.is_active:
            self.setStyleSheet("""
                QPushButton {
                    background-color: #2563eb;
                    border: none;
                    border-radius: 10px;
                }
            """)
        else:
            self.setStyleSheet("""
                QPushButton {
                    background-color: #cbd5e1;
                    border: none;
                    border-radius: 10px;
                }
            """)
    
    def set_state(self, active: bool):
        """设置开关状态"""
        self.is_active = active
        self.setChecked(active)
        self._update_style()


class SettingItem(QWidget):
    """
    设置项组件
    包含设置标签和对应的控件（开关或按钮）
    对应HTML中的setting-item结构
    """
    
    def __init__(self, label_text: str, control_widget: QWidget, parent=None):
        super().__init__(parent)
        self.label_text = label_text
        self.control_widget = control_widget
        self.init_ui()
    
    def init_ui(self):
        """初始化设置项UI"""
        self.setObjectName("SettingItem")
        self.setProperty("class", "SettingItem")
        
        # 水平布局：左侧标签，右侧控件
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 10, 0, 10)
        
        # 设置标签
        label = QLabel(self.label_text)
        label.setObjectName("SettingLabel")
        label.setProperty("class", "SettingLabel")
        # 设置标签使用9px基础字体
        label_font = QFont()
        label_font.setPointSize(9)
        label.setFont(label_font)
        layout.addWidget(label)
        
        layout.addStretch()  # 推送控件到右侧
        
        # 控制控件
        layout.addWidget(self.control_widget)
        
        self.setLayout(layout)
        
        # 添加底部分割线样式
        self.setStyleSheet("""
            QWidget#SettingItem {
                border-bottom: 1px solid #e2e8f0;
                padding: 10px 0px;
            }
            QWidget#SettingItem:last-child {
                border-bottom: none;
            }
        """)


class SettingsPanel(QWidget):
    """
    响应式设置面板主组件 v1.2.1
    =================================
    🚀 基于ResponsiveDetailPageManager重构
    
    核心特性：
    - 🎨 现代化卡片式设计
    - 📱 完美的多设备适配  
    - 🔧 智能布局调整算法
    - ✨ 流畅的视觉过渡
    - 🛡️ 防截断响应式系统
    
    技术栈：使用与DetailPage相同的响应式基础设施
    """
    
    # 信号定义 - 设置变更通知
    setting_changed = pyqtSignal(str, object)  # 设置名称, 新值
    directory_select_requested = pyqtSignal(str)  # 目录选择请求, 设置名称
    
    def __init__(self, config_manager: ConfigManager, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.setting_switches = {}  # 存储开关控件的引用
        self.init_ui()
        self.setup_connections()
        self.load_current_settings()
    
    def init_ui(self):
        """
        初始化响应式用户界面
        🚀 使用ResponsiveDetailPageManager确保完美适配
        """
        # 设置主容器属性
        self.setObjectName("ResponsiveSettingsPanel")
        self.setAttribute(Qt.WA_StyledBackground, True)
        
        # 🔥 关键：使用ResponsiveDetailPageManager创建响应式滚动系统
        scroll_area, content_container = ResponsiveDetailPageManager.create_responsive_detail_page()
        
        # 设置背景色，与DetailPage保持一致的视觉风格
        scroll_area.setStyleSheet("QScrollArea { background-color: #f8fafc; }")
        content_container.setStyleSheet("QWidget { background-color: transparent; }")
        
        # 将响应式滚动区域添加到主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll_area)
        
        # 🎨 创建现代化卡片式设置分组
        self._create_responsive_general_settings(content_container)
        self._create_responsive_language_settings(content_container)
        self._create_responsive_environment_settings(content_container)
        self._create_responsive_advanced_settings(content_container)
        self._create_responsive_storage_settings(content_container)
        self._create_responsive_storage_manager(content_container)  # 新增存储管理
        self._create_responsive_tool_update_settings(content_container)
        
        # 添加弹性空间
        content_container.layout.addStretch()
    
    def _create_responsive_general_settings(self, content_container: QWidget):
        """
        创建响应式常规设置卡片
        """
        # 创建现代化卡片容器
        general_card = ResponsiveSettingsCard("常规设置", content_container)
        content_container.add_section(general_card)
        
        # 自动检查更新设置
        auto_update_switch = IOSToggleSwitch()
        auto_update_item = ResponsiveSettingsItem(
            "自动检查更新", 
            auto_update_switch,
            "启用后将在后台自动检查软件和工具更新",
            general_card
        )
        general_card.add_setting_item(auto_update_item)
        self.setting_switches["auto_update"] = auto_update_switch
        
        # 启动时检查工具状态设置
        check_status_switch = IOSToggleSwitch()
        check_status_item = ResponsiveSettingsItem(
            "启动时检查工具状态", 
            check_status_switch,
            "在应用启动时自动检查所有已安装工具的状态",
            general_card
        )
        general_card.add_setting_item(check_status_item)
        self.setting_switches["check_tool_status_on_startup"] = check_status_switch
        
        # 显示详细安装日志设置
        detailed_log_switch = IOSToggleSwitch()
        detailed_log_item = ResponsiveSettingsItem(
            "显示详细安装日志", 
            detailed_log_switch,
            "安装过程中显示详细的技术日志信息",
            general_card
        )
        general_card.add_setting_item(detailed_log_item)
        self.setting_switches["show_detailed_install_log"] = detailed_log_switch
    
    def _create_responsive_language_settings(self, content_container: QWidget):
        """
        创建响应式语言设置卡片
        """
        # 创建现代化卡片容器
        language_card = ResponsiveSettingsCard("语言设置", content_container)
        content_container.add_section(language_card)
        
        # 界面语言选择器
        language_combo = QComboBox()
        language_combo.addItem("简体中文", "zh_CN")
        language_combo.addItem("English", "en_US")
        language_combo.setObjectName("LanguageComboBox")
        language_combo.setStyleSheet("""
            QComboBox {
                padding: 8px 12px;
                border: 1px solid #d1d5db;
                border-radius: 8px;
                background-color: white;
                min-width: 120px;
            }
            QComboBox:hover {
                border-color: #3b82f6;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 20px;
                border-left: none;
            }
        """)
        
        language_item = ResponsiveSettingsItem(
            "界面语言",
            language_combo,
            "选择应用程序的显示语言，重启后生效",
            language_card
        )
        language_card.add_setting_item(language_item)
        self.setting_switches["language"] = language_combo
    
    def _create_responsive_environment_settings(self, content_container: QWidget):
        """
        创建响应式环境设置卡片
        """
        # 创建现代化卡片容器
        env_card = ResponsiveSettingsCard("环境设置", content_container)
        content_container.add_section(env_card)
        
        # 默认安装目录设置
        install_dir_widget = self._create_path_input_widget("default_install_dir")
        install_dir_item = ResponsiveSettingsItem(
            "默认安装目录",
            install_dir_widget,
            "设置所有工具的默认安装位置",
            env_card,
            vertical_layout=True  # 使用垂直布局，让路径控件独占一行
        )
        env_card.add_setting_item(install_dir_item)
        
        # Conda环境路径设置
        conda_path_widget = self._create_path_input_widget("conda_env_path")
        conda_path_item = ResponsiveSettingsItem(
            "Conda环境路径",
            conda_path_widget,
            "指定Conda安装路径，用于基于Python的生物信息学工具",
            env_card,
            vertical_layout=True  # 使用垂直布局，让路径控件独占一行
        )
        env_card.add_setting_item(conda_path_item)
    
    def _create_path_input_widget(self, setting_name: str) -> QWidget:
        """
        创建路径输入控件组合（输入框 + 浏览按钮）
        """
        # 创建容器
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        # 创建路径输入框
        path_input = QLineEdit()
        path_input.setObjectName(f"{setting_name}_input")
        
        # 设置输入框属性，确保长路径能正确显示
        path_input.setMinimumWidth(300)  # 最小宽度
        path_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        
        path_input.setStyleSheet("""
            QLineEdit {
                padding: 10px 12px;
                border: 1px solid #d1d5db;
                border-radius: 6px;
                background-color: #ffffff;
                color: #374151;
                font-size: 12px;
                font-family: 'Consolas', 'Monaco', monospace;
                min-height: 18px;
                selection-background-color: #3b82f6;
            }
            QLineEdit:focus {
                border-color: #3b82f6;
                box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
            }
            QLineEdit:hover {
                border-color: #9ca3af;
            }
        """)
        
        # 设置当前路径值
        current_path = self._get_current_path_value(setting_name)
        path_input.setText(current_path)
        
        # 创建浏览按钮
        browse_btn = QPushButton("浏览...")
        browse_btn.setObjectName(f"{setting_name}_browse")
        browse_btn.setStyleSheet("""
            QPushButton {
                padding: 8px 16px;
                border: 1px solid #d1d5db;
                border-radius: 6px;
                background-color: #f9fafb;
                color: #374151;
                font-weight: 500;
                font-size: 13px;
                min-width: 70px;
            }
            QPushButton:hover {
                background-color: #f3f4f6;
                border-color: #9ca3af;
            }
            QPushButton:pressed {
                background-color: #e5e7eb;
            }
        """)
        
        # 连接信号
        path_input.textChanged.connect(lambda text: self._on_path_changed(setting_name, text))
        browse_btn.clicked.connect(lambda: self._browse_directory(setting_name, path_input))
        
        # 添加到布局
        layout.addWidget(path_input, 1)  # 输入框占据主要空间
        layout.addWidget(browse_btn, 0)  # 按钮固定宽度
        
        # 保存引用以便后续操作
        if not hasattr(self, 'path_inputs'):
            self.path_inputs = {}
        self.path_inputs[setting_name] = path_input
        
        return container
    
    def _get_current_path_value(self, setting_name: str) -> str:
        """获取当前路径设置值"""
        if hasattr(self.config_manager.settings, setting_name):
            path = getattr(self.config_manager.settings, setting_name, "")
            return path if path else ""
        return ""
    
    def _on_path_changed(self, setting_name: str, new_path: str):
        """处理路径输入框内容变更"""
        # 验证路径并保存设置
        import os
        if new_path and os.path.exists(new_path):
            # 路径有效，保存设置
            setattr(self.config_manager.settings, setting_name, new_path)
            self.config_manager.save_settings()
            self.setting_changed.emit(setting_name, new_path)
            
            # 设置正常样式
            if setting_name in self.path_inputs:
                self.path_inputs[setting_name].setStyleSheet("""
                    QLineEdit {
                        padding: 10px 12px;
                        border: 1px solid #d1d5db;
                        border-radius: 6px;
                        background-color: #ffffff;
                        color: #374151;
                        font-size: 12px;
                        font-family: 'Consolas', 'Monaco', monospace;
                        min-height: 18px;
                        selection-background-color: #3b82f6;
                    }
                    QLineEdit:focus {
                        border-color: #3b82f6;
                        box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
                    }
                    QLineEdit:hover {
                        border-color: #9ca3af;
                    }
                """)
        elif new_path:  # 路径不为空但无效
            # 设置错误样式
            if setting_name in self.path_inputs:
                self.path_inputs[setting_name].setStyleSheet("""
                    QLineEdit {
                        padding: 10px 12px;
                        border: 1px solid #ef4444;
                        border-radius: 6px;
                        background-color: #fef2f2;
                        color: #dc2626;
                        font-size: 12px;
                        font-family: 'Consolas', 'Monaco', monospace;
                        min-height: 18px;
                        selection-background-color: #ef4444;
                    }
                    QLineEdit:focus {
                        border-color: #dc2626;
                        box-shadow: 0 0 0 3px rgba(239, 68, 68, 0.1);
                    }
                """)
    
    def _browse_directory(self, setting_name: str, path_input: QLineEdit):
        """打开文件夹选择对话框"""
        current_path = path_input.text() or ""
        
        # 如果当前路径不存在，使用用户主目录
        import os
        if not os.path.exists(current_path):
            current_path = os.path.expanduser("~")
        
        # 打开文件夹选择对话框
        selected_dir = QFileDialog.getExistingDirectory(
            self,
            f"选择{self._get_setting_display_name(setting_name)}",
            current_path,
            QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks
        )
        
        if selected_dir:
            # 更新输入框内容（这会触发 textChanged 信号）
            path_input.setText(selected_dir)
    
    def _create_responsive_advanced_settings(self, content_container: QWidget):
        """
        创建响应式高级设置卡片
        """
        # 创建现代化卡片容器
        advanced_card = ResponsiveSettingsCard("高级选项", content_container)
        content_container.add_section(advanced_card)
        
        # 使用镜像源加速下载设置
        mirror_source_switch = IOSToggleSwitch()
        mirror_source_item = ResponsiveSettingsItem(
            "使用镜像源加速下载", 
            mirror_source_switch,
            "启用中国大陆镜像源，显著提升下载速度",
            advanced_card
        )
        advanced_card.add_setting_item(mirror_source_item)
        self.setting_switches["use_mirror_source"] = mirror_source_switch
        
        # 保留安装包缓存设置
        keep_cache_switch = IOSToggleSwitch()
        keep_cache_item = ResponsiveSettingsItem(
            "保留安装包缓存", 
            keep_cache_switch,
            "保留已下载的安装包，可节省重复下载时间",
            advanced_card
        )
        advanced_card.add_setting_item(keep_cache_item)
        self.setting_switches["keep_install_cache"] = keep_cache_switch
    
    def _create_responsive_storage_manager(self, content_container: QWidget):
        """
        创建响应式存储管理卡片
        """
        from ui.storage_manager_widget import StorageManagerWidget
        
        # 创建现代化卡片容器
        storage_manager_card = ResponsiveSettingsCard("存储管理", content_container)
        content_container.add_section(storage_manager_card)
        
        # 添加说明文字
        note_label = QLabel("管理已安装的生物信息学工具，查看占用空间并进行批量删除")
        note_label.setStyleSheet("""
            QLabel {
                color: #64748b;
                font-size: 11px;
                margin: 8px 0px;
                padding: 8px 12px;
                background-color: #f1f5f9;
                border-radius: 6px;
                border-left: 3px solid #10b981;
            }
        """)
        note_label.setWordWrap(True)
        storage_manager_card.content_layout.addWidget(note_label)
        
        # 存储管理组件
        self.storage_manager = StorageManagerWidget()
        self.storage_manager.setMaximumHeight(400)  # 调整为更紧凑的高度
        storage_manager_card.content_layout.addWidget(self.storage_manager)
        
        # 连接信号
        self.storage_manager.delete_tools_requested.connect(self._on_delete_tools_requested)
    
    def _create_responsive_storage_settings(self, content_container: QWidget):
        """
        创建响应式存储设置卡片
        """
        # 创建现代化卡片容器
        storage_card = ResponsiveSettingsCard("存储设置", content_container)
        content_container.add_section(storage_card)
        
        # 自动清理日志设置
        auto_clean_logs_switch = IOSToggleSwitch()
        auto_clean_logs_item = ResponsiveSettingsItem(
            "自动清理旧日志", 
            auto_clean_logs_switch,
            "自动删顳30天以前的日志文件，节省磁盘空间",
            storage_card
        )
        storage_card.add_setting_item(auto_clean_logs_item)
        self.setting_switches["auto_clean_logs"] = auto_clean_logs_switch
        
        # 最大日志文件大小
        log_size_spinbox = QSpinBox()
        log_size_spinbox.setRange(1, 100)
        log_size_spinbox.setSuffix(" MB")
        log_size_spinbox.setValue(10)
        log_size_spinbox.setStyleSheet("""
            QSpinBox {
                padding: 8px 12px;
                border: 1px solid #d1d5db;
                border-radius: 8px;
                background-color: white;
                min-width: 80px;
            }
            QSpinBox:hover {
                border-color: #3b82f6;
            }
        """)
        
        log_size_item = ResponsiveSettingsItem(
            "单个日志文件最大大小",
            log_size_spinbox,
            "设置单个日志文件的最大大小，超过后自动轮转",
            storage_card
        )
        storage_card.add_setting_item(log_size_item)
        self.setting_switches["max_log_size"] = log_size_spinbox
    
    def _create_responsive_tool_update_settings(self, content_container: QWidget):
        """
        创建响应式工具更新设置卡片
        注意：仅管理第三方工具更新，不涉及BioNexus本体更新
        """
        # 创建现代化卡片容器
        update_card = ResponsiveSettingsCard("工具更新设置", content_container)
        content_container.add_section(update_card)
        
        # 添加说明文字
        note_label = QLabel("注意：此设置仅管理第三方生物信息工具更新（如FastQC、BLAST等）")
        note_label.setStyleSheet("""
            QLabel {
                color: #64748b;
                font-size: 11px;
                font-style: italic;
                margin: 8px 0px;
                padding: 8px 12px;
                background-color: #f1f5f9;
                border-radius: 6px;
                border-left: 3px solid #3b82f6;
            }
        """)
        note_label.setWordWrap(True)
        update_card.content_layout.addWidget(note_label)
        
        # 更新模式选择
        self.update_mode_combo = QComboBox()
        self.update_mode_combo.addItems(["自动更新", "手动更新"])
        self.update_mode_combo.setStyleSheet("""
            QComboBox {
                padding: 8px 12px;
                border: 1px solid #d1d5db;
                border-radius: 8px;
                background-color: white;
                min-width: 120px;
            }
            QComboBox:hover {
                border-color: #3b82f6;
            }
        """)
        self.update_mode_combo.currentTextChanged.connect(self._on_update_mode_changed)
        
        update_mode_item = ResponsiveSettingsItem(
            "更新模式",
            self.update_mode_combo,
            "选择工具更新的处理方式：自动后台更新或手动确认更新",
            update_card
        )
        update_card.add_setting_item(update_mode_item)
        self.setting_switches["update_mode"] = self.update_mode_combo
        
        # 检查频率设置
        self.check_frequency_combo = QComboBox()
        self.check_frequency_combo.addItems(["每天", "每3天", "每周", "每2周"])
        self.check_frequency_combo.setStyleSheet("""
            QComboBox {
                padding: 8px 12px;
                border: 1px solid #d1d5db;
                border-radius: 8px;
                background-color: white;
                min-width: 100px;
            }
            QComboBox:hover {
                border-color: #3b82f6;
            }
        """)
        
        check_frequency_item = ResponsiveSettingsItem(
            "检查频率",
            self.check_frequency_combo,
            "设置自动检查工具更新的时间间隔",
            update_card
        )
        update_card.add_setting_item(check_frequency_item)
        self.setting_switches["check_frequency"] = self.check_frequency_combo
        
        # 显示通知设置（手动模式专用）
        self.show_notification_switch = IOSToggleSwitch()
        notification_item = ResponsiveSettingsItem(
            "显示更新通知",
            self.show_notification_switch,
            "当发现工具更新时显示桌面通知（仅手动模式）",
            update_card
        )
        update_card.add_setting_item(notification_item)
        self.setting_switches["tool_update_show_notification"] = self.show_notification_switch
        
        # 立即检查按钮
        check_now_btn = QPushButton("立即检查工具更新")
        check_now_btn.setStyleSheet("""
            QPushButton {
                padding: 10px 20px;
                border: 1px solid #3b82f6;
                border-radius: 8px;
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, 
                                           stop: 0 #3b82f6, 
                                           stop: 1 #1e40af);
                color: white;
                font-weight: 600;
                font-size: 12px;
            }
            QPushButton:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, 
                                           stop: 0 #2563eb, 
                                           stop: 1 #1e3a8a);
                box-shadow: 0px 2px 4px rgba(59, 130, 246, 0.3);
            }
            QPushButton:pressed {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, 
                                           stop: 0 #1e40af, 
                                           stop: 1 #1e3a8a);
            }
        """)
        check_now_btn.clicked.connect(self._check_updates_now)
        
        check_now_item = ResponsiveSettingsItem(
            "手动检查更新",
            check_now_btn,
            "立即检查所有已安装工具是否有新版本可用",
            update_card
        )
        update_card.add_setting_item(check_now_item)
        
        # 初始化显示状态
        self._on_update_mode_changed("自动更新")
    
    def setup_connections(self):
        """
        设置信号连接
        对应JavaScript中的设置页面事件监听器
        """
        # 开关控件事件连接
        for setting_name, switch in self.setting_switches.items():
            # 检查是否是响应式开关
            if hasattr(switch, 'toggled_signal'):
                switch.toggled_signal.connect(
                    lambda value, name=setting_name: self._on_setting_changed(name, value)
                )
            elif hasattr(switch, 'toggled'):
                switch.toggled.connect(
                    lambda value, name=setting_name: self._on_setting_changed(name, value)
                )
        
        # 目录选择按钮事件连接
        for button in self.findChildren(QPushButton):
            setting_name = button.property("setting")
            if setting_name:
                button.clicked.connect(
                    lambda checked, name=setting_name: self._on_directory_select(name)
                )
    
    def _on_setting_changed(self, setting_name: str, value: bool):
        """
        设置变更处理
        对应JavaScript中的设置变更处理
        """
        # 更新配置管理器中的设置
        self.config_manager.update_setting(setting_name, value)
        
        # 发出设置变更信号
        self.setting_changed.emit(setting_name, value)
        
        print(f"设置变更: \"{setting_name}\" = {value}")
    
    def _on_directory_select(self, setting_name: str):
        """
        目录选择处理
        对应JavaScript中的文件选择对话框
        """
        # 获取当前设置值
        current_path = getattr(self.config_manager.settings, setting_name, "")
        
        # 打开目录选择对话框
        directory = QFileDialog.getExistingDirectory(
            self, 
            f"选择{self._get_setting_display_name(setting_name)}", 
            current_path
        )
        
        if directory:
            # 更新配置
            self.config_manager.update_setting(setting_name, directory)
            
            # 发出设置变更信号
            self.setting_changed.emit(setting_name, directory)
            
            # 显示成功消息
            QMessageBox.information(
                self, 
                "设置更新", 
                f"{self._get_setting_display_name(setting_name)}已更新为:\n{directory}"
            )
            
            print(f"目录设置更新: \"{setting_name}\" = {directory}")
    
    def _get_setting_display_name(self, setting_name: str) -> str:
        """获取设置项的显示名称"""
        name_map = {
            "default_install_dir": "默认安装目录",
            "conda_env_path": "Conda环境路径"
        }
        return name_map.get(setting_name, setting_name)
    
    def _on_update_mode_changed(self, mode_text: str):
        """
        更新模式变更处理
        根据选择的模式显示或隐藏相关设置
        """
        is_manual = (mode_text == "手动更新")
        
        # 根据模式显示/隐藏通知设置
        if hasattr(self, 'show_notification_switch'):
            # 手动模式才显示通知设置
            notification_item = self.show_notification_switch.parent()
            if notification_item:
                notification_item.setVisible(is_manual)
        
        # 检查频率在自动模式下才有意义
        if hasattr(self, 'check_frequency_combo'):
            frequency_item = self.check_frequency_combo.parent()
            if frequency_item:
                frequency_item.setVisible(not is_manual)
    
    def _check_updates_now(self):
        """
        立即检查更新按钮处理
        """
        # 这里应该调用工具更新检查逻辑
        # 暂时显示一个信息对话框
        QMessageBox.information(
            self,
            "检查更新",
            "正在检查工具更新...\n\n此功能将在后续版本中完善。"
        )
    
    def load_current_settings(self):
        """
        加载当前设置值到UI控件
        对应JavaScript中从配置文件加载设置
        """
        settings = self.config_manager.settings
        
        # 更新开关状态
        for setting_name, control in self.setting_switches.items():
            # 处理不同类型的控件
            if isinstance(control, (ResponsiveToggleSwitch, IOSToggleSwitch, ToggleSwitch)):
                # 开关控件使用set_state方法
                if setting_name.startswith('tool_update_'):
                    # 处理工具更新设置
                    setting_key = setting_name.replace('tool_update_', '')
                    if hasattr(settings, 'tool_update') and settings.tool_update:
                        value = settings.tool_update.get(setting_key, False)
                        control.set_state(value)
                elif hasattr(settings, setting_name):
                    value = getattr(settings, setting_name)
                    control.set_state(value)
            elif isinstance(control, QComboBox):
                # 下拉框使用setCurrentText或setCurrentIndex
                if setting_name == 'language' and hasattr(settings, 'language'):
                    # 语言设置特殊处理
                    language_map = {
                        'zh_CN': '简体中文',
                        'en_US': 'English'
                    }
                    current_lang = getattr(settings, 'language', 'zh_CN')
                    display_text = language_map.get(current_lang, '简体中文')
                    control.setCurrentText(display_text)
                elif setting_name == 'update_mode':
                    # 工具更新模式设置
                    if hasattr(settings, 'tool_update') and settings.tool_update:
                        mode_value = settings.tool_update.get('mode', 'manual')
                        display_text = '自动更新' if mode_value == 'auto' else '手动更新'
                        control.setCurrentText(display_text)
                    else:
                        control.setCurrentText('手动更新')  # 默认手动模式
                elif setting_name == 'check_frequency':
                    # 检查频率设置
                    if hasattr(settings, 'tool_update') and settings.tool_update:
                        frequency = settings.tool_update.get('check_frequency', 'weekly')
                        frequency_map = {
                            'daily': '每天',
                            'every_3_days': '每3天',
                            'weekly': '每周',
                            'bi_weekly': '每2周'
                        }
                        display_text = frequency_map.get(frequency, '每周')
                        control.setCurrentText(display_text)
                    else:
                        control.setCurrentText('每周')  # 默认每周
            elif isinstance(control, QSpinBox):
                # 数字输入框使用setValue
                if hasattr(settings, setting_name):
                    value = getattr(settings, setting_name, 10)
                    control.setValue(value)
        
        # 更新语言选择
        if hasattr(self, 'language_combo'):
            language_map = {
                'zh_CN': '中文',
                'en_US': 'English',
                'ja_JP': '日本語',
                'es_ES': 'Español',
                'fr_FR': 'Français'
            }
            current_lang = getattr(settings, 'language', 'zh_CN')
            display_lang = language_map.get(current_lang, '中文')
            self.language_combo.setCurrentText(display_lang)
        
        # 更新工具更新设置
        if hasattr(self, 'update_mode_combo') and hasattr(settings, 'tool_update'):
            update_mode = settings.tool_update.get('update_mode', 'auto')
            mode_text = '自动更新' if update_mode == 'auto' else '手动更新'
            self.update_mode_combo.setCurrentText(mode_text)
            
            # 更新检查频率
            frequency_map = {1: '每天', 3: '每3天', 7: '每周', 14: '每2周'}
            check_freq = settings.tool_update.get('check_frequency', 1)
            freq_text = frequency_map.get(check_freq, '每天')
            self.check_frequency_combo.setCurrentText(freq_text)
    
    def refresh_settings(self):
        """刷新设置显示"""
        self.load_current_settings()
    
    def reset_to_defaults(self):
        """
        重置为默认设置
        对应JavaScript中的恢复默认功能
        """
        reply = QMessageBox.question(
            self, 
            "确认重置", 
            "确定要将所有设置重置为默认值吗？",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # 创建默认设置对象
            default_settings = Settings()
            
            # 更新配置管理器
            self.config_manager._settings = default_settings
            self.config_manager.save_settings()
            
            # 刷新UI显示
            self.load_current_settings()
            
            # 通知设置变更
            for setting_name in ["auto_update", "check_tool_status_on_startup", 
                               "show_detailed_install_log", "use_mirror_source", 
                               "keep_install_cache"]:
                value = getattr(default_settings, setting_name)
                self.setting_changed.emit(setting_name, value)
            
            QMessageBox.information(self, "重置完成", "所有设置已重置为默认值！")
    
    def export_settings(self):
        """
        导出设置配置
        对应JavaScript中的导出配置功能
        """
        file_path, _ = QFileDialog.getSaveFileName(
            self, 
            "导出设置", 
            "bionexus_settings.json", 
            "JSON Files (*.json)"
        )
        
        if file_path:
            try:
                import json
                from dataclasses import asdict
                
                settings_data = asdict(self.config_manager.settings)
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(settings_data, f, ensure_ascii=False, indent=2)
                
                QMessageBox.information(self, "导出成功", f"设置已导出到:\n{file_path}")
                
            except Exception as e:
                QMessageBox.critical(self, "导出失败", f"导出设置时发生错误:\n{str(e)}")
    
    def import_settings(self):
        """
        导入设置配置
        对应JavaScript中的导入配置功能
        """
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "导入设置", 
            "", 
            "JSON Files (*.json)"
        )
        
        if file_path:
            try:
                import json
                
                with open(file_path, 'r', encoding='utf-8') as f:
                    settings_data = json.load(f)
                
                # 更新设置
                for key, value in settings_data.items():
                    if hasattr(self.config_manager.settings, key):
                        setattr(self.config_manager.settings, key, value)
                
                # 保存设置
                self.config_manager.save_settings()
                
                # 刷新UI
                self.load_current_settings()
                
                QMessageBox.information(self, "导入成功", "设置配置已成功导入！")
                
            except Exception as e:
                QMessageBox.critical(self, "导入失败", f"导入设置时发生错误:\n{str(e)}")
    
    def _on_update_mode_changed(self, mode_text: str):
        """处理更新模式变更"""
        is_manual = mode_text == "手动更新"
        
        # 显示/隐藏相关设置控件
        # 自动模式显示检查频率，手动模式显示通知开关
        if hasattr(self, 'check_frequency_combo'):
            # 查找检查频率设置项的父级容器并控制可见性
            frequency_item = self.check_frequency_combo.parent()
            if frequency_item:
                frequency_item.setVisible(not is_manual)
        
        if hasattr(self, 'show_notification_switch'):
            # 查找通知开关设置项的父级容器并控制可见性
            notification_item = self.show_notification_switch.parent()
            if notification_item:
                notification_item.setVisible(is_manual)
        
        # 更新配置
        mode_value = "manual" if is_manual else "auto"
        if hasattr(self.config_manager.settings, 'tool_update'):
            self.config_manager.settings.tool_update['update_mode'] = mode_value
            self.config_manager.save_settings()
    
    def _clean_cache(self):
        """清理下载缓存"""
        reply = QMessageBox.question(
            self,
            "确认清理",
            "确定要清理所有下载缓存文件吗？\n这将释放磁盘空间，但可能需要重新下载工具。",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                import shutil
                from pathlib import Path
                
                # 清理临时目录
                temp_dir = Path("temp")
                if temp_dir.exists():
                    shutil.rmtree(temp_dir)
                    temp_dir.mkdir()
                
                # 清理下载缓存目录 
                cache_dir = Path("downloads_cache")
                if cache_dir.exists():
                    shutil.rmtree(cache_dir)
                    cache_dir.mkdir()
                
                QMessageBox.information(self, "清理完成", "下载缓存已清理完成！")
                
                # 刷新存储信息显示
                self._update_storage_info()
                
            except Exception as e:
                QMessageBox.critical(self, "清理失败", f"清理缓存时发生错误:\n{str(e)}")
    
    def _update_storage_info(self):
        """更新存储使用信息"""
        try:
            from pathlib import Path
            import os
            
            def get_dir_size(path):
                """计算目录大小"""
                if not path.exists():
                    return 0
                total = 0
                try:
                    for entry in os.scandir(path):
                        if entry.is_file():
                            total += entry.stat().st_size
                        elif entry.is_dir():
                            total += get_dir_size(Path(entry.path))
                except (OSError, FileNotFoundError):
                    pass
                return total
            
            def format_size(bytes_size):
                """格式化文件大小"""
                for unit in ['B', 'KB', 'MB', 'GB']:
                    if bytes_size < 1024.0:
                        return f"{bytes_size:.1f} {unit}"
                    bytes_size /= 1024.0
                return f"{bytes_size:.1f} TB"
            
            # 计算BioNexus总占用
            base_path = Path(".")
            total_size = get_dir_size(base_path)
            self.disk_usage_label.setText(format_size(total_size))
            
            # 计算缓存大小
            cache_size = 0
            cache_dirs = [Path("temp"), Path("downloads_cache"), Path("envs_cache")]
            for cache_dir in cache_dirs:
                if cache_dir.exists():
                    cache_size += get_dir_size(cache_dir)
            
            self.cache_size_label.setText(format_size(cache_size))
            
            # 更新已安装工具列表
            self._update_installed_tools_list()
            
        except Exception as e:
            print(f"更新存储信息失败: {e}")
            self.disk_usage_label.setText("计算失败")
            self.cache_size_label.setText("计算失败")
    
    def _update_installed_tools_list(self):
        """更新已安装工具列表"""
        try:
            from pathlib import Path
            import os
            
            def format_size(bytes_size):
                """格式化文件大小"""
                for unit in ['B', 'KB', 'MB', 'GB']:
                    if bytes_size < 1024.0:
                        return f"{bytes_size:.1f} {unit}"
                    bytes_size /= 1024.0
                return f"{bytes_size:.1f} TB"
            
            def get_dir_size(path):
                """计算目录大小"""
                if not path.exists():
                    return 0
                total = 0
                try:
                    for entry in os.scandir(path):
                        if entry.is_file():
                            total += entry.stat().st_size
                        elif entry.is_dir():
                            total += get_dir_size(Path(entry.path))
                except (OSError, FileNotFoundError):
                    pass
                return total
            
            self.installed_tools_list.clear()
            
            # 扫描已安装工具目录
            tools_dir = Path("installed_tools")
            if tools_dir.exists():
                for tool_dir in tools_dir.iterdir():
                    if tool_dir.is_dir():
                        tool_name = tool_dir.name
                        tool_size = get_dir_size(tool_dir)
                        
                        # 创建列表项
                        item_text = f"📦 {tool_name} - {format_size(tool_size)}"
                        item = QListWidgetItem(item_text)
                        self.installed_tools_list.addItem(item)
            
            # 如果没有已安装工具
            if self.installed_tools_list.count() == 0:
                item = QListWidgetItem("暂无已安装的工具")
                item.setFlags(item.flags() & ~Qt.ItemIsEnabled)
                self.installed_tools_list.addItem(item)
                
        except Exception as e:
            print(f"更新工具列表失败: {e}")
    
    def _check_updates_now(self):
        """立即检查工具更新（无论结果如何都会弹窗显示结果）"""
        # 发送信号给主窗口开始检查更新
        # 检查完成后会自动弹窗显示结果（有更新显示详情，没更新显示"都是最新版本"）
        self.setting_changed.emit("check_updates_now", True)
    
    def _on_delete_tools_requested(self, tool_names: list):
        """处理工具删除请求"""
        if not tool_names:
            return
        
        try:
            from ui.deletion_confirmation_dialog import DeletionConfirmationDialog
            
            # 显示删除确认对话框
            confirmed, tools_to_delete, cleanup_environments = \
                DeletionConfirmationDialog.confirm_deletion(tool_names, self)
            
            if confirmed:
                self._perform_tool_deletion(tools_to_delete, cleanup_environments)
                
        except Exception as e:
            QMessageBox.critical(self, "错误", f"处理删除请求时发生错误:\n{str(e)}")
    
    def _perform_tool_deletion(self, tool_names: list, cleanup_environments: bool):
        """执行工具删除操作"""
        try:
            import shutil
            from pathlib import Path
            from utils.dependency_manager import get_dependency_manager
            
            # 删除工具文件
            tools_dir = Path(__file__).parent.parent / "installed_tools"
            deleted_tools = []
            failed_tools = []
            
            for tool_name in tool_names:
                tool_path = tools_dir / tool_name
                if tool_path.exists():
                    try:
                        shutil.rmtree(tool_path)
                        deleted_tools.append(tool_name)
                    except Exception as e:
                        failed_tools.append((tool_name, str(e)))
            
            # 清理依赖环境
            cleaned_environments = []
            if cleanup_environments:
                dep_manager = get_dependency_manager()
                cleanup_candidates = dep_manager.check_cleanup_candidates(tool_names)
                
                for env_info in cleanup_candidates:
                    success = dep_manager.cleanup_environment(env_info.name)
                    if success:
                        cleaned_environments.append(env_info.name)
            
            # 更新依赖关系
            dep_manager = get_dependency_manager()
            for tool_name in deleted_tools:
                dep_manager.remove_tool_dependencies(tool_name)
            
            # 刷新存储管理显示
            if hasattr(self, 'storage_manager'):
                self.storage_manager.refresh_data()
            
            # 显示结果
            result_msg = f"成功删除 {len(deleted_tools)} 个工具"
            if cleaned_environments:
                result_msg += f"，清理了 {len(cleaned_environments)} 个环境"
            
            if failed_tools:
                result_msg += f"\n\n删除失败的工具:\n"
                for tool, error in failed_tools:
                    result_msg += f"• {tool}: {error}\n"
            
            if deleted_tools or cleaned_environments:
                QMessageBox.information(self, "删除完成", result_msg)
            else:
                QMessageBox.warning(self, "删除失败", "没有工具被成功删除")
                
        except Exception as e:
            QMessageBox.critical(self, "删除失败", f"删除工具时发生错误:\n{str(e)}")
    
    def check_disk_space_before_install(self, required_size: int = 0) -> bool:
        """
        在安装工具前检查磁盘空间
        
        Args:
            required_size: 预计需要的空间（字节）
            
        Returns:
            bool: 是否可以继续安装
        """
        try:
            from utils.storage_calculator import get_storage_calculator
            
            calc = get_storage_calculator()
            show_warning, warning_msg = calc.should_show_space_warning(required_size)
            
            if show_warning:
                reply = QMessageBox.question(
                    self,
                    "存储空间警告",
                    warning_msg,
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                
                return reply == QMessageBox.Yes
            
            return True
            
        except Exception as e:
            # 检查失败时允许继续安装，但记录错误
            import logging
            logging.error(f"磁盘空间检查失败: {e}")
            return True