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
        version_label = QLabel(f"版本 {self.tool_data.get('version', 'N/A')}")
        version_label.setStyleSheet("""
            font-size: 13px;
            color: #7f8c8d;
        """)
        
        # 状态标签
        status = "已安装" if self.tool_data['status'] == 'installed' else "未安装"
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
            self.launch_btn = QPushButton("🚀 启动")
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
            self.uninstall_btn = QPushButton("卸载")
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
            time_label = QLabel(f"已使用 {usage_time}")
            time_label.setStyleSheet("""
                font-size: 11px;
                color: #95a5a6;
                margin-top: 8px;
            """)
            time_label.setAlignment(Qt.AlignCenter)
            right_layout.addWidget(time_label)
        else:
            # 安装按钮（简洁居中）
            self.install_btn = QPushButton("📥 安装工具")
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
        title = QLabel("📝 工具介绍")
        title.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: #2c3e50;
        """)
        
        # 使用 QLabel 而不是 QTextEdit，支持自动换行和高度自适应
        description = QLabel(self.tool_data.get('description', '暂无详细介绍'))
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
        title = QLabel("🔧 技术规格")
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
            label_widget = QLabel(f"{label}：")
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
        title = QLabel("📖 使用说明")
        title.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: #2c3e50;
        """)
        
        # 使用说明内容
        usage_text = self.tool_data.get('usage', '暂无使用说明')
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
            "FastQC": "2.5小时",
            "BLAST": "1.2小时",
            "BWA": "45分钟",
            "SAMtools": "3.8小时"
        }
        return mock_times.get(self.tool_data['name'], "未使用")
    
    def _get_tech_specs(self):
        """获取技术规格"""
        tool_specs = {
            "FastQC": [
                ("编程语言", "Java"),
                ("依赖环境", "Java 8+"),
                ("输入格式", "FASTQ, SAM, BAM"),
                ("输出格式", "HTML, ZIP"),
                ("CPU要求", "单核即可"),
                ("内存要求", "最小2GB"),
                ("存储占用", "85MB"),
                ("下载源", "官方: https://www.bioinformatics.babraham.ac.uk/projects/fastqc/\nGitHub: https://github.com/s-andrews/FastQC")
            ],
            "BLAST": [
                ("编程语言", "C++"),
                ("依赖环境", "标准C++库"),
                ("输入格式", "FASTA"),
                ("输出格式", "多种格式"),
                ("CPU要求", "多核推荐"),
                ("内存要求", "取决于数据库大小"),
                ("存储占用", "245MB"),
                ("下载源", "官方: https://ftp.ncbi.nlm.nih.gov/blast/executables/blast+/\nGitHub: https://github.com/ncbi/blast_plus_docs")
            ],
            "BWA": [
                ("编程语言", "C"),
                ("依赖环境", "标准C库"),
                ("输入格式", "FASTQ, FASTA"),
                ("输出格式", "SAM, BAM"),
                ("CPU要求", "多核推荐"),
                ("内存要求", "3GB以上"),
                ("存储占用", "10MB"),
                ("下载源", "https://github.com/lh3/bwa/releases")
            ],
            "SAMtools": [
                ("编程语言", "C"),
                ("依赖环境", "HTSlib"),
                ("输入格式", "SAM, BAM, CRAM"),
                ("输出格式", "SAM, BAM, CRAM"),
                ("CPU要求", "单核即可"),
                ("内存要求", "1GB以上"),
                ("存储占用", "15MB"),
                ("下载源", "https://github.com/samtools/samtools/releases")
            ],
            "IGV": [
                ("编程语言", "Java"),
                ("依赖环境", "Java 11+"),
                ("输入格式", "BAM, VCF, BED, GFF, BigWig等"),
                ("输出格式", "PNG, SVG, PDF截图"),
                ("CPU要求", "多核推荐"),
                ("内存要求", "4GB以上推荐"),
                ("存储占用", "350MB"),
                ("下载源", "https://data.broadinstitute.org/igv/projects/downloads/")
            ]
        }
        
        default_specs = [
            ("编程语言", "暂无信息"),
            ("依赖环境", "暂无信息"),
            ("输入格式", "暂无信息"),
            ("输出格式", "暂无信息"),
            ("CPU要求", "暂无信息"),
            ("内存要求", "暂无信息"),
            ("存储占用", "暂无信息"),
            ("下载源", "暂无信息")
        ]
        
        return tool_specs.get(self.tool_data['name'], default_specs)
    
    def _get_keywords(self):
        """获取工具的筛选关键词/标签"""
        tool_keywords = {
            "FastQC": [
                "质量控制", "RNA序列分析", "DNA序列分析", 
                "FASTQ处理", "测序质量评估", "高通量测序"
            ],
            "BLAST": [
                "序列比对", "同源性分析", "基因注释",
                "蛋白质分析", "进化分析", "序列搜索"
            ],
            "BWA": [
                "序列比对", "基因组映射", "短序列比对",
                "NGS数据处理", "参考基因组比对"
            ],
            "SAMtools": [
                "BAM文件处理", "SAM文件处理", "序列比对结果处理",
                "基因组数据分析", "变异检测"
            ],
            "IGV": [
                "基因组可视化", "BAM查看器", "VCF查看器",
                "变异验证", "序列比对可视化", "注释查看",
                "交互式浏览", "多轨道显示", "基因组浏览器"
            ]
        }
        
        default_keywords = [
            "生物信息学", "序列分析", "数据处理"
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
        title = QLabel("🏷️ 关键词标签")
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
                    self.install_btn.setText(f"安装中 {progress}%")
                elif status_text:
                    # 限制状态文本长度以适应按钮
                    short_text = status_text[:8] + "..." if len(status_text) > 8 else status_text
                    self.install_btn.setText(short_text)
                else:
                    self.install_btn.setText("安装中...")
                self.logger.info(f"[详情页面进度-2] 更新安装按钮文本: {self.install_btn.text()}")
                
            elif not is_installing and self.uninstall_btn:
                # 卸载中 - 更新卸载按钮
                self.uninstall_btn.setEnabled(False)
                if progress >= 0:
                    self.uninstall_btn.setText(f"卸载中 {progress}%")
                elif status_text:
                    # 限制状态文本长度以适应按钮
                    short_text = status_text[:6] + ".." if len(status_text) > 6 else status_text
                    self.uninstall_btn.setText(short_text)
                else:
                    self.uninstall_btn.setText("卸载中...")
                self.logger.info(f"[详情页面进度-2] 更新卸载按钮文本: {self.uninstall_btn.text()}")
                
            elif not is_installing:
                # 完成安装/卸载 - 恢复按钮状态
                if self.install_btn:
                    try:
                        self.install_btn.setText("📥 安装工具")
                        self.install_btn.setEnabled(True)
                        self.logger.info(f"[详情页面进度-3] 恢复安装按钮状态")
                    except RuntimeError as e:
                        self.logger.warning(f"[详情页面进度-3] 安装按钮已被删除，跳过恢复: {e}")
                        
                if self.uninstall_btn:
                    try:
                        self.uninstall_btn.setText("卸载")
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