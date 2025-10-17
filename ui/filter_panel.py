"""
筛选面板组件
右侧滑出的筛选侧边栏，提供工具类型和安装状态的批量筛选功能
对应HTML中的筛选系统UI设计，模态窗口设计
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QCheckBox, QFrame, QGroupBox
)
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QFont, QFontMetrics
from data.models import ToolCategory, ToolStatus
from .smart_paint_v2 import create_smart_label_v2, create_smart_checkbox
import math  # 用于按钮网格计算


class FilterPanel(QWidget):
    """
    筛选面板主组件
    提供分类和状态的多条件筛选功能
    对应HTML中的filter-sidebar结构
    """
    
    # 信号定义 - 对应JavaScript中的筛选事件
    filters_applied = pyqtSignal(list, list)    # 应用筛选 (categories, statuses)
    filters_reset = pyqtSignal()                # 重置筛选
    panel_closed = pyqtSignal()                 # 面板关闭
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.category_checkboxes = {}
        self.status_checkboxes = {}
        self.init_ui()
        self.setup_connections()
    
    def init_ui(self):
        """
        初始化用户界面
        对应HTML中的filter-sidebar结构
        """
        # 设置面板属性
        self.setObjectName("FilterPanel")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setProperty("class", "FilterPanel")
        
        # 固定宽度300px，对应CSS设计，添加现代化样式
        self.setFixedWidth(300)
        
        # 设置现代化面板样式 - 使用!important确保优先级
        self.setStyleSheet("""
            QWidget#FilterPanel {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #ffffff, stop:1 #f1f5f9) !important;
                border: 1px solid #e2e8f0 !important;
                border-radius: 16px !important;
                padding: 20px !important;
                min-width: 300px !important;
                max-width: 300px !important;
                margin: 8px !important;
            }
            
            /* 确保完全覆盖任何外部样式 */
            QWidget#FilterPanel[class="FilterPanel"] {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #ffffff, stop:1 #f1f5f9) !important;
                border: 1px solid #e2e8f0 !important;
                border-radius: 16px !important;
                padding: 20px !important;
            }
        """)
        
        # 确保面板能正确显示圆角（重要：设置窗口标志）
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        
        # 使用日志系统而不是print，确保输出被记录
        import logging
        logger = logging.getLogger('BioNexus.ui_operations')
        logger.info(f"[筛选面板] 样式设置完成，objectName: {self.objectName()}")
        
        # 主布局
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(24)
        
        # 筛选面板头部：标题 + 关闭按钮
        self._create_header(main_layout)
        
        # 工具类型筛选区域
        self._create_category_section(main_layout)
        
        # 安装状态筛选区域
        self._create_status_section(main_layout)
        
        main_layout.addStretch()  # 推送操作按钮到底部
        
        # 筛选操作按钮
        self._create_action_buttons(main_layout)
        
        self.setLayout(main_layout)
    
    def _create_header(self, main_layout: QVBoxLayout):
        """
        创建筛选面板头部
        对应HTML中的filter-header结构
        """
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 16)
        
        # 标题 - 🔥 使用SmartPaintLabel V2，完全兼容原有样式！
        title_label = create_smart_label_v2("筛选工具")
        title_label.setObjectName("FilterTitle")
        title_label.setProperty("class", "FilterTitle")
        title_label.setFixedSize(200, 32)  # 固定尺寸保证布局稳定
        
        # 🎯 关键：现代化标题样式
        title_label.setStyleSheet("""
            font-size: 16px;
            font-weight: 700;
            color: #1e293b;
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #3b82f6, stop:1 #1d4ed8);
            -webkit-background-clip: text;
            background-clip: text;
        """)
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()  # 推送关闭按钮到右侧
        
        # 关闭按钮
        self.close_btn = QPushButton("×")
        self.close_btn.setObjectName("FilterClose")
        self.close_btn.setProperty("class", "FilterClose")
        self.close_btn.setFixedSize(28, 28)
        # 现代化关闭按钮样式
        self.close_btn.setStyleSheet("""
            QPushButton#FilterClose {
                background: rgba(156, 163, 175, 0.15);
                color: #6b7280;
                border: 1px solid rgba(156, 163, 175, 0.3);
                border-radius: 14px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton#FilterClose:hover {
                background: rgba(239, 68, 68, 0.15);
                color: #ef4444;
                border: 1px solid rgba(239, 68, 68, 0.4);
            }
            QPushButton#FilterClose:pressed {
                background: rgba(239, 68, 68, 0.25);
            }
        """)
        header_layout.addWidget(self.close_btn)
        
        # 添加现代化分割线
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet("""
            QFrame {
                border: none;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 transparent, stop:0.5 #e2e8f0, stop:1 transparent);
                max-height: 1px;
                margin: 8px 0px;
            }
        """)
        
        header_widget = QWidget()
        header_widget.setLayout(header_layout)
        
        main_layout.addWidget(header_widget)
        main_layout.addWidget(separator)
    
    def _create_category_section(self, main_layout: QVBoxLayout):
        """
        创建工具类型筛选区域 - 按钮方格模式
        参考详情页面美术风格和工具卡片自适应排列
        """
        # 分组框 - 🔥 使用智能文本避免标题截断
        category_group = QGroupBox()  # 不设置标题，手动添加
        category_group.setProperty("class", "FilterSection")
        # 现代化分组框样式
        category_group.setStyleSheet("""
            QGroupBox {
                background: rgba(255, 255, 255, 0.7);
                border: 1px solid rgba(226, 232, 240, 0.8);
                border-radius: 12px;
                padding-top: 12px;
                margin: 8px 0px;
            }
        """)
        
        # 手动创建分组标题 - 🔥 SmartPaintLabel V2，完全兼容样式！
        category_title = create_smart_label_v2("工具类型")
        category_title.setFixedSize(260, 28)  # 固定尺寸
        
        # 🎯 关键：现代化分组标题样式
        category_title.setStyleSheet("""
            font-size: 13px;
            font-weight: 600;
            color: #374151;
            margin-bottom: 12px;
            padding-left: 8px;
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #3b82f6, stop:1 #1d4ed8);
            -webkit-background-clip: text;
            background-clip: text;
        """)
        
        # 分组内布局
        category_layout = QVBoxLayout()
        category_layout.setSpacing(8)
        
        # 添加标题到布局
        category_layout.addWidget(category_title)
        
        # 创建按钮方格网格替代复选框
        category_grid_widget = self._create_category_button_grid()
        category_layout.addWidget(category_grid_widget)
        
        category_group.setLayout(category_layout)
        main_layout.addWidget(category_group)
    
    def _create_status_section(self, main_layout: QVBoxLayout):
        """
        创建安装状态筛选区域
        对应HTML中的安装状态筛选部分
        """
        # 分组框 - 🔥 使用智能文本避免标题截断
        status_group = QGroupBox()  # 不设置标题，手动添加
        status_group.setProperty("class", "FilterSection")
        # 现代化分组框样式
        status_group.setStyleSheet("""
            QGroupBox {
                background: rgba(255, 255, 255, 0.7);
                border: 1px solid rgba(226, 232, 240, 0.8);
                border-radius: 12px;
                padding-top: 12px;
                margin: 8px 0px;
            }
        """)
        
        # 手动创建分组标题 - 🔥 SmartPaintLabel V2，完全兼容样式！
        status_title = create_smart_label_v2("安装状态")
        status_title.setFixedSize(260, 28)  # 固定尺寸
        
        # 🎯 关键：现代化分组标题样式
        status_title.setStyleSheet("""
            font-size: 13px;
            font-weight: 600;
            color: #374151;
            margin-bottom: 12px;
            padding-left: 8px;
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #3b82f6, stop:1 #1d4ed8);
            -webkit-background-clip: text;
            background-clip: text;
        """)
        
        # 分组内布局
        status_layout = QVBoxLayout()
        status_layout.setSpacing(8)
        
        # 添加标题到布局
        status_layout.addWidget(status_title)
        
        # 创建状态按钮方格网格替代复选框
        status_grid_widget = self._create_status_button_grid()
        status_layout.addWidget(status_grid_widget)
        
        status_group.setLayout(status_layout)
        main_layout.addWidget(status_group)
    
    def _create_action_buttons(self, main_layout: QVBoxLayout):
        """
        创建筛选操作按钮
        对应HTML中的filter-actions结构
        """
        # 添加上方现代化分割线
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet("""
            QFrame {
                border: none;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 transparent, stop:0.5 #e2e8f0, stop:1 transparent);
                max-height: 1px;
                margin: 16px 0px;
            }
        """)
        main_layout.addWidget(separator)
        
        # 按钮布局
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 20, 0, 0)
        button_layout.setSpacing(12)
        
        # 重置按钮
        self.reset_btn = QPushButton("重置")
        self.reset_btn.setObjectName("FilterResetBtn")
        self.reset_btn.setProperty("class", "FilterResetBtn")
        # 计算自适应按钮高度
        base_font = QFont()
        base_font.setPointSize(10)
        font_metrics = QFontMetrics(base_font)
        font_height = font_metrics.height()
        button_padding = max(int(font_height * 0.8), 12)
        button_height = max(font_height + button_padding * 2, 40)
        self.reset_btn.setMinimumHeight(button_height)
        # 现代化重置按钮样式 - 确保优先级
        self.reset_btn.setStyleSheet("""
            QPushButton#FilterResetBtn {
                background: rgba(156, 163, 175, 0.1) !important;
                color: #6b7280 !important;
                border: 1px solid rgba(156, 163, 175, 0.3) !important;
                border-radius: 10px !important;
                padding: 12px 20px !important;
                font-weight: 500 !important;
                font-size: 13px !important;
            }
            QPushButton#FilterResetBtn:hover {
                background: rgba(156, 163, 175, 0.2) !important;
                border: 1px solid rgba(156, 163, 175, 0.5) !important;
                color: #4b5563 !important;
            }
            QPushButton#FilterResetBtn:pressed {
                background: rgba(156, 163, 175, 0.3) !important;
            }
            /* 覆盖class样式 */
            QPushButton.FilterResetBtn, QPushButton[class="FilterResetBtn"] {
                background: rgba(156, 163, 175, 0.1) !important;
                color: #6b7280 !important;
                border: 1px solid rgba(156, 163, 175, 0.3) !important;
                border-radius: 10px !important;
                padding: 12px 20px !important;
                font-weight: 500 !important;
                font-size: 13px !important;
            }
        """)
        button_layout.addWidget(self.reset_btn)
        
        # 应用按钮
        self.apply_btn = QPushButton("应用")
        self.apply_btn.setObjectName("FilterApplyBtn")
        self.apply_btn.setProperty("class", "FilterApplyBtn")
        self.apply_btn.setMinimumHeight(button_height)
        # 现代化应用按钮样式 - 确保优先级
        self.apply_btn.setStyleSheet("""
            QPushButton#FilterApplyBtn {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #3b82f6, stop:1 #1d4ed8) !important;
                color: white !important;
                border: 1px solid #3b82f6 !important;
                border-radius: 10px !important;
                padding: 12px 20px !important;
                font-weight: 600 !important;
                font-size: 13px !important;
            }
            QPushButton#FilterApplyBtn:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #2563eb, stop:1 #1e40af) !important;
                border: 1px solid #2563eb !important;
            }
            QPushButton#FilterApplyBtn:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #1d4ed8, stop:1 #1e3a8a) !important;
            }
            /* 覆盖class样式 */
            QPushButton.FilterApplyBtn, QPushButton[class="FilterApplyBtn"] {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #3b82f6, stop:1 #1d4ed8) !important;
                color: white !important;
                border: 1px solid #3b82f6 !important;
                border-radius: 10px !important;
                padding: 12px 20px !important;
                font-weight: 600 !important;
                font-size: 13px !important;
            }
        """)
        button_layout.addWidget(self.apply_btn)
        
        main_layout.addLayout(button_layout)
    
    def _create_category_button_grid(self):
        """
        创建工具类型按钮方格网格
        参考工具卡片的自适应排列机制，实现绿色选中效果
        """
        grid_widget = QWidget()
        grid_widget.setFixedHeight(120)  # 预估高度，会根据实际内容调整
        
        # 工具分类数据
        categories = [
            ('sequence', '序列分析'),
            ('genomics', '基因组学'),
            ('rnaseq', 'RNA-seq'),
            ('phylogeny', '系统发育'),
            ('quality', '质量控制'),
            ('visualization', '可视化')
        ]
        
        # 按钮参数
        BUTTON_HEIGHT = 36
        BUTTON_SPACING = 8
        MIN_BUTTON_WIDTH = 80
        MAX_BUTTON_WIDTH = 120
        GRID_PADDING = 4
        
        # 计算按钮宽度（基于文字长度自适应）
        font = QFont()
        font.setPointSize(10)
        font_metrics = QFontMetrics(font)
        
        button_widgets = []
        for category_value, category_text in categories:
            # 计算文字宽度，添加内边距
            text_width = font_metrics.width(category_text)
            button_width = max(MIN_BUTTON_WIDTH, min(MAX_BUTTON_WIDTH, text_width + 24))
            
            # 创建按钮（使用QPushButton而不是QCheckBox）
            btn = QPushButton(category_text)
            btn.setObjectName(f"CategoryBtn_{category_value}")
            btn.setProperty("category", category_value)
            btn.setProperty("selected", False)  # 选中状态
            btn.setCheckable(True)  # 可切换状态
            btn.setFixedSize(button_width, BUTTON_HEIGHT)
            btn.setFont(font)
            
            # 绿色选中样式（参考详情页面风格）
            btn_name = btn.objectName()
            btn.setStyleSheet(f"""
                QPushButton#{btn_name} {{
                    background: white;
                    border: 1px solid #e0e0e0;
                    border-radius: 8px;
                    color: #374151;
                    font-weight: 500;
                    padding: 8px 12px;
                }}
                QPushButton#{btn_name}:hover {{
                    background: #f8fafc;
                    border: 1px solid #d0d0d0;
                    transform: scale(1.02);
                }}
                QPushButton#{btn_name}:checked {{
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 #22c55e, stop:1 #16a34a);
                    border: 2px solid #22c55e;
                    color: white;
                    font-weight: 600;
                }}
                QPushButton#{btn_name}:checked:hover {{
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 #16a34a, stop:1 #15803d);
                    transform: scale(1.05);
                }}
            """)
            
            # 连接点击事件
            btn.toggled.connect(lambda checked, cat=category_value: self._on_category_button_toggled(cat, checked))
            
            button_widgets.append((btn, button_width))
            self.category_checkboxes[category_value] = btn  # 保持兼容性
        
        # 自适应布局计算（参考卡片网格算法）
        available_width = 260  # 面板宽度 - 边距
        
        # 计算最佳网格布局
        total_buttons = len(button_widgets)
        best_layout = self._calculate_button_grid_layout(button_widgets, available_width, BUTTON_SPACING)
        
        # 根据计算结果放置按钮
        for i, (btn, btn_width) in enumerate(button_widgets):
            row = i // best_layout['cols']
            col = i % best_layout['cols']
            
            x = best_layout['left_margin'] + col * (best_layout['avg_width'] + BUTTON_SPACING)
            y = GRID_PADDING + row * (BUTTON_HEIGHT + BUTTON_SPACING)
            
            btn.setParent(grid_widget)
            btn.move(x, y)
            btn.setFixedWidth(best_layout['avg_width'])  # 统一宽度以保持网格整齐
        
        # 调整网格容器高度
        total_height = GRID_PADDING * 2 + best_layout['rows'] * BUTTON_HEIGHT + (best_layout['rows'] - 1) * BUTTON_SPACING
        grid_widget.setFixedHeight(total_height)
        
        return grid_widget
    
    def _calculate_button_grid_layout(self, button_widgets, available_width, spacing):
        """
        计算按钮网格最佳布局
        参考工具卡片的网格算法
        """
        total_buttons = len(button_widgets)
        if total_buttons == 0:
            return {'cols': 1, 'rows': 1, 'left_margin': 0, 'avg_width': 80}
        
        # 计算平均按钮宽度
        total_width = sum(width for _, width in button_widgets)
        avg_width = total_width // total_buttons
        
        # 尝试不同列数，找到最佳布局
        for cols in range(1, total_buttons + 1):
            # 计算此列数下需要的总宽度
            required_width = cols * avg_width + (cols - 1) * spacing
            
            if required_width <= available_width:
                rows = math.ceil(total_buttons / cols)
                left_margin = (available_width - required_width) // 2
                
                return {
                    'cols': cols,
                    'rows': rows,
                    'left_margin': left_margin,
                    'avg_width': avg_width
                }
        
        # 如果无法适配，强制单列
        return {
            'cols': 1,
            'rows': total_buttons,
            'left_margin': (available_width - avg_width) // 2,
            'avg_width': avg_width
        }
    
    def _on_category_button_toggled(self, category, checked):
        """
        处理分类按钮切换事件
        """
        print(f"[筛选按钮] 分类 {category} 切换为 {'选中' if checked else '未选中'}")
        # 这里可以添加实时筛选逻辑，但为了保持兼容性，暂时保留原有应用机制
    
    def _create_status_button_grid(self):
        """
        创建安装状态按钮方格网格
        使用绿色选中效果，自适应布局
        """
        grid_widget = QWidget()
        grid_widget.setFixedHeight(80)  # 状态按钮较少，高度较小
        
        # 安装状态数据
        statuses = [
            ('installed', '已安装'),
            ('available', '可安装'),
            ('update', '需更新')
        ]
        
        # 按钮参数（与分类按钮一致）
        BUTTON_HEIGHT = 36
        BUTTON_SPACING = 8
        MIN_BUTTON_WIDTH = 70
        MAX_BUTTON_WIDTH = 100
        GRID_PADDING = 4
        
        # 字体设置
        font = QFont()
        font.setPointSize(10)
        font_metrics = QFontMetrics(font)
        
        button_widgets = []
        for status_value, status_text in statuses:
            # 计算文字宽度，添加内边距
            text_width = font_metrics.width(status_text)
            button_width = max(MIN_BUTTON_WIDTH, min(MAX_BUTTON_WIDTH, text_width + 20))
            
            # 创建状态按钮
            btn = QPushButton(status_text)
            btn.setObjectName(f"StatusBtn_{status_value}")
            btn.setProperty("status", status_value)
            btn.setProperty("selected", False)
            btn.setCheckable(True)
            btn.setFixedSize(button_width, BUTTON_HEIGHT)
            btn.setFont(font)
            
            # 绿色选中样式（与分类按钮一致）
            btn_name = btn.objectName()
            btn.setStyleSheet(f"""
                QPushButton#{btn_name} {{
                    background: white;
                    border: 1px solid #e0e0e0;
                    border-radius: 8px;
                    color: #374151;
                    font-weight: 500;
                    padding: 8px 12px;
                }}
                QPushButton#{btn_name}:hover {{
                    background: #f8fafc;
                    border: 1px solid #d0d0d0;
                    transform: scale(1.02);
                }}
                QPushButton#{btn_name}:checked {{
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 #22c55e, stop:1 #16a34a);
                    border: 2px solid #22c55e;
                    color: white;
                    font-weight: 600;
                }}
                QPushButton#{btn_name}:checked:hover {{
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 #16a34a, stop:1 #15803d);
                    transform: scale(1.05);
                }}
            """)
            
            # 连接点击事件
            btn.toggled.connect(lambda checked, st=status_value: self._on_status_button_toggled(st, checked))
            
            button_widgets.append((btn, button_width))
            self.status_checkboxes[status_value] = btn  # 保持兼容性
        
        # 自适应布局计算
        available_width = 260
        best_layout = self._calculate_button_grid_layout(button_widgets, available_width, BUTTON_SPACING)
        
        # 放置按钮
        for i, (btn, btn_width) in enumerate(button_widgets):
            row = i // best_layout['cols']
            col = i % best_layout['cols']
            
            x = best_layout['left_margin'] + col * (best_layout['avg_width'] + BUTTON_SPACING)
            y = GRID_PADDING + row * (BUTTON_HEIGHT + BUTTON_SPACING)
            
            btn.setParent(grid_widget)
            btn.move(x, y)
            btn.setFixedWidth(best_layout['avg_width'])
        
        # 调整容器高度
        total_height = GRID_PADDING * 2 + best_layout['rows'] * BUTTON_HEIGHT + (best_layout['rows'] - 1) * BUTTON_SPACING
        grid_widget.setFixedHeight(total_height)
        
        return grid_widget
    
    def _on_status_button_toggled(self, status, checked):
        """
        处理状态按钮切换事件
        """
        print(f"[筛选按钮] 状态 {status} 切换为 {'选中' if checked else '未选中'}")
    
    def setup_connections(self):
        """
        设置信号连接
        对应JavaScript中的筛选事件监听器
        """
        # 关闭按钮
        self.close_btn.clicked.connect(self.panel_closed.emit)
        
        # 操作按钮
        self.apply_btn.clicked.connect(self._apply_filters)
        self.reset_btn.clicked.connect(self._reset_filters)
    
    def _apply_filters(self):
        """
        应用筛选条件
        对应JavaScript中的applyFilters函数
        收集用户选择的筛选选项，更新应用状态，执行筛选
        """
        # 收集选中的分类筛选
        selected_categories = []
        for category_value, checkbox in self.category_checkboxes.items():
            if checkbox.isChecked():
                selected_categories.append(category_value)
        
        # 收集选中的状态筛选
        selected_statuses = []
        for status_value, checkbox in self.status_checkboxes.items():
            if checkbox.isChecked():
                selected_statuses.append(status_value)
        
        # 发出筛选应用信号
        self.filters_applied.emit(selected_categories, selected_statuses)
        
        # 关闭面板
        self.panel_closed.emit()
    
    def _reset_filters(self):
        """
        重置筛选条件 - 适配按钮模式
        对应JavaScript中的resetFilters函数
        清除所有按钮选择，重置应用状态
        """
        # 清除所有分类按钮
        for button in self.category_checkboxes.values():
            button.setChecked(False)
        
        # 清除所有状态按钮
        for button in self.status_checkboxes.values():
            button.setChecked(False)
        
        # 发出重置信号
        self.filters_reset.emit()
    
    def set_selected_filters(self, categories: list, statuses: list):
        """
        设置选中的筛选条件 - 适配按钮模式
        用于恢复之前的筛选状态
        """
        # 设置分类按钮状态
        for category_value, button in self.category_checkboxes.items():
            button.setChecked(category_value in categories)
        
        # 设置状态按钮状态
        for status_value, button in self.status_checkboxes.items():
            button.setChecked(status_value in statuses)
    
    def get_selected_filters(self) -> tuple:
        """
        获取当前选中的筛选条件 - 适配按钮模式
        返回 (categories, statuses) 元组
        """
        categories = [
            category_value for category_value, button in self.category_checkboxes.items()
            if button.isChecked()
        ]
        
        statuses = [
            status_value for status_value, button in self.status_checkboxes.items()
            if button.isChecked()
        ]
        
        return categories, statuses
    
    def clear_all_filters(self):
        """清除所有筛选条件"""
        self._reset_filters()
    
    def has_active_filters(self) -> bool:
        """检查是否有活跃的筛选条件"""
        categories, statuses = self.get_selected_filters()
        return bool(categories or statuses)