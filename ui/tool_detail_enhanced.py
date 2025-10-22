#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工具详情页面 - 增强版
解决自适应高度、统一边距等问题
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QScrollArea, QFrame, QSizePolicy, QGridLayout, QApplication
)
from PyQt5.QtCore import Qt, pyqtSignal, QPropertyAnimation, QEasingCurve, pyqtProperty
from PyQt5.QtGui import QFont, QColor, QPalette, QPixmap, QPainter, QPainterPath, QBrush, QPen
import logging


class EnhancedDetailPage(QWidget):
    """增强版详情页面 - 完美自适应"""
    
    # 信号
    back_requested = pyqtSignal()
    install_requested = pyqtSignal(str)
    launch_requested = pyqtSignal(str)
    uninstall_requested = pyqtSignal(str)
    favorite_toggled = pyqtSignal(str, bool)  # 收藏状态切换信号
    
    # 统一的边距设置
    CONTENT_MARGIN = 40  # 内容区域左右边距
    SECTION_SPACING = 20  # 区块之间的间距
    CARD_PADDING = 20  # 卡片内边距
    
    def __init__(self, tool_data: dict, parent=None):
        super().__init__(parent)
        self.tool_data = tool_data
        self.logger = logging.getLogger(f"BioNexus.EnhancedDetail.{tool_data.get('name', 'Unknown')}")
        
        # 存储按钮引用用于进度更新
        self.install_btn = None
        self.launch_btn = None
        self.uninstall_btn = None
        self.favorite_btn = None  # 收藏按钮引用
        
        self.init_ui()

        # Connect to global language change to support runtime localization
        try:
            from utils.translator import get_translator
            get_translator().languageChanged.connect(self.retranslateUi)
        except Exception:
            pass
        
    def init_ui(self):
        """初始化UI"""
        # 主背景色
        self.setStyleSheet("""
            EnhancedDetailPage {
                background-color: #f8f9fa;
            }
        """)
        
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 创建滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: #f8f9fa;
            }
            QScrollBar:vertical {
                background: #f0f0f0;
                width: 10px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical {
                background: #c0c0c0;
                border-radius: 5px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background: #a0a0a0;
            }
        """)
        
        # 内容容器
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(
            self.CONTENT_MARGIN,  # 左
            20,  # 上
            self.CONTENT_MARGIN,  # 右
            20   # 下
        )
        content_layout.setSpacing(self.SECTION_SPACING)
        
        # 1. 头部信息卡片
        header_card = self.create_header_card()
        content_layout.addWidget(header_card)
        
        # 2. 工具介绍卡片（自适应高度）
        description_card = self.create_description_card()
        content_layout.addWidget(description_card)
        
        # 3. 技术规格卡片
        specs_card = self.create_specs_card()
        content_layout.addWidget(specs_card)
        
        # 4. 关键词标签卡片
        keywords_card = self.create_keywords_card()
        content_layout.addWidget(keywords_card)
        
        # 5. 使用说明卡片（可选）
        if self.tool_data.get('usage'):
            usage_card = self.create_usage_card()
            content_layout.addWidget(usage_card)
        
        # 添加底部间距
        content_layout.addStretch()
        
        scroll.setWidget(content)
        main_layout.addWidget(scroll)

    def retranslateUi(self, locale: str = None):
        """Retranslate all UI text on runtime language change.
        Rebuilds the content and preserves scroll position.
        """
        try:
            from PyQt5.QtWidgets import QScrollArea
            vpos = 0
            old_scroll = None
            try:
                old_scroll = next(iter(self.findChildren(QScrollArea)), None)
                if old_scroll:
                    vpos = old_scroll.verticalScrollBar().value()
            except Exception:
                pass

            self.update_ui()

            try:
                new_scroll = next(iter(self.findChildren(QScrollArea)), None)
                if new_scroll:
                    new_scroll.verticalScrollBar().setValue(vpos)
            except Exception:
                pass
        except Exception as e:
            try:
                self.logger.error(f"retranslateUi failed: {e}")
            except Exception:
                pass
    
    def create_header_card(self):
        """创建头部信息卡片"""
        card = QFrame()
        card.setObjectName("headerCard")
        card.setStyleSheet("""
            QFrame#headerCard {
                background-color: white;
                border-radius: 12px;
                border: 1px solid #e0e0e0;
                /* 添加阴影效果 */
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 white, stop:1 #fdfdfd);
            }
        """)
        
        layout = QHBoxLayout(card)
        layout.setContentsMargins(self.CARD_PADDING, self.CARD_PADDING, self.CARD_PADDING, self.CARD_PADDING)
        layout.setSpacing(20)
        
        # 左侧：图标和基本信息
        left_widget = QWidget()
        left_layout = QHBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(15)
        
        # 工具图标 - 根据工具类型使用不同渐变色
        icon_label = QLabel()
        icon_label.setFixedSize(64, 64)
        gradient = self._get_tool_gradient()
        icon_label.setStyleSheet(f"""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 {gradient[0]}, stop:1 {gradient[1]});
            border-radius: 12px;
            color: white;
            font-size: 24px;
            font-weight: bold;
            border: 2px solid rgba(255, 255, 255, 0.2);
        """)
        icon_label.setText(self.tool_data['name'][:2].upper())
        icon_label.setAlignment(Qt.AlignCenter)
        
        # 基本信息 - 设置固定高度与图标对齐（64px）
        info_widget = QWidget()
        info_widget.setFixedHeight(64)
        info_layout = QVBoxLayout(info_widget)
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(8)
        info_layout.setAlignment(Qt.AlignVCenter)  # 垂直居中
        
        # 工具名称和收藏按钮的水平布局
        name_container = QWidget()
        name_layout = QHBoxLayout(name_container)
        name_layout.setContentsMargins(0, 0, 0, 0)
        name_layout.setSpacing(8)
        
        # 工具名称
        name_label = QLabel(self.tool_data['name'])
        name_label.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: #2c3e50;
            margin: 0px;
        """)
        
        # 收藏按钮
        self.favorite_btn = QPushButton()
        self.favorite_btn.setFixedSize(24, 24)
        self.favorite_btn.clicked.connect(self._on_favorite_clicked)
        self._update_favorite_button()  # 根据收藏状态设置图标和样式
        
        # 添加到名称布局
        name_layout.addWidget(name_label)
        name_layout.addWidget(self.favorite_btn)
        name_layout.addStretch()  # 推向左侧
        
        # 版本和状态信息的水平布局
        meta_container = QWidget()
        meta_layout = QHBoxLayout(meta_container)
        meta_layout.setContentsMargins(0, 0, 0, 0)
        meta_layout.setSpacing(12)
        
        # 版本信息
        version_label = QLabel(self.tr("Version {0}").format(self.tool_data.get('version', 'N/A')))
        version_label.setStyleSheet("""
            font-size: 13px;
            color: #7f8c8d;
        """)
        
        # 状态标签
        status = self.tr("Installed") if self.tool_data['status'] == 'installed' else self.tr("Not Installed")
        status_label = QLabel(status)
        status_label.setStyleSheet(f"""
            font-size: 12px;
            font-weight: bold;
            color: {'#27ae60' if self.tool_data['status'] == 'installed' else '#e74c3c'};
            padding: 4px 12px;
            background-color: {'#e8f5e9' if self.tool_data['status'] == 'installed' else '#ffebee'};
            border-radius: 12px;
            border: 1px solid {'#27ae60' if self.tool_data['status'] == 'installed' else '#e74c3c'};
        """)
        
        meta_layout.addWidget(version_label)
        meta_layout.addWidget(status_label)
        meta_layout.addStretch()  # 推到左边
        
        info_layout.addWidget(name_container)
        info_layout.addWidget(meta_container)
        
        left_layout.addWidget(icon_label)
        left_layout.addWidget(info_widget)
        left_layout.addStretch()
        
        # 右侧：操作按钮
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(8)
        right_layout.setAlignment(Qt.AlignCenter)
        
        if self.tool_data['status'] == 'installed':
            # 按钮容器 - 水平排列启动和卸载按钮
            button_container = QWidget()
            button_layout = QHBoxLayout(button_container)
            button_layout.setContentsMargins(0, 0, 0, 0)
            button_layout.setSpacing(10)
            
            # 启动按钮
            self.launch_btn = QPushButton(self.tr("🚀 Launch"))
            self.launch_btn.setFixedSize(80, 32)
            self.launch_btn.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #10b981, stop:1 #059669);
                    color: white;
                    border: none;
                    border-radius: 6px;
                    font-size: 12px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #34d399, stop:1 #10b981);
                }
                QPushButton:pressed {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #047857, stop:1 #065f46);
                }
            """)
            self.launch_btn.clicked.connect(lambda: self.launch_requested.emit(self.tool_data['name']))
            
            # 卸载按钮
            self.uninstall_btn = QPushButton(self.tr("Uninstall"))
            self.uninstall_btn.setFixedSize(80, 32)
            self.uninstall_btn.setStyleSheet("""
                QPushButton {
                    background: transparent;
                    color: #e74c3c;
                    border: 1px solid #e74c3c;
                    border-radius: 6px;
                    font-size: 12px;
                    font-weight: 500;
                }
                QPushButton:hover {
                    background: #e74c3c;
                    color: white;
                }
            """)
            # 🎯 详情页面卸载按钮日志
            def emit_uninstall():
                tool_name = self.tool_data['name']
                print(f"【下载状态链路-详情页-U1】详情页面卸载按钮被点击: {tool_name}")
                import logging
                logger = logging.getLogger(__name__)
                logger.info(f"【下载状态链路-详情页-U1】详情页面卸载按钮被点击: {tool_name}")
                self.uninstall_requested.emit(tool_name)
            self.uninstall_btn.clicked.connect(emit_uninstall)
            
            button_layout.addWidget(self.launch_btn)
            button_layout.addWidget(self.uninstall_btn)
            
            right_layout.addWidget(button_container)
            
            # 使用时间信息（移到按钮下方）
            usage_time = self._get_usage_time()
            time_label = QLabel(self.tr("Used {0}").format(usage_time))
            time_label.setStyleSheet("""
                font-size: 11px;
                color: #95a5a6;
                margin-top: 8px;
            """)
            time_label.setAlignment(Qt.AlignCenter)
            right_layout.addWidget(time_label)
        else:
            # 安装按钮（简洁居中）
            self.install_btn = QPushButton(self.tr("📥 Install Tool"))
            self.install_btn.setFixedSize(120, 36)
            self.install_btn.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #3b82f6, stop:1 #2563eb);
                    color: white;
                    border: none;
                    border-radius: 8px;
                    font-size: 13px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #60a5fa, stop:1 #3b82f6);
                }
                QPushButton:pressed {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #1d4ed8, stop:1 #1e40af);
                }
            """)
            # 🎯 详情页面安装按钮日志
            def emit_install():
                tool_name = self.tool_data['name']
                print(f"【下载状态链路-详情页-I1】详情页面安装按钮被点击: {tool_name}")
                import logging
                logger = logging.getLogger(__name__)
                logger.info(f"【下载状态链路-详情页-I1】详情页面安装按钮被点击: {tool_name}")
                self.install_requested.emit(tool_name)
            self.install_btn.clicked.connect(emit_install)
            right_layout.addWidget(self.install_btn)
        
        layout.addWidget(left_widget)
        layout.addWidget(right_widget)
        
        return card
    
    def create_description_card(self):
        """创建工具介绍卡片（自适应高度）"""
        card = QFrame()
        card.setObjectName("descriptionCard")
        card.setStyleSheet("""
            QFrame#descriptionCard {
                background-color: white;
                border-radius: 12px;
                border: 1px solid #e0e0e0;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 white, stop:1 #fdfdfd);
            }
        """)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(self.CARD_PADDING, self.CARD_PADDING, self.CARD_PADDING, self.CARD_PADDING)
        layout.setSpacing(12)
        
        # 标题
        title = QLabel(self.tr("📝 Tool Overview"))
        title.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: #2c3e50;
        """)
        
        # 使用 QLabel 而不是 QTextEdit，支持自动换行和高度自适应
        try:
            from utils.tool_localization import get_localized_tool_description
            desc_text = get_localized_tool_description(self.tool_data)
        except Exception:
            desc_text = ''
        if not desc_text:
            desc_text = self.tr('No detailed description')
        description = QLabel(desc_text)
        description.setWordWrap(True)  # 自动换行
        description.setStyleSheet("""
            QLabel {
                font-size: 13px;
                color: #34495e;
                line-height: 1.6;
                padding: 15px;
                background-color: #f8f9fa;
                border-radius: 8px;
                border: 1px solid #e9ecef;
            }
        """)
        description.setTextInteractionFlags(Qt.TextSelectableByMouse)  # 可选择文本
        
        layout.addWidget(title)
        layout.addWidget(description)
        
        return card
    
    def create_specs_card(self):
        """创建技术规格卡片"""
        card = QFrame()
        card.setObjectName("specsCard")
        card.setStyleSheet("""
            QFrame#specsCard {
                background-color: white;
                border-radius: 12px;
                border: 1px solid #e0e0e0;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 white, stop:1 #fdfdfd);
            }
        """)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(self.CARD_PADDING, self.CARD_PADDING, self.CARD_PADDING, self.CARD_PADDING)
        layout.setSpacing(12)
        
        # 标题
        title = QLabel(self.tr("🔧 Technical Specs"))
        title.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: #2c3e50;
        """)
        
        # 规格列表
        specs_widget = QWidget()
        specs_layout = QGridLayout(specs_widget)
        specs_layout.setContentsMargins(10, 10, 10, 10)
        specs_layout.setSpacing(10)
        specs_layout.setColumnStretch(1, 1)  # 第二列可伸缩
        
        specs_data = self._get_tech_specs()
        for i, (label, value) in enumerate(specs_data):
            # 标签
            label_widget = QLabel(f"{label}:")
            label_widget.setStyleSheet("""
                font-size: 12px;
                color: #7f8c8d;
                font-weight: 500;
            """)
            label_widget.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            
            # 值
            value_widget = QLabel(value)
            value_widget.setWordWrap(True)
            value_widget.setStyleSheet("""
                font-size: 12px;
                color: #2c3e50;
            """)
            
            specs_layout.addWidget(label_widget, i, 0)
            specs_layout.addWidget(value_widget, i, 1)
        
        specs_widget.setStyleSheet("""
            background-color: #f8f9fa;
            border-radius: 8px;
        """)
        
        layout.addWidget(title)
        layout.addWidget(specs_widget)
        
        return card
    
    def create_usage_card(self):
        """创建使用说明卡片"""
        card = QFrame()
        card.setObjectName("usageCard")
        card.setStyleSheet("""
            QFrame#usageCard {
                background-color: white;
                border-radius: 12px;
                border: 1px solid #e0e0e0;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 white, stop:1 #fdfdfd);
            }
        """)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(self.CARD_PADDING, self.CARD_PADDING, self.CARD_PADDING, self.CARD_PADDING)
        layout.setSpacing(12)
        
        # 标题
        title = QLabel(self.tr("📖 Usage Guide"))
        title.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: #2c3e50;
        """)
        
        # 使用说明内容
        usage_text = self.tool_data.get('usage', self.tr('No usage instructions yet'))
        usage = QLabel(usage_text)
        usage.setWordWrap(True)
        usage.setStyleSheet("""
            QLabel {
                font-size: 13px;
                color: #34495e;
                line-height: 1.6;
                padding: 15px;
                background-color: #f8f9fa;
                border-radius: 8px;
                border: 1px solid #e9ecef;
                font-family: 'Consolas', 'Monaco', monospace;
            }
        """)
        
        layout.addWidget(title)
        layout.addWidget(usage)
        
        return card
    
    
    def _get_usage_time(self):
        """获取使用时间"""
        mock_times = {
            "FastQC": self.tr("2.5 hours"),
            "BLAST": self.tr("1.2 hours"),
            "BWA": self.tr("45 minutes"),
            "SAMtools": self.tr("3.8 hours")
        }
        return mock_times.get(self.tool_data['name'], self.tr("Not Used"))
    
    def _get_tech_specs(self):
        """获取技术规格"""
        tool_specs = {
            "FastQC": [
                (self.tr("Programming Language"), "Java"),
                (self.tr("Dependencies"), "Java 8+"),
                (self.tr("Input Formats"), "FASTQ, SAM, BAM"),
                (self.tr("Output Formats"), "HTML, ZIP"),
                (self.tr("CPU Requirements"), self.tr("Single core is fine")),
                (self.tr("Memory Requirements"), self.tr("Minimum 2GB")),
                (self.tr("Disk Usage"), "85MB"),
                (self.tr("Download Sources"), self.tr("Official: https://www.bioinformatics.babraham.ac.uk/projects/fastqc/\nGitHub: https://github.com/s-andrews/FastQC"))
            ],
            "BLAST": [
                (self.tr("Programming Language"), "C++"),
                (self.tr("Dependencies"), self.tr("Standard C++ Library")),
                (self.tr("Input Formats"), "FASTA"),
                (self.tr("Output Formats"), self.tr("Multiple formats")),
                (self.tr("CPU Requirements"), self.tr("Multi-core recommended")),
                (self.tr("Memory Requirements"), self.tr("Depends on database size")),
                (self.tr("Disk Usage"), "245MB"),
                (self.tr("Download Sources"), self.tr("Official: https://ftp.ncbi.nlm.nih.gov/blast/executables/blast+/\nGitHub: https://github.com/ncbi/blast_plus_docs"))
            ],
            "BWA": [
                (self.tr("Programming Language"), "C"),
                (self.tr("Dependencies"), self.tr("Standard C Library")),
                (self.tr("Input Formats"), "FASTQ, FASTA"),
                (self.tr("Output Formats"), "SAM, BAM"),
                (self.tr("CPU Requirements"), self.tr("Multi-core recommended")),
                (self.tr("Memory Requirements"), self.tr("3GB or more")),
                (self.tr("Disk Usage"), "10MB"),
                (self.tr("Download Sources"), "https://github.com/lh3/bwa/releases")
            ],
            "SAMtools": [
                (self.tr("Programming Language"), "C"),
                (self.tr("Dependencies"), "HTSlib"),
                (self.tr("Input Formats"), "SAM, BAM, CRAM"),
                (self.tr("Output Formats"), "SAM, BAM, CRAM"),
                (self.tr("CPU Requirements"), self.tr("Single core is fine")),
                (self.tr("Memory Requirements"), self.tr("1GB or more")),
                (self.tr("Disk Usage"), "15MB"),
                (self.tr("Download Sources"), "https://github.com/samtools/samtools/releases")
            ],
            "IGV": [
                (self.tr("Programming Language"), "Java"),
                (self.tr("Dependencies"), "Java 11+"),
                (self.tr("Input Formats"), "BAM, VCF, BED, GFF, BigWig"),
                (self.tr("Output Formats"), "PNG, SVG, PDF"),
                (self.tr("CPU Requirements"), self.tr("Multi-core recommended")),
                (self.tr("Memory Requirements"), self.tr("4GB or more recommended")),
                (self.tr("Disk Usage"), "350MB"),
                (self.tr("Download Sources"), "https://data.broadinstitute.org/igv/projects/downloads/")
            ]
        }
        
        default_specs = [
            (self.tr("Programming Language"), self.tr("N/A")),
            (self.tr("Dependencies"), self.tr("N/A")),
            (self.tr("Input Formats"), self.tr("N/A")),
            (self.tr("Output Formats"), self.tr("N/A")),
            (self.tr("CPU Requirements"), self.tr("N/A")),
            (self.tr("Memory Requirements"), self.tr("N/A")),
            (self.tr("Disk Usage"), self.tr("N/A")),
            (self.tr("Download Sources"), self.tr("N/A"))
        ]
        
        return tool_specs.get(self.tool_data['name'], default_specs)
    
    def _get_keywords(self):
        """获取工具的筛选关键词/标签"""
        tool_keywords = {
            "FastQC": [
                self.tr("Quality Control"), self.tr("RNA-seq Analysis"), self.tr("DNA-seq Analysis"), 
                self.tr("FASTQ Processing"), self.tr("Sequencing QC"), self.tr("High-throughput Sequencing")
            ],
            "BLAST": [
                self.tr("Sequence Alignment"), self.tr("Homology Analysis"), self.tr("Gene Annotation"),
                self.tr("Protein Analysis"), self.tr("Phylogenetic Analysis"), self.tr("Sequence Search")
            ],
            "BWA": [
                self.tr("Sequence Alignment"), self.tr("Genome Mapping"), self.tr("Short Read Alignment"),
                self.tr("NGS Data Processing"), self.tr("Reference Alignment")
            ],
            "SAMtools": [
                self.tr("BAM Processing"), self.tr("SAM Processing"), self.tr("Alignment Processing"),
                self.tr("Genomic Data Analysis"), self.tr("Variant Calling")
            ],
            "IGV": [
                self.tr("Genome Visualization"), self.tr("BAM Viewer"), self.tr("VCF Viewer"),
                self.tr("Variant Validation"), self.tr("Alignment Visualization"), self.tr("Annotation Viewer"),
                self.tr("Interactive Browsing"), self.tr("Multi-track Display"), self.tr("Genome Browser")
            ]
        }
        
        default_keywords = [
            self.tr("Bioinformatics"), self.tr("Sequence Analysis"), self.tr("Data Processing")
        ]
        
        return tool_keywords.get(self.tool_data['name'], default_keywords)
    
    def create_keywords_card(self):
        """创建关键词/标签卡片"""
        card = QFrame()
        card.setObjectName("keywordsCard")
        card.setStyleSheet("""
            QFrame#keywordsCard {
                background-color: white;
                border-radius: 12px;
                border: 1px solid #e0e0e0;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 white, stop:1 #fdfdfd);
            }
        """)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(self.CARD_PADDING, self.CARD_PADDING, self.CARD_PADDING, self.CARD_PADDING)
        layout.setSpacing(12)
        
        # 标题
        title = QLabel(self.tr("🏷️ Keywords"))
        title.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: #2c3e50;
        """)
        
        # 关键词标签容器
        keywords_widget = QWidget()
        keywords_widget.setStyleSheet("""
            background-color: #f8f9fa;
            border-radius: 8px;
        """)
        
        # 使用流式布局显示标签
        from ui.flow_layout import FlowLayout
        flow_layout = FlowLayout(keywords_widget)
        flow_layout.setContentsMargins(15, 15, 15, 15)
        flow_layout.setSpacing(8)
        
        # 获取关键词并创建标签
        keywords = self._get_keywords()
        for keyword in keywords:
            tag_label = QLabel(keyword)
            tag_label.setStyleSheet("""
                QLabel {
                    background-color: #e3f2fd;
                    color: #1976d2;
                    border: 1px solid #bbdefb;
                    border-radius: 12px;
                    padding: 6px 14px;
                    font-size: 12px;
                    font-weight: 500;
                }
                QLabel:hover {
                    background-color: #bbdefb;
                    border-color: #90caf9;
                    cursor: pointer;
                }
            """)
            tag_label.setAlignment(Qt.AlignCenter)
            # 使标签自适应内容大小
            tag_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
            flow_layout.addWidget(tag_label)
        
        layout.addWidget(title)
        layout.addWidget(keywords_widget)
        
        return card
    
    def _get_tool_gradient(self):
        """根据工具类型获取图标渐变色"""
        category_gradients = {
            "quality": ("#667eea", "#764ba2"),  # 紫蓝渐变 - 质量控制
            "sequence": ("#f093fb", "#f5576c"),  # 粉红渐变 - 序列分析
            "rnaseq": ("#4facfe", "#00f2fe"),   # 蓝青渐变 - RNA测序
            "genomics": ("#43e97b", "#38f9d7"),  # 绿青渐变 - 基因组学
            "phylogeny": ("#fa709a", "#fee140"),  # 粉黄渐变 - 系统发育
            "visualization": ("#ff6b6b", "#ffd93d")  # 红黄渐变 - 可视化
        }
        
        category = self.tool_data.get('category', 'unknown')
        return category_gradients.get(category, ("#667eea", "#764ba2"))  # 默认紫蓝
    
    def update_ui(self):
        """更新UI显示，通常在工具状态改变后调用"""
        self.logger.info(f"[详情页面更新-1] 开始更新UI: {self.tool_data['name']}")
        self.logger.info(f"[详情页面更新-2] 当前状态: {self.tool_data.get('status', 'unknown')}")
        
        # 清理现有布局
        self.logger.info(f"[详情页面更新-3] 清理现有布局")
        old_layout = self.layout()
        if old_layout is not None:
            # 清理所有子widget
            while old_layout.count():
                child = old_layout.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()
            # 删除旧布局
            QWidget().setLayout(old_layout)
        
        # 重新初始化UI以反映新的工具状态
        self.logger.info(f"[详情页面更新-4] 重新初始化UI")
        self.init_ui()
        
        # 强制刷新显示
        self.logger.info(f"[详情页面更新-5] 强制刷新显示")
        self.update()
        self.repaint()
        QApplication.processEvents()
        
        self.logger.info(f"[详情页面更新-6] UI更新完成: {self.tool_data['name']}")
    
    def set_installing_state(self, is_installing: bool, progress: int = -1, status_text: str = ""):
        """设置安装/卸载状态，在详情页面按钮上显示进度"""
        self.logger.info(f"[详情页面进度-1] 设置安装状态: {self.tool_data['name']}, installing={is_installing}, progress={progress}, text='{status_text}'")
        
        try:
            if is_installing and self.install_btn:
                # 安装中 - 更新安装按钮
                self.install_btn.setEnabled(False)
                if progress >= 0:
                    self.install_btn.setText(self.tr("Installing {0}%").format(progress))
                elif status_text:
                    # 限制状态文本长度以适应按钮
                    short_text = status_text[:8] + "..." if len(status_text) > 8 else status_text
                    self.install_btn.setText(short_text)
                else:
                    self.install_btn.setText(self.tr("Installing..."))
                self.logger.info(f"[详情页面进度-2] 更新安装按钮文本: {self.install_btn.text()}")
                
            elif not is_installing and self.uninstall_btn:
                # 卸载中 - 更新卸载按钮
                self.uninstall_btn.setEnabled(False)
                if progress >= 0:
                    self.uninstall_btn.setText(self.tr("Uninstalling {0}%").format(progress))
                elif status_text:
                    # 限制状态文本长度以适应按钮
                    short_text = status_text[:6] + ".." if len(status_text) > 6 else status_text
                    self.uninstall_btn.setText(short_text)
                else:
                    self.uninstall_btn.setText(self.tr("Uninstalling..."))
                self.logger.info(f"[详情页面进度-2] 更新卸载按钮文本: {self.uninstall_btn.text()}")
                
            elif not is_installing:
                # 完成安装/卸载 - 恢复按钮状态
                if self.install_btn:
                    try:
                        self.install_btn.setText(self.tr("📥 Install Tool"))
                        self.install_btn.setEnabled(True)
                        self.logger.info(f"[详情页面进度-3] 恢复安装按钮状态")
                    except RuntimeError as e:
                        self.logger.warning(f"[详情页面进度-3] 安装按钮已被删除，跳过恢复: {e}")
                        
                if self.uninstall_btn:
                    try:
                        self.uninstall_btn.setText(self.tr("Uninstall"))
                        self.uninstall_btn.setEnabled(True)
                        self.logger.info(f"[详情页面进度-3] 恢复卸载按钮状态")
                    except RuntimeError as e:
                        self.logger.warning(f"[详情页面进度-3] 卸载按钮已被删除，跳过恢复: {e}")
                        
        except Exception as e:
            self.logger.error(f"[详情页面进度-ERROR] 设置安装状态时发生异常: {e}")
    
    def _update_favorite_button(self):
        """更新收藏按钮的显示状态"""
        if not self.favorite_btn:
            self.logger.warning(f"[收藏按钮] 按钮还未创建，跳过更新")
            return
            
        is_favorite = self.tool_data.get('is_favorite', False)
        
        # 基础样式（每次都重新设置，避免样式累积）
        base_style = """
            QPushButton {
                background: transparent;
                border: none;
                font-size: 16px;
                padding: 0px;
                color: %s;
            }
            QPushButton:hover {
                background: rgba(0, 0, 0, 0.1);
                border-radius: 12px;
            }
            QPushButton:pressed {
                background: rgba(0, 0, 0, 0.2);
            }
        """
        
        if is_favorite:
            # 已收藏 - 金黄色实心星星
            self.favorite_btn.setText("★")
            self.favorite_btn.setStyleSheet(base_style % "#fbbf24")
            self.logger.info(f"[收藏按钮] 设置为已收藏状态（金黄色）: {self.tool_data['name']}")
        else:
            # 未收藏 - 灰色空心星星
            self.favorite_btn.setText("☆")
            self.favorite_btn.setStyleSheet(base_style % "#9ca3af")
            self.logger.info(f"[收藏按钮] 设置为未收藏状态（灰色）: {self.tool_data['name']}")
        
        self.logger.info(f"[收藏按钮] 更新显示状态完成: {self.tool_data['name']} -> {'收藏' if is_favorite else '未收藏'}")
    
    def _on_favorite_clicked(self):
        """收藏按钮点击处理"""
        current_state = self.tool_data.get('is_favorite', False)
        new_state = not current_state
        
        self.logger.info(f"[收藏点击-1] 用户点击收藏按钮: {self.tool_data['name']}")
        self.logger.info(f"[收藏点击-2] 当前状态: {'收藏' if current_state else '未收藏'} -> 目标状态: {'收藏' if new_state else '未收藏'}")
        
        # 立即更新UI（乐观更新）
        self.tool_data['is_favorite'] = new_state
        self.logger.info(f"[收藏点击-3] 更新本地数据: is_favorite = {new_state}")
        
        self._update_favorite_button()
        self.logger.info(f"[收藏点击-4] 按钮UI已更新")
        
        # 发送信号给主窗口处理
        self.logger.info(f"[收藏点击-5] 发送 favorite_toggled 信号: ({self.tool_data['name']}, {new_state})")
        self.favorite_toggled.emit(self.tool_data['name'], new_state)
        self.logger.info(f"[收藏点击-6] 信号发送完成")
    
    def set_favorite_state(self, is_favorite: bool):
        """外部设置收藏状态（用于同步）"""
        self.logger.info(f"[收藏同步] 外部设置收藏状态: {self.tool_data['name']} -> {'收藏' if is_favorite else '未收藏'}")
        self.tool_data['is_favorite'] = is_favorite
        if self.favorite_btn:
            self._update_favorite_button()
