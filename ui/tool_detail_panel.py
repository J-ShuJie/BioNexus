"""
工具详情页面组件
宽度：自适应（最小700px）
最小高度：600px
背景色：#f8fafc
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTabWidget, QTextEdit, QGridLayout, QFrame, QScrollArea,
    QDialog, QDialogButtonBox, QSizePolicy
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QPixmap, QPalette, QColor


class ToolDetailDialog(QDialog):
    """工具详情对话框"""
    
    install_requested = pyqtSignal(str)
    launch_requested = pyqtSignal(str)
    
    def __init__(self, tool_data: dict, parent=None):
        super().__init__(parent)
        self.tool_data = tool_data
        self.setWindowTitle(f"{tool_data['name']} - " + self.tr("Tool Details"))
        
        # 宽度自适应，高度固定最小值
        self.setMinimumWidth(700)  # 最小宽度
        self.setMinimumHeight(600)  # 最小高度
        
        # 获取父窗口大小，设置为父窗口的80%宽度
        if parent:
            parent_width = parent.width()
            parent_height = parent.height()
            self.resize(int(parent_width * 0.8), max(600, int(parent_height * 0.8)))
        else:
            self.resize(900, 600)  # 默认大小
            
        self.setStyleSheet("background-color: #f8fafc;")
        self.init_ui()
        
    def init_ui(self):
        """初始化UI"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 创建滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("QScrollArea { border: none; }")
        
        # 内容容器
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(10)
        
        # 1. 顶部概览区
        header_section = self.create_header_section()
        content_layout.addWidget(header_section)
        
        # 2. 统计信息栏
        stats_bar = self.create_stats_bar()
        content_layout.addWidget(stats_bar)
        
        # 3. 主内容区和侧边栏容器
        content_container = QWidget()
        content_container.setMinimumHeight(350)  # 最小高度，允许扩展
        container_layout = QHBoxLayout(content_container)
        container_layout.setContentsMargins(30, 0, 30, 0)
        container_layout.setSpacing(30)
        
        # 3.1 选项卡区域
        tabs_section = self.create_tabs_section()
        container_layout.addWidget(tabs_section)
        
        # 3.2 右侧边栏
        sidebar = self.create_sidebar()
        container_layout.addWidget(sidebar)
        
        content_layout.addWidget(content_container)
        content_layout.addStretch()
        
        # 设置滚动区域内容
        scroll_area.setWidget(content_widget)
        main_layout.addWidget(scroll_area)
        
        # 底部按钮栏
        button_bar = self.create_button_bar()
        main_layout.addWidget(button_bar)
        
    def create_header_section(self):
        """创建顶部概览区"""
        header_widget = QWidget()
        header_widget.setFixedHeight(120)
        header_widget.setStyleSheet("""
            QWidget {
                background-color: white;
                border-radius: 8px;
                margin: 15px;
            }
        """)
        
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(30, 20, 30, 20)
        
        # 左侧信息组
        left_group = QWidget()
        left_layout = QHBoxLayout(left_group)
        left_layout.setSpacing(16)
        
        # 工具图标
        icon_label = QLabel()
        icon_label.setFixedSize(64, 64)
        icon_colors = {
            "quality": "#3b82f6",
            "sequence": "#10b981",
            "rnaseq": "#f59e0b",
            "genomics": "#8b5cf6",
            "phylogeny": "#ec4899"
        }
        color = icon_colors.get(self.tool_data.get('category', 'quality'), "#64748b")
        icon_label.setStyleSheet(f"""
            background-color: {color};
            border-radius: 12px;
            color: white;
            font-size: 24px;
            font-weight: bold;
        """)
        icon_label.setText(self.tool_data['name'][:2])
        icon_label.setAlignment(Qt.AlignCenter)
        
        # 工具基本信息
        info_widget = QWidget()
        info_layout = QVBoxLayout(info_widget)
        info_layout.setSpacing(4)
        
        # 工具名称
        name_label = QLabel(self.tool_data['name'])
        name_font = QFont()
        name_font.setPointSize(18)
        name_font.setBold(True)
        name_label.setFont(name_font)
        name_label.setStyleSheet("color: #1e293b;")
        
        # 版本和更新时间
        version_label = QLabel(self.tr("v{0} · Bioinformatics Tool").format(self.tool_data.get('version', 'N/A')))
        version_label.setStyleSheet("font-size: 12px; color: #64748b;")
        
        # 分类标签
        category_label = QLabel(self._get_category_display())
        category_label.setStyleSheet("""
            background-color: #f1f5f9;
            color: #475569;
            padding: 2px 12px;
            border-radius: 11px;
            font-size: 11px;
        """)
        category_label.setFixedHeight(22)
        
        info_layout.addWidget(name_label)
        info_layout.addWidget(version_label)
        info_layout.addWidget(category_label)
        
        left_layout.addWidget(icon_label)
        left_layout.addWidget(info_widget)
        left_layout.addStretch()
        
        # 右侧按钮组
        right_group = QWidget()
        right_layout = QHBoxLayout(right_group)
        right_layout.setSpacing(12)
        
        # 主操作按钮
        if self.tool_data['status'] == 'installed':
            main_btn = QPushButton(self.tr("🚀 Launch Tool"))
            main_btn.setFixedSize(120, 40)
            main_btn.setStyleSheet("""
                QPushButton {
                    background-color: #2563eb;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    font-size: 14px;
                    font-weight: 500;
                }
                QPushButton:hover {
                    background-color: #1d4ed8;
                }
            """)
            main_btn.clicked.connect(lambda: self.launch_requested.emit(self.tool_data['name']))
        else:
            main_btn = QPushButton(self.tr("📦 Install"))
            main_btn.setFixedSize(120, 40)
            main_btn.setStyleSheet("""
                QPushButton {
                    background-color: #10b981;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    font-size: 14px;
                    font-weight: 500;
                }
                QPushButton:hover {
                    background-color: #059669;
                }
            """)
            main_btn.clicked.connect(lambda: self.install_requested.emit(self.tool_data['name']))
        
        # 次要按钮
        docs_btn = QPushButton("📖")
        docs_btn.setFixedSize(40, 40)
        docs_btn.setToolTip(self.tr("View Documentation"))
        docs_btn.setStyleSheet("""
            QPushButton {
                background-color: #f1f5f9;
                border: none;
                border-radius: 6px;
                font-size: 18px;
            }
            QPushButton:hover {
                background-color: #e2e8f0;
            }
        """)
        
        github_btn = QPushButton("⚙")
        github_btn.setFixedSize(40, 40)
        github_btn.setToolTip("GitHub")
        github_btn.setStyleSheet("""
            QPushButton {
                background-color: #f1f5f9;
                border: none;
                border-radius: 6px;
                font-size: 18px;
            }
            QPushButton:hover {
                background-color: #e2e8f0;
            }
        """)
        
        right_layout.addWidget(main_btn)
        right_layout.addWidget(docs_btn)
        right_layout.addWidget(github_btn)
        
        header_layout.addWidget(left_group)
        header_layout.addWidget(right_group)
        
        return header_widget
        
    def create_stats_bar(self):
        """创建统计信息栏"""
        stats_widget = QWidget()
        stats_widget.setFixedHeight(80)
        stats_layout = QHBoxLayout(stats_widget)
        stats_layout.setContentsMargins(30, 10, 30, 10)
        stats_layout.setSpacing(15)
        
        # 统计数据
        stats_data = [
            {"label": "安装状态", "value": "已安装" if self.tool_data['status'] == 'installed' else "未安装", 
             "color": "#10b981" if self.tool_data['status'] == 'installed' else "#f59e0b"},
            {"label": "磁盘占用", "value": self.tool_data.get('disk_usage', 'N/A'), "color": "#475569"},
            {"label": "使用次数", "value": "暂无数据", "color": "#475569"},
            {"label": "上次使用", "value": "暂无数据", "color": "#475569"},
            {"label": "兼容系统", "value": "全平台", "color": "#2563eb"}
        ]
        
        for stat in stats_data:
            stat_card = self.create_stat_card(stat)
            stats_layout.addWidget(stat_card)
            
        return stats_widget
        
    def create_stat_card(self, stat_data):
        """创建统计卡片"""
        card = QWidget()
        card.setFixedSize(156, 60)
        card.setStyleSheet("""
            QWidget {
                background-color: white;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
            }
        """)
        
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(12, 8, 12, 8)
        card_layout.setSpacing(2)
        
        # 标签
        label = QLabel(stat_data['label'])
        label.setStyleSheet("font-size: 11px; color: #94a3b8;")
        
        # 值
        value = QLabel(stat_data['value'])
        value.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {stat_data['color']};")
        
        card_layout.addWidget(label)
        card_layout.addWidget(value)
        
        return card
        
    def create_tabs_section(self):
        """创建选项卡区域"""
        tabs = QTabWidget()
        tabs.setMinimumHeight(320)  # 只固定高度，宽度自适应
        tabs.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        tabs.setStyleSheet("""
            QTabWidget::pane {
                background-color: white;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
            }
            QTabBar::tab {
                padding: 8px 16px;
                margin-right: 4px;
                background-color: #f8fafc;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
            }
            QTabBar::tab:selected {
                background-color: white;
                border-bottom: 2px solid #2563eb;
            }
        """)
        
        # Tab 1: 功能介绍
        overview_tab = self.create_overview_tab()
        tabs.addTab(overview_tab, self.tr("Overview"))
        
        # Tab 2: 技术规格
        tech_tab = self.create_tech_tab()
        tabs.addTab(tech_tab, self.tr("Technical Specs"))
        
        # Tab 3: 使用说明
        usage_tab = self.create_usage_tab()
        tabs.addTab(usage_tab, self.tr("Usage Guide"))
        
        # Tab 4: 版本历史
        version_tab = self.create_version_tab()
        tabs.addTab(version_tab, self.tr("Version History"))
        
        return tabs
        
    def create_overview_tab(self):
        """创建功能介绍选项卡"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 描述文本
        description = QTextEdit()
        description.setReadOnly(True)
        description.setPlainText(self.tool_data.get('description', '暂无书写，占位符，日后增添'))
        description.setStyleSheet("""
            QTextEdit {
                border: none;
                font-size: 13px;
                line-height: 1.6;
                color: #475569;
                background-color: transparent;
            }
        """)
        
        # 功能列表
        features_title = QLabel(self.tr("Main Features"))
        features_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #1e293b; margin-top: 16px;")
        
        features_text = QTextEdit()
        features_text.setReadOnly(True)
        features_text.setPlainText(self._get_features_text())
        features_text.setMaximumHeight(100)
        features_text.setStyleSheet("""
            QTextEdit {
                border: none;
                font-size: 12px;
                color: #475569;
                background-color: transparent;
            }
        """)
        
        layout.addWidget(description)
        layout.addWidget(features_title)
        layout.addWidget(features_text)
        layout.addStretch()
        
        return tab
        
    def create_tech_tab(self):
        """创建技术规格选项卡"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 规格信息网格
        specs_grid = QGridLayout()
        specs_grid.setSpacing(12)
        
        specs = self._get_tech_specs()
        
        for i, (label, value) in enumerate(specs):
            label_widget = QLabel(label)
            label_widget.setStyleSheet("font-size: 12px; color: #64748b; font-weight: 500;")
            value_widget = QLabel(value)
            value_widget.setStyleSheet("font-size: 12px; color: #1e293b;")
            specs_grid.addWidget(label_widget, i, 0)
            specs_grid.addWidget(value_widget, i, 1)
            
        layout.addLayout(specs_grid)
        layout.addStretch()
        
        return tab
        
    def create_usage_tab(self):
        """创建使用说明选项卡"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)
        
        usage_text = QTextEdit()
        usage_text.setReadOnly(True)
        usage_text.setPlainText("暂无书写，占位符，日后增添\n\n使用说明将包含：\n• 基本用法\n• 参数说明\n• 示例命令\n• 常见问题")
        usage_text.setStyleSheet("""
            QTextEdit {
                border: none;
                font-size: 12px;
                color: #475569;
                background-color: transparent;
            }
        """)
        
        layout.addWidget(usage_text)
        
        return tab
        
    def create_version_tab(self):
        """创建版本历史选项卡"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)
        
        version_text = QTextEdit()
        version_text.setReadOnly(True)
        version_text.setPlainText(f"当前版本: {self.tool_data.get('version', 'N/A')}\n\n版本历史：\n暂无书写，占位符，日后增添")
        version_text.setStyleSheet("""
            QTextEdit {
                border: none;
                font-size: 12px;
                color: #475569;
                background-color: transparent;
            }
        """)
        
        layout.addWidget(version_text)
        
        return tab
        
    def create_sidebar(self):
        """创建右侧边栏"""
        sidebar = QWidget()
        sidebar.setFixedWidth(240)  # 只固定宽度，高度自适应
        sidebar.setMinimumHeight(320)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(20)
        
        # 引用信息卡片
        citation_card = self.create_citation_card()
        sidebar_layout.addWidget(citation_card)
        
        # 相关工具卡片
        related_card = self.create_related_tools_card()
        sidebar_layout.addWidget(related_card)
        
        sidebar_layout.addStretch()
        
        return sidebar
        
    def create_citation_card(self):
        """创建引用信息卡片"""
        card = QWidget()
        card.setFixedHeight(120)
        card.setStyleSheet("""
            QWidget {
                background-color: #fef3c7;
                border: 1px solid #fbbf24;
                border-radius: 8px;
            }
        """)
        
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(12, 12, 12, 12)
        
        title = QLabel(self.tr("📚 Citation"))
        title.setStyleSheet("font-size: 13px; font-weight: bold; color: #92400e;")
        
        citation_text = QLabel(self.tr("No citation information yet\nTo be added later"))
        citation_text.setStyleSheet("font-size: 11px; color: #78350f; margin-top: 4px;")
        
        copy_btn = QPushButton(self.tr("Copy BibTeX"))
        copy_btn.setFixedHeight(28)
        copy_btn.setStyleSheet("""
            QPushButton {
                background-color: #f59e0b;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #d97706;
            }
        """)
        
        card_layout.addWidget(title)
        card_layout.addWidget(citation_text)
        card_layout.addStretch()
        card_layout.addWidget(copy_btn)
        
        return card
        
    def create_related_tools_card(self):
        """创建相关工具卡片"""
        card = QWidget()
        card.setFixedHeight(180)
        card.setStyleSheet("""
            QWidget {
                background-color: white;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
            }
        """)
        
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(12, 12, 12, 12)
        
        title = QLabel(self.tr("🔗 Related Tools"))
        title.setStyleSheet("font-size: 13px; font-weight: bold; color: #1e293b;")
        card_layout.addWidget(title)
        
        # 相关工具列表
        related_tools = self._get_related_tools()
        for tool in related_tools:
            tool_btn = QPushButton(tool)
            tool_btn.setFixedHeight(32)
            tool_btn.setStyleSheet("""
                QPushButton {
                    background-color: #f8fafc;
                    border: 1px solid #e2e8f0;
                    border-radius: 4px;
                    text-align: left;
                    padding-left: 12px;
                    font-size: 12px;
                    color: #475569;
                }
                QPushButton:hover {
                    background-color: #e2e8f0;
                    color: #1e293b;
                }
            """)
            card_layout.addWidget(tool_btn)
            
        card_layout.addStretch()
        
        return card
        
    def create_button_bar(self):
        """创建底部按钮栏"""
        button_bar = QWidget()
        button_bar.setFixedHeight(60)
        button_bar.setStyleSheet("background-color: white; border-top: 1px solid #e2e8f0;")
        
        layout = QHBoxLayout(button_bar)
        layout.setContentsMargins(30, 10, 30, 10)
        
        # 关闭按钮
        close_btn = QPushButton(self.tr("Close"))
        close_btn.setFixedSize(100, 36)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #f1f5f9;
                color: #475569;
                border: none;
                border-radius: 6px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #e2e8f0;
            }
        """)
        close_btn.clicked.connect(self.close)
        
        layout.addStretch()
        layout.addWidget(close_btn)
        
        return button_bar
        
    def _get_category_display(self):
        """获取分类显示名称"""
        category_map = {
            "quality": "质量控制",
            "sequence": "序列分析",
            "genomics": "基因组学",
            "rnaseq": "RNA-seq",
            "phylogeny": "系统发育"
        }
        return category_map.get(self.tool_data.get('category', ''), "其他工具")
        
    def _get_features_text(self):
        """获取功能特性文本"""
        tool_features = {
            "FastQC": "• 高通量测序数据质量控制\n• 支持多种测序平台数据格式\n• 实时质量报告生成\n• 批量处理能力",
            "BLAST": "• 序列相似性搜索\n• 支持核酸和蛋白质序列\n• 多种比对算法\n• 大规模数据库搜索",
            "BWA": "• 快速准确的序列比对\n• 支持长读段和短读段\n• 内存效率高\n• 并行计算支持",
            "SAMtools": "• SAM/BAM/CRAM格式处理\n• 排序、索引、统计功能\n• 变异检测支持\n• 数据格式转换",
            "HISAT2": "• RNA-seq读段比对\n• 剪接位点识别\n• 快速索引构建\n• 低内存占用",
            "IQ-TREE": "• 最大似然法建树\n• 模型选择功能\n• Bootstrap支持\n• 并行计算优化"
        }
        return tool_features.get(self.tool_data['name'], "暂无书写，占位符，日后增添")
        
    def _get_tech_specs(self):
        """获取技术规格"""
        default_specs = [
            ("编程语言:", "暂无信息"),
            ("依赖环境:", "暂无信息"),
            ("输入格式:", "暂无信息"),
            ("输出格式:", "暂无信息"),
            ("CPU要求:", "多核推荐"),
            ("内存要求:", "最小4GB, 推荐8GB+")
        ]
        
        # 根据工具定制规格
        tool_specs = {
            "FastQC": [
                ("编程语言:", "Java"),
                ("依赖环境:", "Java Runtime Environment"),
                ("输入格式:", "FASTQ, SAM, BAM"),
                ("输出格式:", "HTML报告, ZIP"),
                ("CPU要求:", "单核即可"),
                ("内存要求:", "最小250MB")
            ],
            "BLAST": [
                ("编程语言:", "C++"),
                ("依赖环境:", "无特殊要求"),
                ("输入格式:", "FASTA"),
                ("输出格式:", "多种格式支持"),
                ("CPU要求:", "多核推荐"),
                ("内存要求:", "取决于数据库大小")
            ]
        }
        
        return tool_specs.get(self.tool_data['name'], default_specs)
        
    def _get_related_tools(self):
        """获取相关工具列表"""
        related_map = {
            "FastQC": ["MultiQC", "Trimmomatic", "Cutadapt"],
            "BLAST": ["BWA", "Bowtie2", "DIAMOND"],
            "BWA": ["BLAST", "Bowtie2", "minimap2"],
            "SAMtools": ["BCFtools", "HTSlib", "Picard"],
            "HISAT2": ["StringTie", "Cufflinks", "STAR"],
            "IQ-TREE": ["RAxML", "PhyML", "MrBayes"]
        }
        return related_map.get(self.tool_data['name'], ["BLAST", "BWA", "SAMtools"])[:3]
