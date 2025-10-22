"""
现代化筛选悬浮卡片 - 全新卡片化设计
==========================================
采用卡片式筛选选项，类似工具卡片的自适应布局
悬浮式筛选卡片，现代化UI设计，绿色选中主题

⚠️  铁律：禁止使用 QLabel 和 QText 系列组件！
🚫 IRON RULE: NEVER USE QLabel, QTextEdit, QTextBrowser, QPlainTextEdit
✅ 替代方案: 使用 smart_text_module.py 中的智能文本组件
📋 原因: QLabel/QText 存在文字截断、字体渲染、DPI适配等问题
"""

import sys
import traceback
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QScrollArea, QFrame, QGraphicsDropShadowEffect,
    QGridLayout, QSizePolicy
)
from PyQt5.QtCore import (
    Qt, pyqtSignal, QRect, QPropertyAnimation, 
    QEasingCurve, QPoint, QSize
)
from PyQt5.QtGui import (
    QPainter, QLinearGradient, QColor, QBrush, QPen,
    QFont, QFontMetrics, QPainterPath
)
from data.models import ToolCategory, ToolStatus
from utils.comprehensive_logger import get_comprehensive_logger

# 添加日志记录
def log_error(func_name, error):
    """记录错误到文件"""
    try:
        with open("filter_panel_error.log", "a", encoding="utf-8") as f:
            f.write(f"\n{'='*50}\n")
            f.write(f"Function: {func_name}\n")
            f.write(f"Error: {str(error)}\n")
            f.write(f"Traceback:\n{traceback.format_exc()}\n")
            f.write(f"{'='*50}\n")
    except:
        pass


class SmartTextWidget(QWidget):
    """
    🎯 智能文本组件 - 基于paintEvent的高性能文本渲染
    ===============================================
    
    优势:
    - 完全避免QLabel截断问题
    - 高性能GPU渲染
    - 自动文字居中和自适应
    - 支持中文字体优化
    - 可自定义颜色和字体
    """
    
    def __init__(self, text="", font_size=11, color="#333333", parent=None):
        super().__init__(parent)
        self.text = text
        self.font_size = font_size
        self.color = QColor(color)
        self.font_family = "微软雅黑"  # 中文优化字体
        
        # 设置最小尺寸 - 根据字体大小调整
        min_height = 28 if self.font_size < 10 else 36  # 8px字体需要更少空间
        self.setMinimumHeight(min_height)
        
        # 计算文字尺寸用于布局
        self._calculate_text_size()
    
    def _calculate_text_size(self):
        """计算文字的实际尺寸"""
        font = QFont(self.font_family, self.font_size)
        metrics = QFontMetrics(font)
        
        self.text_width = metrics.horizontalAdvance(self.text)
        self.text_height = metrics.height()
        
        # 设置推荐尺寸
        self.setMinimumWidth(self.text_width + 20)  # 左右各10px边距
    
    def setText(self, text):
        """设置文字内容"""
        self.text = text
        self._calculate_text_size()
        self.update()  # 触发重绘
    
    def setTextColor(self, color):
        """设置文字颜色"""
        if isinstance(color, str):
            self.color = QColor(color)
        else:
            self.color = color
        self.update()
    
    def setFontSize(self, size):
        """设置字体大小"""
        self.font_size = size
        self._calculate_text_size()
        self.update()
    
    def paintEvent(self, event):
        """🎯 paintEvent绘制 - 核心渲染逻辑"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)  # 抗锯齿
        painter.setRenderHint(QPainter.TextAntialiasing)  # 文字抗锯齿
        
        # 设置字体 - 根据字体大小调整粗细
        if self.font_size >= 10:  # 主标题和分类标题使用加粗
            weight = QFont.Bold      # 加粗字体
        else:
            weight = QFont.Normal    # 卡片文字使用普通字体
            
        font = QFont(self.font_family, self.font_size, weight)
        painter.setFont(font)
        painter.setPen(self.color)
        
        # 计算文字绘制区域
        text_rect = self.rect()
        
        # 绘制文字 - 自动居中，支持自动换行
        flags = Qt.AlignCenter | Qt.TextWordWrap
        painter.drawText(text_rect, flags, self.text)


class SmartTitleWidget(SmartTextWidget):
    """
    🎯 智能标题组件 - 专用于区域标题
    ===============================
    """
    
    def __init__(self, text="", parent=None):
        super().__init__(text, font_size=8, color="#374151", parent=parent)  # 分类标题: 8px加粗
        self.setMinimumHeight(20)  # 相应降低高度
        
    def paintEvent(self, event):
        """标题样式的paintEvent"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.TextAntialiasing)
        
        # 标题字体 - 加粗
        font = QFont(self.font_family, self.font_size, QFont.Bold)
        painter.setFont(font)
        painter.setPen(self.color)
        
        # 左对齐绘制标题
        text_rect = self.rect()
        painter.drawText(text_rect, Qt.AlignLeft | Qt.AlignVCenter, self.text)


class FilterOptionCard(QWidget):
    """
    筛选选项卡片 - 类似工具卡片的设计
    支持选中/未选中状态，带动画效果
    """
    
    clicked = pyqtSignal(str)  # 发送选项ID
    
    def __init__(self, option_id, option_text, parent=None):
        super().__init__(parent)
        self.option_id = option_id
        self.option_text = option_text
        self.is_selected = False
        
        # 颜色主题 - 绿色选中系统
        self.colors = {
            'bg_normal': QColor(255, 255, 255),      # 白色背景
            'bg_hover': QColor(248, 250, 252),       # #f8fafc 悬停
            'bg_selected': QColor(34, 197, 94),      # #22c55e 绿色选中
            'border_normal': QColor(229, 231, 235),  # #e5e7eb 边框
            'border_hover': QColor(209, 213, 219),   # #d1d5db 悬停边框
            'border_selected': QColor(34, 197, 94),  # #22c55e 选中边框
            'text_normal': QColor(55, 65, 81),       # #374151 深色文字
            'text_selected': QColor(255, 255, 255),  # 白色文字
        }
        
        self._init_ui()
        self._setup_animations()
        
        # 鼠标跟踪和悬停状态
        self.setMouseTracking(True)
        self.is_hovered = False

    def set_option_text(self, text: str):
        """更新显示文本并重绘"""
        self.option_text = text
        # 重新计算最小宽度以适应新文本
        font = QFont("微软雅黑", 8, QFont.Normal)
        metrics = QFontMetrics(font)
        text_width = metrics.horizontalAdvance(self.option_text)
        self.setMinimumWidth(max(80, text_width + 24))
        self.update()
        
    def _init_ui(self):
        """🎯 初始化UI - 使用paintEvent绘制文字"""
        self.setFixedHeight(30)  # 进一步降低高度适应8px字体
        self.setMinimumWidth(80)  # 最小宽度
        self.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Fixed)
        
        # 计算文字尺寸用于布局优化
        font = QFont("微软雅黑", 8, QFont.Normal)  # 与绘制时保持一致: 8px普通字体
        metrics = QFontMetrics(font)
        text_width = metrics.horizontalAdvance(self.option_text)
        
        # 根据文字长度设置最小宽度
        self.setMinimumWidth(max(80, text_width + 24))  # 左右各12px边距
        
        # 不需要布局和QLabel - 直接使用paintEvent绘制
    
    def _setup_animations(self):
        """设置动画"""
        # 背景色动画
        self.bg_animation = QPropertyAnimation(self, b"geometry")
        self.bg_animation.setDuration(200)
        self.bg_animation.setEasingCurve(QEasingCurve.OutCubic)
    
    def _update_appearance(self):
        """🎯 更新外观 - 触发重绘"""
        try:
            # 不再需要设置QLabel样式，直接触发paintEvent重绘
            self.update()
        except Exception as e:
            log_error("FilterOptionCard._update_appearance", e)
            print(f"FilterOptionCard更新外观错误: {e}")
    
    def paintEvent(self, event):
        """🎯 paintEvent绘制 - 核心渲染逻辑"""
        try:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setRenderHint(QPainter.TextAntialiasing)
            
            # 获取当前状态的颜色 (优先级: 选中 > 悬停 > 普通)
            if self.is_selected:
                bg_color = self.colors['bg_selected']
                border_color = self.colors['border_selected']
                text_color = self.colors['text_selected']
            elif self.is_hovered:
                bg_color = self.colors['bg_hover']
                border_color = self.colors['border_hover']
                text_color = self.colors['text_normal']
            else:
                bg_color = self.colors['bg_normal']
                border_color = self.colors['border_normal']
                text_color = self.colors['text_normal']
            
            # 绘制背景和边框
            rect = self.rect().adjusted(1, 1, -1, -1)  # 调整1px避免边框被裁切
            
            # 设置画笔和画刷
            painter.setPen(QPen(border_color, 2))
            painter.setBrush(QBrush(bg_color))
            
            # 绘制圆角矩形背景
            painter.drawRoundedRect(rect, 8, 8)
            
            # 绘制文字 - 保持卡片文字适中大小
            painter.setPen(text_color)
            font = QFont("微软雅黑", 8, QFont.Normal)  # 卡片文字: 8px普通字体
            painter.setFont(font)
            
            # 计算文字绘制区域（考虑内边距，适应8px字体）
            text_rect = self.rect().adjusted(12, 6, -12, -6)  # 进一步减少垂直内边距
            
            # 居中绘制文字
            painter.drawText(text_rect, Qt.AlignCenter, self.option_text)
            
        except Exception as e:
            log_error("FilterOptionCard.paintEvent", e)
            print(f"FilterOptionCard绘制错误: {e}")
    
    def enterEvent(self, event):
        """🎯 鼠标进入事件 - 悬停效果"""
        self.is_hovered = True
        self.update()
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        """🎯 鼠标离开事件 - 取消悬停"""
        self.is_hovered = False
        self.update()
        super().leaveEvent(event)
    
    def mousePressEvent(self, event):
        """鼠标点击事件"""
        try:
            if event.button() == Qt.LeftButton:
                self.toggle_selection()
                self.clicked.emit(self.option_id)
        except Exception as e:
            log_error("FilterOptionCard.mousePressEvent", e)
            print(f"FilterOptionCard点击错误: {e}")
    
    def toggle_selection(self):
        """切换选中状态"""
        try:
            self.is_selected = not self.is_selected
            self._update_appearance()
        except Exception as e:
            log_error("FilterOptionCard.toggle_selection", e)
            print(f"FilterOptionCard切换状态错误: {e}")
    
    def set_selected(self, selected):
        """设置选中状态"""
        if self.is_selected != selected:
            self.is_selected = selected
            self._update_appearance()
    
    def is_option_selected(self):
        """获取选中状态"""
        return self.is_selected


class AdaptiveGridLayout(QVBoxLayout):
    """
    🎯 真正自适应网格布局 - 基于容器宽度的智能布局
    =============================================
    特性:
    - 根据实际容器宽度动态计算每行卡片数量
    - 考虑卡片文字长度，避免截断
    - 支持窗口大小变化时自动重新布局
    - 完全避免超出窗口问题
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.cards = []
        self.rows = []
        self.last_width = 0  # 记录上次容器宽度，用于检测变化
        
    def add_card(self, card):
        """添加卡片"""
        self.cards.append(card)
        self._relayout()
    
    def check_and_relayout(self):
        """🎯 检查容器宽度变化，必要时重新布局"""
        if hasattr(self.parent(), 'width') and self.parent():
            current_width = self.parent().width()
            if abs(current_width - self.last_width) > 20:  # 宽度变化超过20px时重新布局
                self.last_width = current_width
                self._relayout()
    
    def clear_cards(self):
        """清空所有卡片"""
        for card in self.cards:
            card.setParent(None)
        self.cards.clear()
        self._clear_rows()
    
    def _clear_rows(self):
        """清空行布局"""
        try:
            # 直接清空主布局中的所有widget
            while self.count():
                item = self.takeAt(0)
                if item and item.widget():
                    widget = item.widget()
                    widget.setParent(None)  # 安全移除
                    widget.deleteLater()    # 延迟删除
            self.rows.clear()
        except Exception as e:
            log_error("AdaptiveGridLayout._clear_rows", e)
            print(f"清空行布局错误: {e}")
    
    def _relayout(self):
        """重新布局"""
        self._clear_rows()
        
        if not self.cards:
            return
        
        # 🎯 真正的自适应计算 - 基于实际容器宽度
        if hasattr(self.parent(), 'width') and self.parent():
            container_width = self.parent().width() - 40  # 扣除左右边距
        else:
            container_width = 280  # 默认宽度
        
        # 计算每个卡片的实际宽度（找最长的卡片）
        max_card_width = 80  # 默认最小宽度
        for card in self.cards:
            if hasattr(card, 'text_width'):
                card_width = card.text_width + 24  # 文字宽度 + 内边距
                max_card_width = max(max_card_width, card_width)
        
        card_spacing = 8       # 卡片间距
        
        # 🎯 真正自适应：根据容器宽度和卡片宽度计算
        if container_width > max_card_width:
            cards_per_row = max(1, (container_width + card_spacing) // (max_card_width + card_spacing))
        else:
            cards_per_row = 1  # 容器太小时每行只放一个
        
        print(f"【自适应DEBUG】容器宽度:{container_width}, 最大卡片宽度:{max_card_width}, 每行卡片数:{cards_per_row}")
        
        # 创建行
        for i in range(0, len(self.cards), cards_per_row):
            row_layout = QHBoxLayout()
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.setSpacing(card_spacing)
            
            # 添加卡片到行
            row_cards = self.cards[i:i + cards_per_row]
            for card in row_cards:
                row_layout.addWidget(card)
            
            # 添加弹性空间
            row_layout.addStretch()
            
            # 包装为widget
            row_widget = QWidget()
            row_widget.setLayout(row_layout)
            
            # 添加到主布局
            self.addWidget(row_widget)
            self.rows.append(row_layout)


class ModernFilterCard(QWidget):
    """
    现代化筛选悬浮卡片 - 全新卡片化设计
    """
    
    # 信号定义 - 保持与旧版本完全一致
    filters_applied = pyqtSignal(list, list)    # 应用筛选 (categories, statuses)
    filters_reset = pyqtSignal()                # 重置筛选
    card_closed = pyqtSignal()                  # 卡片关闭
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        try:
            print("【DEBUG】步骤1: 创建筛选选项存储")
            # 筛选选项存储
            self.category_cards = {}
            self.status_cards = {}
            
            print("【DEBUG】步骤2: 设置窗口属性")
            # 窗口属性 - 与下载卡片保持一致，添加圆角支持
            self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
            self.setAttribute(Qt.WA_ShowWithoutActivating)
            self.setAttribute(Qt.WA_TranslucentBackground)  # 支持透明背景和圆角
            # 🎯 动态高度设计：宽度固定360px，高度根据内容自适应
            self.setFixedWidth(360)
            self.setMinimumHeight(200)  # 最小高度保证
            self.setMaximumHeight(600)  # 最大高度限制，防止超出屏幕
            self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.MinimumExpanding)
            
            print("【DEBUG】步骤3: 设置颜色主题")
            # 颜色主题 - 与下载卡片保持一致
            self.colors = {
                'card_bg': QColor(255, 255, 255),
                'border': QColor(229, 231, 235),        # #e5e7eb
                'shadow': QColor(0, 0, 0, 20),
                'title': QColor(17, 24, 39),            # #111827
                'subtitle': QColor(75, 85, 99),         # #4b5563
                'button_primary': QColor(34, 197, 94),  # #22c55e 绿色主题
                'button_secondary': QColor(156, 163, 175), # #9ca3af
                'separator': QColor(243, 244, 246),     # #f3f4f6
            }
            
            print("【DEBUG】步骤4: 开始初始化UI")
            self._init_ui()
            print("【DEBUG】步骤5: UI初始化完成，开始设置阴影")
            self._setup_shadow()
            
            print("【DEBUG】ModernFilterCard 初始化完成 - 已启用圆角支持和卡片化设计")
            # 连接语言切换
            try:
                from utils.translator import get_translator
                get_translator().languageChanged.connect(self.retranslateUi)
            except Exception:
                pass
        except Exception as e:
            log_error("ModernFilterCard.__init__", e)
            print(f"ModernFilterCard初始化错误: {e}")
            raise
    
    def _init_ui(self):
        """初始化UI - 全新卡片化设计"""
        try:
            print("【DEBUG】UI步骤1: 创建主布局")
            main_layout = QVBoxLayout()
            main_layout.setContentsMargins(16, 16, 16, 16)  # 🎯 在最外层设置16px边距！
            main_layout.setSpacing(0)
            
            print("【DEBUG】UI步骤2: 创建统一卡片内容区域 (移除分割和头部分离)")
            # 🎯 动态高度：直接使用内容widget，移除滚动区域
            # 让内容直接决定面板高度，实现完美的动态布局
            
            # 如果未来内容过多需要滚动，可以这样设置：
            # scroll_area = QScrollArea()
            # scroll_area.setWidgetResizable(True)
            # scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            # scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
            # 🎯 动态高度设计：不需要复杂的滚动区域CSS
            
            print("【DEBUG】UI步骤3: 创建动态内容区域")
            # 🎯 动态高度设计：纯内容容器，无边距
            content_widget = QWidget()
            # 🎯 完全透明，边距由外层main_layout控制
            content_widget.setStyleSheet("background-color: transparent;")
            content_layout = QVBoxLayout()
            content_layout.setContentsMargins(0, 0, 0, 0)  # 🎯 无边距，纯内容
            content_layout.setSpacing(16)  # 组件间距
            
            # 🎯 统一标题行 - 主标题 + 关闭按钮
            title_row = QHBoxLayout()
            title_row.setContentsMargins(0, 0, 0, 0)
            title_row.setSpacing(0)
            
            self.main_title = SmartTextWidget(self.tr("筛选工具"), font_size=12, color="#111827")  # 主标题: 12px加粗
            title_row.addWidget(self.main_title)
            title_row.addStretch()
            
            # 关闭按钮
            close_btn = QPushButton("×")
            close_btn.setFixedSize(28, 28)
            close_btn.setStyleSheet("""
                QPushButton {
                    background-color: #f3f4f6;
                    color: #6b7280;
                    border: none;
                    border-radius: 14px;
                    font-size: 16px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #e5e7eb;
                    color: #374151;
                }
                QPushButton:pressed {
                    background-color: #d1d5db;
                }
            """)
            close_btn.clicked.connect(self._on_close_clicked)
            title_row.addWidget(close_btn)
            
            # 将标题行作为widget添加到主布局
            title_widget = QWidget()
            title_widget.setObjectName("TitleWidget")  # 设置名称便于调试
            title_widget.setFixedHeight(32)  # 🎯 固定标题区域高度，防止被拉伸
            title_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            title_widget.setLayout(title_row)
            content_layout.addWidget(title_widget)
            
            print("【DEBUG】UI步骤4: 创建分类筛选区域")
            # 添加筛选区域
            content_layout.addWidget(self._create_category_section())
            print("【DEBUG】UI步骤5: 创建状态筛选区域")
            content_layout.addWidget(self._create_status_section())
            
            print("【DEBUG】UI步骤8: 设置内容布局")
            content_widget.setLayout(content_layout)
            # 🎯 动态高度：直接将内容widget添加到主布局
            main_layout.addWidget(content_widget)
            
            print("【DEBUG】UI步骤6: 添加底部操作区域到内容中")
            # 🎯 底部操作区域直接加到内容布局中，形成统一卡片
            # 不需要额外间距，由统一的16px边距控制
            content_layout.addWidget(self._create_footer())
            
            print("【DEBUG】UI步骤7: 设置主布局")
            self.setLayout(main_layout)
            
            # 🎯 布局调试日志 - 延迟执行确保组件已创建完成
            from PyQt5.QtCore import QTimer
            QTimer.singleShot(100, self._log_layout_debug)
            
            print("【DEBUG】UI步骤8: 设置统一卡片背景和圆角")
            # 🎯 整体卡片背景 - 使用paintEvent实现完美圆角
            # 不再使用CSS样式，避免影响子组件
        except Exception as e:
            log_error("ModernFilterCard._init_ui", e)
            print(f"ModernFilterCard._init_ui错误: {e}")
            raise
    
    # 🎯 _create_header 方法已删除 - 统一到主布局中
    
    def _create_category_section(self):
        """创建分类筛选区域 - 卡片化设计"""
        section = QWidget()
        section.setObjectName("CategorySection")  # 设置名称便于调试
        section.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)  # 🎯 防止被过度拉伸
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        
        # 🎯 区域标题 - 使用智能标题组件
        self.category_title = SmartTitleWidget(self.tr("工具分类"))
        layout.addWidget(self.category_title)
        
        # 卡片容器 - 自适应网格布局
        cards_container = QWidget()
        cards_layout = AdaptiveGridLayout()
        
        # 分类选项卡片
        categories = [
            ('sequence_analysis', self.tr('序列分析')),
            ('phylogenetics', self.tr('进化分析')),
            ('genomics', self.tr('基因组学')),
            ('alignment', self.tr('序列比对')),
            ('structure', self.tr('结构分析')),
            ('annotation', self.tr('基因注释'))
        ]
        
        for category_id, category_name in categories:
            card = FilterOptionCard(category_id, category_name)
            # 修复闭包问题：使用默认参数捕获当前值
            card.clicked.connect(lambda cat, cid=category_id: self._on_category_card_clicked(cid))
            cards_layout.add_card(card)
            self.category_cards[category_id] = card
        
        cards_container.setLayout(cards_layout)
        layout.addWidget(cards_container)
        
        section.setLayout(layout)
        return section
    
    def _create_status_section(self):
        """创建状态筛选区域 - 卡片化设计"""
        section = QWidget()
        section.setObjectName("StatusSection")  # 设置名称便于调试
        section.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)  # 🎯 防止被过度拉伸
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        
        # 🎯 区域标题 - 使用智能标题组件
        self.status_title = SmartTitleWidget(self.tr("安装状态"))
        layout.addWidget(self.status_title)
        
        # 卡片容器 - 自适应网格布局
        cards_container = QWidget()
        cards_layout = AdaptiveGridLayout()
        
        # 状态选项卡片
        statuses = [
            ('installed', self.tr('已安装')),
            ('available', self.tr('可安装')),
            ('update', self.tr('需要更新'))
        ]
        
        for status_id, status_name in statuses:
            card = FilterOptionCard(status_id, status_name)
            # 修复闭包问题：使用默认参数捕获当前值
            card.clicked.connect(lambda stat, sid=status_id: self._on_status_card_clicked(sid))
            cards_layout.add_card(card)
            self.status_cards[status_id] = card
        
        cards_container.setLayout(cards_layout)
        layout.addWidget(cards_container)
        
        section.setLayout(layout)
        return section
    
    def _create_footer(self):
        """🎯 创建完全融合式操作按钮区域 - 与内容无缝连接"""
        footer = QWidget()
        footer.setObjectName("FooterWidget")  # 设置名称便于调试
        footer.setFixedHeight(30)  # 🎯 仅按钮高度，边距由主容器控制
        footer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)  # 🎯 确保不被拉伸
        # 🎯 完全透明，无任何独立样式
        footer.setStyleSheet("background-color: transparent; border: none;")
        
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)  # 🎯 按钮区域不设独立边距，由主容器统一控制
        layout.setSpacing(12)
        
        # 重置按钮 - 与应用按钮并列
        self.reset_btn = QPushButton(self.tr("重置"))
        self.reset_btn.setFixedHeight(30)  # 适应小字体，降低高度
        self.reset_btn.setStyleSheet("""
            QPushButton {
                background-color: #f8fafc;
                color: #64748b;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                padding: 0 16px;
                font-weight: 500;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #f1f5f9;
                color: #475569;
                border-color: #cbd5e1;
            }
            QPushButton:pressed {
                background-color: #e2e8f0;
            }
        """)
        self.reset_btn.clicked.connect(self._on_reset_clicked)
        layout.addWidget(self.reset_btn)
        
        # 弹性空间
        layout.addStretch()
        
        # 应用按钮 - 绿色主题，融合式设计
        self.apply_btn = QPushButton(self.tr("应用筛选"))
        self.apply_btn.setFixedHeight(30)  # 与重置按钮相同高度
        self.apply_btn.setStyleSheet("""
            QPushButton {
                background-color: #22c55e;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 0 20px;
                font-weight: 600;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #16a34a;
            }
            QPushButton:pressed {
                background-color: #15803d;
            }
        """)
        self.apply_btn.clicked.connect(self._on_apply_clicked)
        layout.addWidget(self.apply_btn)
        
        # 绑定布局并返回footer
        footer.setLayout(layout)
        return footer
    
    def retranslateUi(self, locale: str = None):
        """语言变更时，更新标题与选项文本"""
        try:
            if hasattr(self, 'main_title'):
                self.main_title.setText(self.tr("筛选工具"))
            if hasattr(self, 'category_title'):
                self.category_title.setText(self.tr("工具分类"))
            if hasattr(self, 'status_title'):
                self.status_title.setText(self.tr("安装状态"))
            if hasattr(self, 'reset_btn'):
                self.reset_btn.setText(self.tr("重置"))
            if hasattr(self, 'apply_btn'):
                self.apply_btn.setText(self.tr("应用筛选"))

            # 更新分类卡片文本
            category_map = {
                'sequence_analysis': self.tr('序列分析'),
                'phylogenetics': self.tr('进化分析'),
                'genomics': self.tr('基因组学'),
                'alignment': self.tr('序列比对'),
                'structure': self.tr('结构分析'),
                'annotation': self.tr('基因注释'),
            }
            for cid, card in getattr(self, 'category_cards', {}).items():
                if cid in category_map and hasattr(card, 'set_option_text'):
                    card.set_option_text(category_map[cid])

            # 更新状态卡片文本
            status_map = {
                'installed': self.tr('已安装'),
                'available': self.tr('可安装'),
                'update': self.tr('需要更新'),
            }
            for sid, card in getattr(self, 'status_cards', {}).items():
                if sid in status_map and hasattr(card, 'set_option_text'):
                    card.set_option_text(status_map[sid])
        except Exception as e:
            log_error("ModernFilterCard.retranslateUi", e)

    # _on_reset_clicked 已存在：清空选择并关闭面板
        
        footer.setLayout(layout)
        return footer
    
    def _setup_shadow(self):
        """设置阴影效果 - 与下载卡片保持一致"""
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setXOffset(0)
        shadow.setYOffset(4)
        shadow.setColor(self.colors['shadow'])
        self.setGraphicsEffect(shadow)
    
    def paintEvent(self, event):
        """🎯 绘制统一的卡片背景和圆角"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 绘制圆角背景 - 现代化卡片设计
        bg_color = QColor(255, 255, 255)  # 白色背景
        border_color = QColor(229, 231, 235, 180)  # #e5e7eb 边框，半透明
        
        # 设置画笔和画刷
        painter.setPen(QPen(border_color, 1))
        painter.setBrush(QBrush(bg_color))
        
        # 绘制圆角矩形 - 整个卡片的背景，现代化圆角
        rect = self.rect().adjusted(1, 1, -1, -1)  # 调整避免边框被裁切
        painter.drawRoundedRect(rect, 12, 12)  # 12px 圆角，现代化设计
        
        # 绘制微妙的内阴影效果（可选）
        inner_shadow_color = QColor(0, 0, 0, 8)  # 极淡的内阴影
        painter.setPen(QPen(inner_shadow_color, 1))
        painter.setBrush(Qt.NoBrush)
        inner_rect = self.rect().adjusted(2, 2, -2, -2)
        painter.drawRoundedRect(inner_rect, 11, 11)
    
    def _on_category_card_clicked(self, category_id):
        """分类卡片点击"""
        print(f"【DEBUG】分类卡片点击: {category_id}")
    
    def _on_status_card_clicked(self, status_id):
        """状态卡片点击"""
        print(f"【DEBUG】状态卡片点击: {status_id}")
    
    def _on_apply_clicked(self):
        """应用筛选"""
        print("【DEBUG】应用筛选按钮被点击")
        
        # 收集选中的分类
        selected_categories = []
        for category_id, card in self.category_cards.items():
            if card.is_option_selected():
                selected_categories.append(category_id)
        
        # 收集选中的状态
        selected_statuses = []
        for status_id, card in self.status_cards.items():
            if card.is_option_selected():
                selected_statuses.append(status_id)
        
        print(f"【DEBUG】应用筛选: 分类={selected_categories}, 状态={selected_statuses}")
        
        # 🎯 修复：先发出筛选信号，然后发出关闭信号让主窗口清理遮罩层
        self.filters_applied.emit(selected_categories, selected_statuses)
        self.hide()
        self.card_closed.emit()  # 🎯 发送关闭信号，触发主窗口清理遮罩层
    
    def _on_reset_clicked(self):
        """重置筛选"""
        print("【DEBUG】重置筛选按钮被点击")
        
        # 清除所有选择
        for card in self.category_cards.values():
            card.set_selected(False)
        
        for card in self.status_cards.values():
            card.set_selected(False)
        
        # 🎯 修复：发出重置信号，并关闭面板（清理遮罩层）
        self.filters_reset.emit()
        self.hide()
        self.card_closed.emit()  # 🎯 发送关闭信号，触发主窗口清理遮罩层
    
    def _on_close_clicked(self):
        """关闭卡片"""
        print("【DEBUG】关闭筛选卡片")
        self.hide()
        self.card_closed.emit()
    
    def resizeEvent(self, event):
        """🎯 窗口大小变化事件 - 触发自适应重新布局"""
        super().resizeEvent(event)
        
        # 延迟触发重新布局，避免频繁重绘
        if not hasattr(self, '_resize_timer'):
            from PyQt5.QtCore import QTimer
            self._resize_timer = QTimer()
            self._resize_timer.setSingleShot(True)
            self._resize_timer.timeout.connect(self._do_adaptive_relayout)
        
        self._resize_timer.start(100)  # 100ms延迟
    
    def _do_adaptive_relayout(self):
        """🎯 执行自适应重新布局"""
        print("【自适应DEBUG】窗口大小变化，触发重新布局")
        
        # 这里需要找到并触发自适应布局的重新计算
        # 由于布局结构较复杂，我们通过查找所有AdaptiveGridLayout来触发
        def find_and_relayout(widget):
            if hasattr(widget, '_relayout'):
                widget._relayout()
            for child in widget.findChildren(QWidget):
                if hasattr(child, '_relayout'):
                    child._relayout()
        
        find_and_relayout(self)
    
    def set_selected_filters(self, categories, statuses):
        """设置选中的筛选条件"""
        try:
            print(f"【DEBUG】设置筛选条件: 分类={categories}, 状态={statuses}")
            
            # 设置分类选择状态
            for category_id, card in self.category_cards.items():
                card.set_selected(category_id in categories)
            
            # 设置状态选择状态
            for status_id, card in self.status_cards.items():
                card.set_selected(status_id in statuses)
        except Exception as e:
            log_error("ModernFilterCard.set_selected_filters", e)
            print(f"设置筛选条件错误: {e}")
    
    def _log_layout_debug(self):
        """🎯 布局调试日志 - 诊断边距和空间分配问题"""
        try:
            logger = get_comprehensive_logger()
            
            # 开始布局诊断
            logger.log_debug("FilterCard-Layout", "开始诊断筛选卡片布局边距和空间分配")
            
            # 1. 卡片整体尺寸
            card_size = f"{self.width()}x{self.height()}"
            logger.log_debug("FilterCard-Layout", f"卡片总尺寸: {card_size}")
            
            # 2. 查找关键组件 - 动态高度版本
            content_widget = self.findChild(QWidget)  # 直接查找内容widget
                
            if content_widget:
                content_size = f"{content_widget.width()}x{content_widget.height()}"
                logger.log_debug("FilterCard-Layout", f"内容区域尺寸: {content_size}")
                logger.log_debug("FilterCard-Layout", f"动态高度模式: 内容直接决定面板高度")
                
                # 3. 内容布局边距验证
                layout = content_widget.layout()
                if layout:
                    margins = layout.contentsMargins()
                    spacing = layout.spacing()
                    
                    margins_info = {
                        "top": margins.top(),
                        "left": margins.left(), 
                        "right": margins.right(),
                        "bottom": margins.bottom(),
                        "spacing": spacing
                    }
                    logger.log_debug("FilterCard-Layout", f"内容布局边距设置: {margins_info}")
                    
                    # 4. 各个子组件尺寸分析
                    components_info = []
                    for i in range(layout.count()):
                        item = layout.itemAt(i)
                        if item and item.widget():
                            widget = item.widget()
                            widget_name = widget.objectName() or widget.__class__.__name__
                            widget_size = f"{widget.width()}x{widget.height()}"
                            components_info.append(f"{widget_name}: {widget_size}")
                    
                    logger.log_debug("FilterCard-Layout", f"子组件尺寸分析: {components_info}")
            
            # 5. 空间计算分析
            if content_widget:
                content_height = content_widget.height()
                margins_total = 32  # 16px top + 16px bottom
                available_height = content_height - margins_total
                
                space_analysis = {
                    "内容区域总高度": f"{content_height}px",
                    "边距占用": f"{margins_total}px", 
                    "实际内容可用高度": f"{available_height}px",
                    "边距占比": f"{(margins_total/content_height*100):.1f}%" if content_height > 0 else "N/A"
                }
                logger.log_debug("FilterCard-Layout", f"空间分配分析: {space_analysis}")
            
            logger.log_debug("FilterCard-Layout", "筛选卡片布局诊断完成")
            
        except Exception as e:
            logger = get_comprehensive_logger()
            logger.log_error("FilterCard-Layout", f"布局诊断出错: {str(e)}")
    
    def resizeEvent(self, event):
        """🎯 窗口大小变化事件 - 触发布局调试"""
        super().resizeEvent(event)
        # 触发调试日志
        from PyQt5.QtCore import QTimer
        QTimer.singleShot(50, self._log_layout_debug)
    
    def show_aligned_to_toolbar(self, toolbar_bottom, button_rect, window_rect):
        """
        🎯 动态高度版本 - 智能定位显示卡片
        根据实际内容高度自适应定位，紧贴工具栏分界线
        """
        try:
            print(f"【DEBUG】动态高度版本 - 智能定位卡片: toolbar_bottom={toolbar_bottom}")
            
            # 🎯 先显示以确定实际高度，然后定位
            self.show()
            self.adjustSize()  # 根据内容调整到合适大小
            
            actual_height = self.height()
            actual_width = self.width()  # 应该是360px
            print(f"【DEBUG】动态尺寸: {actual_width}x{actual_height}")
            
            # 垂直位置：紧贴工具栏底部，但要确保不超出屏幕
            y = toolbar_bottom
            window_height = window_rect.height()
            if y + actual_height > window_height:
                y = window_height - actual_height - 10  # 留10px底部边距
                print(f"【DEBUG】调整Y位置防止超出屏幕: y={y}")
            
            # 水平位置：靠右对齐
            margin = 2
            window_width = window_rect.width()
            x = window_width - actual_width - margin
            
            final_pos = QPoint(x, y)
            print(f"【DEBUG】动态高度最终位置: {final_pos}")
            
            self.raise_()
            
            # 滑入动画：从稍高的位置滑入
            start_y = y - 15
            self.move(x, start_y)
            
            # 创建位置动画
            if not hasattr(self, 'slide_animation'):
                from PyQt5.QtCore import QPropertyAnimation
                self.slide_animation = QPropertyAnimation(self, b"pos")
                self.slide_animation.setDuration(250)
                self.slide_animation.setEasingCurve(QEasingCurve.OutCubic)
            
            self.slide_animation.setStartValue(QPoint(x, start_y))
            self.slide_animation.setEndValue(final_pos)
            self.slide_animation.start()
            
            self.activateWindow()
        except Exception as e:
            log_error("ModernFilterCard.show_aligned_to_toolbar", e)
            print(f"显示动态筛选卡片错误: {e}")
            # 尝试简单显示
            try:
                self.show()
                self.adjustSize()
            except:
                pass
