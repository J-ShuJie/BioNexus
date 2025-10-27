"""
工具详情页面组件（页面版本，非弹窗）
超精简版本 - 专注核心功能的启动器体验

⚠️⚠️⚠️ 响应式布局重要警告 ⚠️⚠️⚠️
===========================================
此文件包含关键的响应式布局配置，修改时请特别注意以下要点：

1. 🔥 绝对不能删除或修改 setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
   这是防止内容被左右截断的最关键配置！

2. 🔥 content_widget.setSizePolicy() 的配置不能随意改动
   这确保了内容能够正确适应不同窗口尺寸

3. 🔥 文本组件必须正确设置换行：QLabel用setWordWrap(True)，QTextEdit用setLineWrapMode()
   这保证文本自动换行而不是被截断

4. 🔥 使用 ResponsiveDetailPageManager 来创建滚动区域
   不要手动创建QScrollArea，这可能丢失关键配置

历史教训：在1.1.7开发过程中，曾经意外移除了响应式配置，
导致小窗口下内容被截断。此注释是为了防止类似问题再次发生。

如果需要修改布局，请先阅读 ui/responsive_layout.py 中的详细说明！
===========================================
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QScrollArea, QSizePolicy, QTextBrowser, QFrame,
    QGraphicsDropShadowEffect, QGraphicsOpacityEffect
)
from PyQt5.QtCore import Qt, pyqtSignal, QObject, QEvent, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QFont
from .responsive_layout import (
    ResponsiveDetailPageManager,
    AdaptiveStatsBar,
    validate_responsive_config
)
from .smart_paint_v2 import create_smart_label_v2
from vendor.auto_resizing.text_edit import AutoResizingTextEdit
import logging


class ToolDetailPage(QWidget):
    """工具详情页面（超精简版本）"""
    
    back_requested = pyqtSignal()  # 返回信号
    install_requested = pyqtSignal(str)
    launch_requested = pyqtSignal(str)
    uninstall_requested = pyqtSignal(str)  # 卸载信号
    
    def __init__(self, tool_data: dict, parent=None):
        super().__init__(parent)
        self.tool_data = tool_data
        
        # 初始化详细日志记录器
        self.logger = logging.getLogger(f"BioNexus.ToolDetailPage.{tool_data.get('name', 'Unknown')}")
        self.logger.setLevel(logging.DEBUG)
        
        self.logger.info(f"开始初始化工具详情页面: {tool_data.get('name', 'Unknown')}")
        
        # v1.2.5: 优化背景层次 - 主背景使用浅灰色
        self.setStyleSheet("""
            ToolDetailPage {
                background: #F5F6F8;
            }
        """)
        
        try:
            self.logger.debug("开始UI初始化")
            self.init_ui()
            self.logger.debug("UI初始化完成")
            
            self.logger.debug("开始动画设置")
            self.setup_animations()
            self.logger.debug("动画设置完成")
            
            self.logger.info(f"工具详情页面初始化成功: {tool_data.get('name', 'Unknown')}")
        except Exception as e:
            self.logger.error(f"初始化工具详情页面失败: {str(e)}", exc_info=True)
            raise
        
    def init_ui(self):
        """
        初始化UI
        
        ⚠️ 响应式配置警告：
        此方法包含防止内容截断的关键配置，修改时请极其小心！
        
        🔥 重要更新（1.1.7）：
        现在基于实际可用宽度（父容器宽度）进行自适应布局，
        而不是基于整个屏幕宽度。
        """
        try:
            self.logger.debug("=== 开始UI初始化详细步骤 ===")
            
            # 创建主布局
            self.logger.debug("创建主布局")
            main_layout = QVBoxLayout(self)
            main_layout.setContentsMargins(0, 0, 0, 0)
            main_layout.setSpacing(0)
            self.logger.debug("主布局创建成功")
            
            # 顶部返回栏
            self.logger.debug("开始创建顶部返回栏")
            top_bar = self.create_top_bar()
            main_layout.addWidget(top_bar)
            self.logger.debug("顶部返回栏创建并添加成功")
            
            # 🔥🔥🔥 关键配置：使用响应式管理器创建滚动区域
            # 这确保了所有防截断的配置都正确设置
            # 请不要手动创建 QScrollArea，这可能丢失关键配置！
            self.logger.debug("开始创建响应式滚动区域")
            scroll_area, content_container = ResponsiveDetailPageManager.create_responsive_detail_page()
            self.logger.debug("响应式滚动区域创建成功")
            
            # 🔥 关键验证：确保响应式配置正确（调试用，可在发布时移除）
            if __debug__:  # 只在调试模式下验证
                self.logger.debug("验证响应式配置")
                validate_responsive_config(scroll_area)
                self.logger.debug("响应式配置验证通过")
            
            # 获取内容布局，用于添加各个区块
            self.logger.debug("获取内容布局")
            content_layout = content_container.layout
            self.logger.debug("内容布局获取成功")
            
            # 🔥 NEW: 检测实际可用宽度并确定布局模式
            # 这是解决子容器宽度问题的关键！
            self.logger.debug("开始检测可用宽度")
            self.available_width = self._get_available_width()
            self.layout_mode = ResponsiveDetailPageManager.get_layout_mode(self.available_width)
            self.logger.debug(f"宽度检测完成: available_width={self.available_width}, layout_mode={self.layout_mode}")
        
            # 调试信息（可在发布时移除）
            if __debug__:
                print(f"📐 详情页面可用宽度: {self.available_width}px")
                print(f"📐 使用布局模式: {self.layout_mode}")
            
            # 1. 顶部概览区
            self.logger.debug("开始创建顶部概览区")
            header_section = self.create_header_section()
            content_layout.addWidget(header_section)
            self.logger.debug("顶部概览区创建并添加成功")
            
            # 2. 统计信息栏已移除（2025设计优化：信息整合到其他区域）
            
            # 3. 工具详细介绍区域
            self.logger.debug("开始创建工具详细介绍区域")
            description_section = self.create_description_section()
            content_layout.addWidget(description_section)
            self.logger.debug("工具详细介绍区域创建并添加成功")
            
            # 4. 技术规格区域
            self.logger.debug("开始创建技术规格区域")
            specs_section = self.create_tech_specs_section()
            content_layout.addWidget(specs_section)
            self.logger.debug("技术规格区域创建并添加成功")
            
            # 🔥 关键步骤：将滚动区域添加到主布局
            # 注意：content_container已经通过ResponsiveDetailPageManager正确设置到scroll_area中
            self.logger.debug("将滚动区域添加到主布局")
            main_layout.addWidget(scroll_area)
            self.logger.debug("滚动区域添加成功")
            
            self.logger.debug("=== UI初始化详细步骤完成 ===")
            
        except Exception as e:
            self.logger.error(f"UI初始化失败在步骤中: {str(e)}", exc_info=True)
            raise
        
    def _get_available_width(self):
        """
        获取详情页面的实际可用宽度
        
        🔥 关键方法：这是解决子容器宽度问题的核心
        
        返回的是详情页面在主窗口中实际分配到的宽度，
        而不是整个屏幕或主窗口的宽度。
        
        @return: 可用宽度（像素）
        """
        # 尝试获取父容器的宽度
        if self.parent():
            parent_width = self.parent().width()
            # 如果父容器宽度有效，使用它
            if parent_width > 0:
                return parent_width
        
        # 尝试获取自身的宽度（可能在初始化时还是0）
        self_width = self.width()
        if self_width > 0:
            return self_width
        
        # 默认返回一个合理的值（假设详情页面占主窗口的60%）
        # 这是一个估计值，用于初始化时
        from PyQt5.QtWidgets import QApplication
        screen = QApplication.desktop().screenGeometry()
        # 假设详情页面占主窗口的60%，主窗口占屏幕的80%
        estimated_width = int(screen.width() * 0.8 * 0.6)
        
        # 限制在合理范围内
        return min(max(estimated_width, 400), 800)  # 最小400px，最大800px
    
    def create_top_bar(self):
        """创建顶部返回栏"""
        top_bar = QWidget()
        top_bar.setFixedHeight(50)
        top_bar.setStyleSheet("""
            QWidget {
                background-color: white;
            }
        """)
        
        # v1.2.5: 添加底部阴影效果代替边框
        try:
            from PyQt5.QtGui import QColor
            shadow = QGraphicsDropShadowEffect()
            shadow.setBlurRadius(5)
            shadow.setColor(QColor(0, 0, 0, 15))
            shadow.setOffset(0, 2)
            top_bar.setGraphicsEffect(shadow)
        except ImportError:
            pass
        
        layout = QHBoxLayout(top_bar)
        layout.setContentsMargins(20, 0, 20, 0)
        
        # 返回按钮
        back_btn = QPushButton(self.tr("← Back"))
        back_btn.setFixedSize(80, 32)
        back_btn.setStyleSheet("""
            QPushButton {
                background-color: #f1f5f9;
                color: #475569;
                border: none;
                border-radius: 6px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #e2e8f0;
            }
        """)
        back_btn.clicked.connect(self.back_requested.emit)
        
        layout.addWidget(back_btn)
        layout.addStretch()
        
        return top_bar
        
    def create_header_section(self):
        """
        创建顶部概览区
        
        🔥 响应式更新（1.1.7）：
        根据布局模式调整头部布局：
        - 紧凑模式：简化按钮，垂直排列部分元素
        - 中等模式：适度简化
        - 完整模式：正常显示
        """
        header_widget = QWidget()
        
        # 🔥 NEW: 根据布局模式调整高度
        # v1.2.6 FIX: 增加高度以防止按钮和时间统计被截断
        if self.layout_mode == "compact":
            header_widget.setMinimumHeight(160)  # 紧凑模式需要更高，因为可能垂直排列
        else:
            # 已安装状态需要更多高度来容纳按钮+时间统计
            if self.tool_data['status'] == 'installed':
                header_widget.setMinimumHeight(145)  # 从120增加到145，确保时间统计不被截断
            else:
                header_widget.setFixedHeight(120)  # 未安装状态保持原高度
            
        header_widget.setStyleSheet("""
            QWidget {
                background: #FFFFFF;
                border-radius: 12px;
            }
        """)
        
        # v1.2.5: 添加淡阴影效果
        try:
            from PyQt5.QtGui import QColor
            shadow = QGraphicsDropShadowEffect()
            shadow.setBlurRadius(10)
            shadow.setColor(QColor(0, 0, 0, 30))
            shadow.setOffset(0, 2)
            header_widget.setGraphicsEffect(shadow)
        except ImportError:
            pass
        
        # v1.2.6: 统一优化边距设置
        if self.layout_mode == "compact":
            header_layout = QVBoxLayout(header_widget)  # 紧凑模式使用垂直布局
            header_layout.setContentsMargins(16, 12, 16, 12)
        else:
            header_layout = QHBoxLayout(header_widget)
            header_layout.setContentsMargins(20, 16, 20, 16)
        
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
        name_label.setStyleSheet("color: #0f172a;")
        
        # 版本信息（2025设计优化：移除冗余分类显示）
        meta_label = QLabel(self.tr("Version v{0}").format(self.tool_data.get('version', 'N/A')))
        meta_label.setStyleSheet("color: #6366f1; font-size: 12px; font-weight: 500;")
        
        # ✅ 已删除重复的简短描述 - 详情页面下方已有完整的工具介绍区域
        
        info_layout.addWidget(name_label)
        info_layout.addWidget(meta_label)
        # 不再添加desc_label，避免重复信息
        
        left_layout.addWidget(icon_label)
        left_layout.addWidget(info_widget)
        left_layout.addStretch()
        
        # 右侧操作组 - v1.2.6: 移除GraphicsEffect避免渲染冲突
        right_group = QWidget()
        # v1.2.6 FIX: 设置最小尺寸确保内容不被截断
        right_group.setMinimumHeight(110)  # 确保有足够高度容纳按钮+时间统计
        right_group.setMinimumWidth(140)   # 确保有足够宽度
        right_group.setStyleSheet("""
            QWidget {
                background: rgba(248, 249, 250, 0.8);
                border-radius: 8px;
                padding: 16px;
                border: 1px solid rgba(226, 232, 240, 0.5);
            }
        """)
        
        right_layout = QVBoxLayout(right_group)
        right_layout.setSpacing(8)  # v1.2.6 FIX: 减少间距使布局更紧凑
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setAlignment(Qt.AlignCenter)  # v1.2.6 FIX: 居中对齐避免内容偏移
        
        # 🔥 v1.2.5: 按钮和时间统计在同一个卡片内
        if self.tool_data['status'] == 'installed':
            # 已安装状态：创建增强版启动+卸载按钮组合
            button_group = self.create_enhanced_button_group()
            right_layout.addWidget(button_group)
            
            # 🎮 Steam风格：按钮下方显示使用时长
            # v1.2.6 FIX: 优化时间统计样式，使其更紧凑且不会截断
            usage_time = self._get_usage_time_display()
            # 智能显示：如果是"暂未使用"，直接显示；否则显示"已使用 X小时"
            if usage_time == self.tr("暂未使用"):
                usage_time_text = usage_time
            else:
                usage_time_text = self.tr("已使用 {0}").format(usage_time)
            usage_time_label = QLabel(usage_time_text)
            usage_time_label.setFixedHeight(24)  # 固定高度避免布局问题
            usage_time_label.setStyleSheet("""
                color: #6B7280;
                font-size: 10px;        /* 稍微缩小字体 */
                font-weight: 500;
                margin-top: 8px;        /* 减少上边距 */
                padding: 4px 8px;       /* 调整内边距 */
                background: transparent; /* 移除背景避免视觉冲突 */
                border-top: 1px solid rgba(229, 231, 235, 0.5);  /* 添加顶部分隔线 */
            """)
            usage_time_label.setAlignment(Qt.AlignCenter)
            right_layout.addWidget(usage_time_label)
            
        else:
            # 未安装状态：增强版安装按钮
            install_btn = self.create_enhanced_install_button()
            right_layout.addWidget(install_btn)
        
        # 🔥 确保左右对齐和间距分配
        if self.layout_mode == "compact":
            # 紧凑模式：垂直布局
            header_layout.addWidget(left_group)
            header_layout.addWidget(right_group)
        else:
            # 完整模式：水平布局，左侧扩展，右侧固定
            header_layout.addWidget(left_group)
            header_layout.addStretch()  # 推动右侧按钮到最右边
            header_layout.addWidget(right_group)
        
        return header_widget
    
    def create_enhanced_button_group(self):
        """
        创建增强版按钮组合（启动+卸载）
        v1.2.4: 改进视觉连接、hover效果、动画过渡
        """
        # 按钮组合容器
        button_group = QFrame()
        button_group.setFrameStyle(QFrame.NoFrame)
        
        # 设置容器样式：统一的阴影和圆角
        button_group.setStyleSheet("""
            QFrame {
                background: transparent;
                border-radius: 10px;
            }
        """)
        
        # 布局
        button_layout = QHBoxLayout(button_group)
        button_layout.setSpacing(1)  # 极小间隙，营造分割线效果
        button_layout.setContentsMargins(0, 0, 0, 0)
        
        # 尺寸设置
        # v1.2.6 FIX: 稍微减小按钮高度，为时间统计留出空间
        if getattr(self, 'layout_mode', 'full') == "compact":
            button_height = 34  # 从36减少到34
            launch_width = 70
            uninstall_width = 30
        else:
            button_height = 38  # 从42减少到38
            launch_width = 90
            uninstall_width = 36
        
        # 启动按钮（主要功能）
        launch_btn = QPushButton(self.tr("🚀 Launch"))
        launch_btn.setFixedSize(launch_width, button_height)
        launch_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #10b981, stop:1 #059669);
                color: white;
                border: none;
                border-radius: 10px 0px 0px 10px;
                font-size: 13px;
                font-weight: bold;
                padding: 0px;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #34d399, stop:1 #10b981);
                transform: scale(1.02);
            }}
            QPushButton:pressed {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #047857, stop:1 #065f46);
            }}
        """)
        launch_btn.clicked.connect(lambda: self.launch_requested.emit(self.tool_data['name']))
        
        # 卸载按钮（辅助功能）
        uninstall_btn = QPushButton("🗑️")
        uninstall_btn.setFixedSize(uninstall_width, button_height)
        uninstall_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #ef4444, stop:1 #dc2626);
                color: white;
                border: none;
                border-radius: 0px 10px 10px 0px;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #f87171, stop:1 #ef4444);
                transform: scale(1.02);
            }}
            QPushButton:pressed {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #b91c1c, stop:1 #991b1b);
            }}
        """)
        uninstall_btn.setToolTip(self.tr("卸载工具"))
        uninstall_btn.clicked.connect(lambda: self.uninstall_requested.emit(self.tool_data['name']))
        
        # 添加组件
        button_layout.addWidget(launch_btn)
        button_layout.addWidget(uninstall_btn)
        
        # v1.2.6: 恢复按钮的轻微阴影（避免与容器冲突）
        try:
            from PyQt5.QtGui import QColor
            shadow = QGraphicsDropShadowEffect()
            shadow.setBlurRadius(4)
            shadow.setColor(QColor(0, 0, 0, 15))
            shadow.setOffset(0, 1)
            button_group.setGraphicsEffect(shadow)
        except ImportError:
            pass
        
        return button_group
    
    def create_enhanced_install_button(self):
        """
        创建增强版安装按钮
        v1.2.4: 渐变背景、hover动画、现代化设计
        """
        install_btn = QPushButton(self.tr("📥 Install Tool"))

        # 尺寸设置
        # v1.2.6 FIX: 与启动按钮保持一致的高度
        if getattr(self, 'layout_mode', 'full') == "compact":
            install_btn.setFixedSize(100, 34)  # 与启动按钮高度一致
        else:
            install_btn.setFixedSize(126, 38)  # 与启动按钮高度一致
        
        # 增强样式
        install_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #3b82f6, stop:1 #2563eb);
                color: white;
                border: none;
                border-radius: 10px;
                font-size: 13px;
                font-weight: bold;
                padding: 0px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #60a5fa, stop:1 #3b82f6);
                transform: scale(1.02);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #1d4ed8, stop:1 #1e40af);
            }
        """)
        
        install_btn.clicked.connect(lambda: self.install_requested.emit(self.tool_data['name']))
        
        # v1.2.6: 恢复安装按钮的轻微阴影
        try:
            from PyQt5.QtGui import QColor
            shadow = QGraphicsDropShadowEffect()
            shadow.setBlurRadius(4)
            shadow.setColor(QColor(0, 0, 0, 15))
            shadow.setOffset(0, 1)
            install_btn.setGraphicsEffect(shadow)
        except ImportError:
            pass
        
        return install_btn
    
    def setup_animations(self):
        """
        设置页面动画效果
        v1.2.4: 增强交互反馈
        """
        try:
            self.logger.debug("开始设置页面动画效果")
            
            # 🔧 临时禁用页面级透明度效果以修复QPainter冲突
            # 问题：页面级QGraphicsOpacityEffect与子组件的QGraphicsDropShadowEffect冲突
            # 导致QPainter错误：A paint device can only be painted by one painter at a time
            self.logger.debug("跳过透明度效果以避免渲染冲突")
            
            # TODO: 未来可以考虑以下替代方案：
            # 1. 使用CSS动画替代QPropertyAnimation
            # 2. 只在子组件上使用单一类型的GraphicsEffect
            # 3. 实现自定义淡入效果而不依赖QGraphicsOpacityEffect
            
            self.logger.debug("页面动画设置完成（已跳过冲突效果）")
            
        except ImportError as ie:
            self.logger.warning(f"动画导入失败，跳过动画设置: {str(ie)}")
        except Exception as e:
            self.logger.error(f"动画设置失败: {str(e)}", exc_info=True)
    
    def enterEvent(self, event):
        """鼠标进入页面事件"""
        super().enterEvent(event)
        # 可以在这里添加hover效果
        
    def leaveEvent(self, event):
        """鼠标离开页面事件"""
        super().leaveEvent(event)
        # 可以在这里添加hover效果恢复
        
    def create_stats_bar(self):
        """
        创建精简统计信息栏
        
        统计栏设计说明：
        ================
        🔥 v1.2.4 视觉增强更新：
        - 增加图标提升识别度
        - 渐变背景增强视觉层次
        - Hover效果提供交互反馈
        - 圆角阴影增强现代感
        
        根据可用宽度自动切换布局模式：
        - 完整模式(>700px)：4个卡片水平排列
        - 中等模式(500-700px)：2x2网格布局
        - 紧凑模式(<500px)：垂直堆叠
        
        当前统计项目：
        1. 安装状态 - 显示工具是否已安装（绿色=已安装，橙色=未安装）
        2. 磁盘占用 - 显示工具占用的磁盘空间
        3. 版本 - 显示当前安装的工具版本
        4. 使用时间 - 显示累计使用时间（重点功能，类似Steam游戏时间统计）
        """
        # 统计数据配置（4个核心信息，包含使用时间统计）
        # v1.2.4: 增强版配置，包含图标和渐变配色
        stats_data = [
            {
                "label": self.tr("安装状态"),
                "value": self.tr("已安装") if self.tool_data['status'] == 'installed' else self.tr("未安装"),
                "icon": "✅" if self.tool_data['status'] == 'installed' else "⏳",
                "color": "#10b981" if self.tool_data['status'] == 'installed' else "#f59e0b",
                "gradient": "qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #10b981, stop:1 #059669)" if self.tool_data['status'] == 'installed' else "qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #f59e0b, stop:1 #d97706)"
            },
            {
                "label": self.tr("磁盘占用"),
                "value": self.tool_data.get('disk_usage', 'N/A'),
                "icon": "💾",
                "color": "#475569",
                "gradient": "qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #64748b, stop:1 #475569)"
            },
            {
                "label": self.tr("版本"),
                "value": self.tool_data.get('version', 'N/A'),
                "icon": "🏷️",
                "color": "#2563eb",
                "gradient": "qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #3b82f6, stop:1 #2563eb)"
            },
            {
                "label": self.tr("使用时间"),
                "value": self._get_usage_time_display(),
                "icon": "⏱️",
                "color": "#059669",
                "gradient": "qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #10b981, stop:1 #047857)"
            }
        ]
        
        # 🔥 NEW: 使用增强版自适应统计栏组件
        stats_bar = EnhancedAdaptiveStatsBar()
        stats_bar.setMinimumHeight(90)  # 为图标和新效果留更多空间
        
        # 创建增强版统计卡片
        for data in stats_data:
            card = self.create_enhanced_stat_card(data)
            stats_bar.add_stat_card(card)
        
        # 调试信息
        if __debug__:
            print(f"📊 统计栏使用增强版设计，布局模式: {getattr(self, 'layout_mode', 'auto')}")
        
        return stats_bar
    
    def create_enhanced_stat_card(self, data):
        """
        创建增强版统计卡片
        v1.2.4: 包含图标、渐变背景、hover效果
        """
        card = QFrame()
        card.setFrameStyle(QFrame.StyledPanel)
        
        # 创建布局
        layout = QVBoxLayout(card)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(5)
        
        # 顶部：图标和标签行
        top_layout = QHBoxLayout()
        top_layout.setContentsMargins(0, 0, 0, 0)
        
        # 图标
        icon_label = QLabel(data.get('icon', '📊'))
        icon_label.setStyleSheet("""
            font-size: 16px;
            margin-right: 6px;
        """)
        top_layout.addWidget(icon_label)
        
        # 标签
        label_widget = QLabel(data['label'])
        label_widget.setStyleSheet("""
            font-size: 12px;
            color: rgba(255, 255, 255, 0.9);
            font-weight: 500;
        """)
        top_layout.addWidget(label_widget)
        top_layout.addStretch()
        
        layout.addLayout(top_layout)
        
        # 数值
        value_widget = QLabel(str(data['value']))
        value_widget.setStyleSheet("""
            font-size: 18px;
            color: white;
            font-weight: bold;
            margin-top: 2px;
        """)
        layout.addWidget(value_widget)
        
        # 设置卡片样式：渐变背景、圆角、阴影、hover效果
        card.setStyleSheet(f"""
            QFrame {{
                background: {data.get('gradient', 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)')};
                border-radius: 12px;
                border: none;
                min-width: 120px;
                min-height: 70px;
                transition: all 0.3s ease;
            }}
            QFrame:hover {{
                background: {self._create_hover_gradient(data.get('gradient', ''))};
                border: 2px solid rgba(255, 255, 255, 0.3);
            }}
        """)
        
        # 阴影效果和动画
        try:
            from PyQt5.QtGui import QColor
            shadow = QGraphicsDropShadowEffect()
            shadow.setBlurRadius(8)
            shadow.setColor(QColor(0, 0, 0, 60))
            shadow.setOffset(0, 2)
            card.setGraphicsEffect(shadow)
            
            # 添加hover动画效果
            animator = StatCardAnimator(card, shadow)
            card.installEventFilter(animator)
            # 保持对动画器的引用，避免被垃圾回收
            card._animator = animator
            
        except ImportError:
            pass  # 如果不支持阴影效果则跳过
        
        return card
    
    def _create_hover_gradient(self, original_gradient):
        """创建hover状态的渐变色（更亮）"""
        if 'stop:0 #10b981' in original_gradient:
            return "qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #34d399, stop:1 #10b981)"
        elif 'stop:0 #f59e0b' in original_gradient:
            return "qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #fbbf24, stop:1 #f59e0b)"
        elif 'stop:0 #64748b' in original_gradient:
            return "qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #94a3b8, stop:1 #64748b)"
        elif 'stop:0 #3b82f6' in original_gradient:
            return "qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #60a5fa, stop:1 #3b82f6)"
        else:
            return original_gradient
    
    def _get_category_display(self):
        """
        获取工具分类的显示名称
        将内部分类代码转换为用户友好的显示名称
        """
        category_map = {
            "quality": self.tr("质量控制"),
            "sequence": self.tr("序列分析"),
            "rnaseq": self.tr("RNA测序"),
            "genomics": self.tr("基因组学"),
            "phylogeny": self.tr("系统发育"),
            "alignment": self.tr("序列比对"),
            "assembly": self.tr("基因组组装"),
            "annotation": self.tr("基因注释"),
            "visualization": self.tr("数据可视化"),
            "statistics": self.tr("统计分析")
        }

        category_code = self.tool_data.get('category', 'unknown')
        return category_map.get(category_code, self.tr('未知分类'))
    
    def _get_tech_specs(self):
        """获取当前工具的技术规格数据"""
        tool_specs = {
            "FastQC": [
                (self.tr("编程语言"), "Java"),
                (self.tr("依赖环境"), "Java 8+"),
                (self.tr("输入格式"), "FASTQ, SAM, BAM"),
                (self.tr("输出格式"), "HTML, ZIP"),
                (self.tr("CPU要求"), self.tr("单核即可")),
                (self.tr("内存要求"), self.tr("最小2GB")),
                (self.tr("存储占用"), "85MB"),
                (self.tr("源代码"), "github.com/s-andrews/FastQC")
            ],
            "BLAST": [
                (self.tr("编程语言"), "C++"),
                (self.tr("依赖环境"), self.tr("标准C++库")),
                (self.tr("输入格式"), "FASTA"),
                (self.tr("输出格式"), self.tr("多种格式")),
                (self.tr("CPU要求"), self.tr("多核推荐")),
                (self.tr("内存要求"), self.tr("取决于数据库大小")),
                (self.tr("存储占用"), "245MB"),
                (self.tr("源代码"), "ncbi.nlm.nih.gov/blast")
            ],
            "BWA": [
                (self.tr("编程语言"), "C"),
                (self.tr("依赖环境"), self.tr("标准C库")),
                (self.tr("输入格式"), "FASTA, FASTQ"),
                (self.tr("输出格式"), "SAM"),
                (self.tr("CPU要求"), self.tr("多核强烈推荐")),
                (self.tr("内存要求"), self.tr("取决于参考基因组大小")),
                (self.tr("存储占用"), "15MB"),
                (self.tr("源代码"), "github.com/lh3/bwa")
            ],
            "SAMtools": [
                (self.tr("编程语言"), "C"),
                (self.tr("依赖环境"), self.tr("标准C库, zlib")),
                (self.tr("输入格式"), "SAM, BAM, CRAM"),
                (self.tr("输出格式"), "SAM, BAM, CRAM"),
                (self.tr("CPU要求"), self.tr("多核推荐")),
                (self.tr("内存要求"), self.tr("最小4GB")),
                (self.tr("存储占用"), "32MB"),
                (self.tr("源代码"), "github.com/samtools/samtools")
            ],
            "HISAT2": [
                (self.tr("编程语言"), "C++"),
                (self.tr("依赖环境"), self.tr("标准C++库")),
                (self.tr("输入格式"), "FASTA, FASTQ"),
                (self.tr("输出格式"), "SAM"),
                (self.tr("CPU要求"), self.tr("多核强烈推荐")),
                (self.tr("内存要求"), self.tr("最小8GB")),
                (self.tr("存储占用"), "128MB"),
                (self.tr("源代码"), "github.com/DaehwanKimLab/hisat2")
            ],
            "IQ-TREE": [
                (self.tr("编程语言"), "C++"),
                (self.tr("依赖环境"), self.tr("标准C++库")),
                (self.tr("输入格式"), "Phylip, Nexus, FASTA"),
                (self.tr("输出格式"), "Newick, PDF"),
                (self.tr("CPU要求"), self.tr("多核强烈推荐")),
                (self.tr("内存要求"), self.tr("取决于序列数量")),
                (self.tr("存储占用"), "78MB"),
                (self.tr("源代码"), "github.com/iqtree/iqtree2")
            ]
        }
        
        default_specs = [
            (self.tr("编程语言"), self.tr("暂无信息")),
            (self.tr("依赖环境"), self.tr("暂无信息")),
            (self.tr("输入格式"), self.tr("暂无信息")),
            (self.tr("输出格式"), self.tr("暂无信息")),
            (self.tr("CPU要求"), self.tr("多核推荐")),
            (self.tr("内存要求"), self.tr("最小4GB")),
            (self.tr("存储占用"), self.tr("未知"))
        ]
        
        return tool_specs.get(self.tool_data['name'], default_specs)
    
    def _get_usage_time_display(self):
        """获取工具使用时间的显示文本（使用智能格式化）"""
        # 使用真实的使用时间数据
        total_runtime = self.tool_data.get('total_runtime', 0)

        if total_runtime == 0:
            return self.tr("暂未使用")

        # 使用智能时间格式化：
        # < 60秒: 显示秒
        # 60-7199秒 (1-120分钟): 显示分钟
        # >= 7200秒 (120分钟+): 显示小时
        from utils.time_formatter import format_runtime
        return format_runtime(total_runtime, language='zh_CN')


    def create_description_section(self):
        """创建工具详细介绍区域 - 使用AutoResizingTextEdit实现高度自适应"""
        section_widget = QWidget()
        section_widget.setStyleSheet("""
            QWidget {
                background: #FFFFFF;
                border-radius: 12px;
            }
        """)
        
        # v1.2.5: 添加淡阴影效果
        try:
            from PyQt5.QtGui import QColor
            shadow = QGraphicsDropShadowEffect()
            shadow.setBlurRadius(10)
            shadow.setColor(QColor(0, 0, 0, 30))
            shadow.setOffset(0, 2)
            section_widget.setGraphicsEffect(shadow)
        except ImportError:
            pass
        
        layout = QVBoxLayout(section_widget)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)
        
        # 标题 - 🔥 使用SmartPaintLabel V2，完全兼容原有样式！
        title_label = create_smart_label_v2(self.tr("工具介绍"))

        # 🎯 关键：2025优化字体大小
        title_font = QFont()
        title_font.setPointSize(14)  # 16px → 14px
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #0f172a; margin-bottom: 10px;")
        
        # 🔥 NEW: 使用AutoResizingTextEdit，字体固定，高度自适应！
        description = AutoResizingTextEdit()
        description.setPlainText(self.tool_data.get('description', self.tr('暂无详细介绍，日后增添')))
        description.setReadOnly(True)
        description.setMinimumLines(3)  # 最少显示3行
        
        # v1.2.6: 更紧凑的字体设置
        desc_font = QFont()
        desc_font.setPointSize(11)  # 更紧凑的字体
        description.setFont(desc_font)
        
        # 设置样式
        description.setStyleSheet("""
            QTextEdit {
                border: none;
                border-radius: 8px;
                padding: 12px;
                color: #374151;
                background: rgba(248, 250, 252, 0.8);
                line-height: 1.5;
                font-weight: 400;
            }
        """)
        
        # ⚠️ 已删除主要功能板块 - 根据用户要求移除重复信息
        
        layout.addWidget(title_label)
        layout.addWidget(description)
        
        return section_widget
        
    def create_tech_specs_section(self):
        """
        创建技术规格区域
        
        技术规格设计说明：
        ==================
        用户明确要求将技术规格直接显示在页面中，而不是作为Tab的二级菜单。
        采用标签-数值对的形式显示，格式如："编程语言: Java"
        
        显示内容包括：
        1. 编程语言 - 工具使用的主要编程语言
        2. 依赖环境 - 运行所需的环境或库  
        3. 输入格式 - 支持的输入文件格式
        4. 输出格式 - 生成的输出文件格式
        5. CPU要求 - 处理器要求说明
        6. 内存要求 - 内存使用建议
        
        设计特点：
        - 白色背景，8px圆角边框，与其他区域保持一致的视觉风格
        - 垂直布局，每个规格占一行，清晰易读
        - 30px左右内边距，25px上下内边距，提供舒适的阅读空间
        - 16px行间距确保足够的视觉分离
        - 🔧 图标提供直观的技术属性指示
        
        数据来源：
        - 通过 _get_tech_specs() 方法获取特定工具的技术规格
        - 支持每个工具的个性化规格信息
        - 如果工具未定义规格，则显示默认的通用规格
        
        未来扩展计划：
        - 支持更多技术参数（GPU支持、网络要求、特殊硬件需求等）
        - 添加规格说明的工具提示（hover显示详细解释）
        - 实现系统规格的动态检测和兼容性验证
        - 添加规格不满足时的警告提示
        - 支持规格的本地化显示（中英文切换）
        """
        section_widget = QWidget()
        section_widget.setStyleSheet("""
            QWidget {
                background: #FFFFFF;
                border-radius: 12px;
            }
        """)
        
        # v1.2.5: 添加淡阴影效果
        try:
            from PyQt5.QtGui import QColor
            shadow = QGraphicsDropShadowEffect()
            shadow.setBlurRadius(10)
            shadow.setColor(QColor(0, 0, 0, 30))
            shadow.setOffset(0, 2)
            section_widget.setGraphicsEffect(shadow)
        except ImportError:
            pass
        
        layout = QVBoxLayout(section_widget)
        layout.setContentsMargins(20, 16, 20, 16)  # 更紧凑的内边距
        layout.setSpacing(8)  # 更紧凑的行间距
        
        # 技术规格标题 - 🔥 使用SmartPaintLabel V2，完全兼容原有样式！
        title_label = create_smart_label_v2(self.tr("🔧 技术规格"))

        # 🎯 关键：2025优化字体大小
        title_font = QFont()
        title_font.setPointSize(14)  # 16px → 14px
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #0f172a; margin-bottom: 10px;")
        layout.addWidget(title_label)  # 标题放在最前面
        
        # 获取当前工具的技术规格数据
        # 每个工具都有特定的技术规格，如果未定义则使用默认值
        specs_data = self._get_tech_specs()
        
        # 逐行创建规格显示
        # 使用统一的 create_spec_row 方法确保视觉一致性
        for spec_label, spec_value in specs_data:
            spec_row = self.create_spec_row(spec_label, spec_value)
            layout.addWidget(spec_row)
        
        return section_widget
        
    def create_spec_row(self, label: str, value: str):
        """
        创建技术规格行
        
        规格行设计说明：
        ================
        每一行技术规格都采用统一的标签-值对格式，确保视觉一致性。
        用户要求的格式："编程语言： Java"（使用中文冒号），即标签后加中文冒号，然后是对应的值。
        
        布局设计：
        - 水平布局，标签在左，值在右，左对齐
        - 标签固定宽度80px，确保所有行的对齐一致（比100px更紧凑）
        - 8px的左边距分离标签和值（比12px更紧凑）
        - 右侧留白避免内容过度拉伸
        - 支持值内容的自动换行（适应长文本）
        
        样式设计：
        - 标签：中等灰色(#64748b)，13px字体，500字重，次要但清晰
        - 值：深灰色(#475569)，13px字体，正常字重，主要内容
        - 标签左对齐，保持整齐的视觉效果
        - 无边距和内边距，保持紧凑布局
        
        参数说明：
        @param label: 规格标签，如"编程语言"、"依赖环境"等
        @param value: 规格值，如"Java"、"Python 3.6+"等，支持长文本自动换行
        @return: 配置好的行控件，可直接添加到父布局中
        
        实现特点：
        - 使用中文全角冒号"：" 符合中文排版习惯
        - 固定宽度避免因标签长度不同导致的不对齐
        - WordWrap支持长值内容的换行显示
        - 左对齐确保多行内容的视觉一致性
        
        未来优化：
        - 支持交互式内容（如版本号点击显示更新选项）
        - 添加hover效果显示详细说明或帮助信息
        - 支持规格验证状态显示（如依赖是否已满足）
        """
        row_widget = QWidget()
        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(0, 0, 0, 0)  # 无边距，紧凑布局
        row_layout.setSpacing(0)  # 手动控制间距
        
        # 规格标签，根据布局模式调整宽度
        label_widget = QLabel(f"{label}:")
        
        # v1.2.6: 更紧凑的标签宽度设置
        if hasattr(self, 'layout_mode'):
            if self.layout_mode == "compact":
                label_widget.setMinimumWidth(55)  
                label_widget.setMaximumWidth(70)
            elif self.layout_mode == "medium":
                label_widget.setFixedWidth(65)    
            else:
                label_widget.setFixedWidth(70)    # 更紧凑的标签宽度
        else:
            label_widget.setFixedWidth(70)  
        label_widget.setStyleSheet("""
            font-size: 12px;         
            color: #4B5563;          /* 更中性的灰色 */
            font-weight: 600;        
            padding-right: 4px;      /* 与值的间距 */
        """)
        label_widget.setAlignment(Qt.AlignLeft)  # 左对齐，保持整齐
        
        # 🔥 特殊处理：如果是源代码链接，使用QTextBrowser支持点击
        if label == "源代码" and ("github.com" in value or "ncbi.nlm.nih.gov" in value or "http" in value):
            # 使用QTextBrowser处理链接
            value_widget = QTextBrowser()
            html_link = f'<a href="https://{value}" style="color: #2563eb; text-decoration: none;">{value}</a>'
            value_widget.setHtml(html_link)
            value_widget.setOpenExternalLinks(True)  # QTextBrowser支持此方法
            value_widget.setMaximumHeight(25)  # 限制高度，类似单行
        else:
            # 普通文本使用AutoResizingTextEdit
            value_widget = AutoResizingTextEdit()
            value_widget.setPlainText(value)
            value_widget.setMinimumLines(1)
            
        value_widget.setReadOnly(True)
        value_widget.setStyleSheet("""
            QTextEdit, QTextBrowser {
                font-size: 12px;         
                color: #374151;          /* 更中性的主文本颜色 */
                margin-left: 6px;        /* 更紧凑的间距 */
                border: none;            
                background-color: transparent; 
                padding: 0px;            
                font-weight: 400;        /* 正常字重，更干净 */
                line-height: 1.4;        /* 紧凑的行高 */
            }
            QTextBrowser a {
                color: #3B82F6;          /* 现代蓝色 */
                text-decoration: none;   
                font-weight: 500;        
            }
            QTextBrowser a:hover {
                color: #1D4ED8;          
                text-decoration: underline; 
            }
        """)
        
        # 组装布局：标签 + 值 + 右侧留白
        row_layout.addWidget(label_widget)
        row_layout.addWidget(value_widget)
        row_layout.addStretch()  # 右侧留白，避免内容拉伸
        
        return row_widget


class StatCardAnimator(QObject):
    """统计卡片动画器，提供hover效果"""
    
    def __init__(self, card_widget, shadow_effect):
        super().__init__()
        self.card = card_widget
        self.shadow = shadow_effect
        self.original_blur = shadow_effect.blurRadius() if shadow_effect else 8
        
    def eventFilter(self, obj, event):
        if obj == self.card:
            if event.type() == QEvent.Enter:
                # 鼠标进入：增强阴影
                if self.shadow:
                    self.shadow.setBlurRadius(12)
                    self.shadow.setOffset(0, 4)
                return True
            elif event.type() == QEvent.Leave:
                # 鼠标离开：恢复原始阴影
                if self.shadow:
                    self.shadow.setBlurRadius(self.original_blur)
                    self.shadow.setOffset(0, 2)
                return True
        return super().eventFilter(obj, event)


class EnhancedAdaptiveStatsBar(QWidget):
    """
    增强版自适应统计栏
    v1.2.4: 基于AdaptiveStatsBar扩展，增加现代化视觉效果
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 使用水平布局，支持自动换行
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 5, 0, 5)
        self.layout.setSpacing(15)
        
        # 存储卡片引用
        self.stat_cards = []
        
        # 设置尺寸策略
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.MinimumExpanding)
    
    def add_stat_card(self, card):
        """添加统计卡片"""
        self.stat_cards.append(card)
        self.layout.addWidget(card)
        
        # 设置卡片的尺寸策略
        card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
    
    def clear_cards(self):
        """清空所有卡片"""
        for card in self.stat_cards:
            card.deleteLater()
        self.stat_cards.clear()
        
    def resizeEvent(self, event):
        """响应窗口大小变化，自动调整布局"""
        super().resizeEvent(event)
        
        # 计算可用宽度
        available_width = self.width()
        card_min_width = 120
        spacing = 15
        
        # 根据宽度调整卡片排列
        if len(self.stat_cards) > 0:
            total_min_width = len(self.stat_cards) * card_min_width + (len(self.stat_cards) - 1) * spacing
            
            if available_width < total_min_width:
                # 空间不足时使用网格布局
                self._arrange_as_grid()
            else:
                # 空间充足时使用水平布局
                self._arrange_horizontal()
    
    def _arrange_horizontal(self):
        """水平排列卡片"""
        for card in self.stat_cards:
            card.setMaximumWidth(16777215)  # 移除最大宽度限制
    
    def _arrange_as_grid(self):
        """网格排列卡片（2x2）"""
        for card in self.stat_cards:
            card.setMaximumWidth(200)  # 限制卡片宽度


# 如果你需要修改此文件的布局或添加新功能，请务必遵循以下原则：
# 
# 1. 🔥 永远不要移除 ResponsiveDetailPageManager 的使用
#    这是防止内容截断的核心组件
# 
# 2. 🔥 所有长文本显示都应该使用 AutoResizingTextEdit
#    不要使用普通的 QTextEdit 或 QLabel (因文本截断问题)
# 
# 3. 🔥 不要手动设置固定宽度（setFixedWidth）
#    这会破坏响应式布局
# 
# 4. 🔥 新增的滚动区域必须设置：
#    - setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
#    - setWidgetResizable(True)
#    - setSizePolicy(QSizePolicy.Expanding, QSizePolicy.MinimumExpanding)
# 
# 5. 🔥 测试新功能时，请确保在不同窗口尺寸下都能正确显示：
#    - 最小窗口（800x600）
#    - 中等窗口（1200x800）
#    - 大窗口（1920x1080）
#    - 特别注意小窗口下不应该出现水平滚动条
# 
# 6. 🔥 如果遇到布局问题，请参考：
#    - ui/responsive_layout.py 中的详细说明
#    - BioNexus 1.1.6 的 adaptive_layout.py 实现
# 
# 历史教训记录：
# - 2023年在1.1.7开发中误删了关键响应式配置
# - 导致小窗口下内容被左右截断
# - 花费大量时间才发现和修复问题
# 
# 请帮助我们避免重复同样的错误！
# ===========================================
