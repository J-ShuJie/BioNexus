"""
现代化工具卡片组件 V3
=====================================
尺寸：170×113px
特性：圆角边框、收藏按钮、文本截断、优化布局
使用paintEvent实现精确渲染
"""

from PyQt5.QtWidgets import QWidget, QPushButton, QGraphicsDropShadowEffect
from PyQt5.QtCore import Qt, pyqtSignal, QRect, QRectF, QPointF
from PyQt5.QtGui import (
    QPainter, QColor, QFont, QFontMetrics, QPen, QBrush, 
    QPainterPath, QLinearGradient
)


class ToolCardV3(QWidget):
    """
    现代化工具卡片组件 V3
    精确控制布局和渲染
    """
    
    # 信号定义 - 保持向后兼容
    clicked = pyqtSignal(dict)  # 点击信号，传递工具数据
    install_clicked = pyqtSignal(str)
    launch_clicked = pyqtSignal(str)
    favorite_toggled = pyqtSignal(str, bool)  # 新增：收藏信号
    
    # 布局常量
    CARD_WIDTH = 170
    CARD_HEIGHT = 113
    BORDER_RADIUS = 8
    PADDING = 10
    TITLE_HEIGHT = 24
    DESC_HEIGHT = 45  # 调整为45px，确保3行文本完整显示
    BUTTON_HEIGHT = 24
    BUTTON_WIDTH = 60
    
    def __init__(self, tool_data: dict, parent=None):
        super().__init__(parent)
        self.tool_data = tool_data
        self.is_selected = False
        self.is_hovered = False
        self.is_favorite = tool_data.get('is_favorite', False)
        
        # 设置固定大小
        self.setFixedSize(self.CARD_WIDTH, self.CARD_HEIGHT)
        self.setCursor(Qt.PointingHandCursor)
        self.setMouseTracking(True)
        
        # 初始化按钮
        self._init_buttons()

        # 设置阴影效果
        self._setup_shadow()

        # Connect to language change signal
        self._connect_language_change()
        
    def _init_buttons(self):
        """初始化底部按钮"""
        button_y = self.CARD_HEIGHT - self.BUTTON_HEIGHT - 8
        button_spacing = 5
        total_width = self.CARD_WIDTH - 2 * self.PADDING
        button_width = (total_width - button_spacing) // 2
        
        if self.tool_data['status'] == 'installed':
            # 已安装：启动按钮 + 详情按钮
            self.launch_btn = QPushButton(self.tr("Launch"), self)
            self.launch_btn.setGeometry(
                self.PADDING, button_y, button_width, self.BUTTON_HEIGHT
            )
            self.launch_btn.clicked.connect(
                lambda: self.launch_clicked.emit(self.tool_data['name'])
            )
            self._style_button(self.launch_btn, "primary")

            self.detail_btn = QPushButton(self.tr("Details"), self)
            self.detail_btn.setGeometry(
                self.PADDING + button_width + button_spacing,
                button_y, button_width, self.BUTTON_HEIGHT
            )
            self.detail_btn.clicked.connect(self._on_detail_clicked)
            self._style_button(self.detail_btn, "secondary")
        else:
            # 未安装：安装按钮 + 详情按钮
            self.install_btn = QPushButton(self.tr("Install"), self)
            self.install_btn.setGeometry(
                self.PADDING, button_y, button_width, self.BUTTON_HEIGHT
            )
            self.install_btn.clicked.connect(
                lambda: self.install_clicked.emit(self.tool_data['name'])
            )
            self._style_button(self.install_btn, "success")

            self.detail_btn = QPushButton(self.tr("Details"), self)
            self.detail_btn.setGeometry(
                self.PADDING + button_width + button_spacing,
                button_y, button_width, self.BUTTON_HEIGHT
            )
            self.detail_btn.clicked.connect(self._on_detail_clicked)
            self._style_button(self.detail_btn, "secondary")
    
    def _style_button(self, button, style_type):
        """设置按钮样式"""
        styles = {
            "primary": """
                QPushButton {
                    background-color: #3b82f6;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    font-size: 11px;
                    font-weight: 500;
                }
                QPushButton:hover {
                    background-color: #2563eb;
                }
                QPushButton:pressed {
                    background-color: #1d4ed8;
                }
                QPushButton:disabled {
                    background-color: #94a3b8;
                }
            """,
            "success": """
                QPushButton {
                    background-color: #10b981;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    font-size: 11px;
                    font-weight: 500;
                }
                QPushButton:hover {
                    background-color: #059669;
                }
                QPushButton:pressed {
                    background-color: #047857;
                }
                QPushButton:disabled {
                    background-color: #94a3b8;
                }
            """,
            "secondary": """
                QPushButton {
                    background-color: #f3f4f6;
                    color: #374151;
                    border: 1px solid #d1d5db;
                    border-radius: 4px;
                    font-size: 11px;
                    font-weight: 500;
                }
                QPushButton:hover {
                    background-color: #e5e7eb;
                    border-color: #9ca3af;
                }
                QPushButton:pressed {
                    background-color: #d1d5db;
                }
            """
        }
        button.setStyleSheet(styles.get(style_type, styles["secondary"]))
    
    def _setup_shadow(self):
        """设置阴影效果"""
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(10)
        shadow.setColor(QColor(0, 0, 0, 25))
        shadow.setOffset(0, 2)
        self.setGraphicsEffect(shadow)
    
    def paintEvent(self, event):
        """绘制卡片内容"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 1. 绘制背景和边框
        self._draw_background(painter)
        
        # 2. 绘制标题和收藏按钮
        self._draw_title_bar(painter)
        
        # 3. 绘制描述文本
        self._draw_description(painter)
        
        # 4. 绘制状态指示器
        self._draw_status_indicator(painter)
    
    def _draw_background(self, painter):
        """绘制背景和边框"""
        # 创建圆角矩形路径
        path = QPainterPath()
        rect = QRectF(0.5, 0.5, self.width() - 1, self.height() - 1)
        path.addRoundedRect(rect, self.BORDER_RADIUS, self.BORDER_RADIUS)
        
        # 填充背景
        if self.is_selected:
            painter.fillPath(path, QColor("#eff6ff"))
        elif self.is_hovered:
            painter.fillPath(path, QColor("#f8fafc"))
        else:
            painter.fillPath(path, QColor("#ffffff"))
        
        # 绘制边框
        pen = QPen()
        if self.is_selected:
            pen.setColor(QColor("#3b82f6"))
            pen.setWidth(2)
        elif self.is_hovered:
            pen.setColor(QColor("#94a3b8"))
            pen.setWidth(1)
        else:
            pen.setColor(QColor("#e5e7eb"))
            pen.setWidth(1)
        
        painter.setPen(pen)
        painter.drawPath(path)
    
    def _draw_title_bar(self, painter):
        """绘制标题栏（包含工具名和收藏按钮）"""
        # 标题字体
        title_font = QFont()
        title_font.setPointSize(11)
        title_font.setBold(True)
        painter.setFont(title_font)
        
        # 标题文本区域（留出收藏按钮空间）
        title_rect = QRect(
            self.PADDING, 
            8,
            self.width() - 2 * self.PADDING - 24,  # 减去收藏按钮宽度
            self.TITLE_HEIGHT
        )
        
        # 绘制标题（带省略号）
        painter.setPen(QColor("#1f2937"))
        title = self.tool_data['name']
        metrics = QFontMetrics(title_font)
        elided_title = metrics.elidedText(
            title, Qt.ElideRight, title_rect.width()
        )
        painter.drawText(title_rect, Qt.AlignLeft | Qt.AlignVCenter, elided_title)
        
        # 绘制收藏按钮
        star_rect = QRect(
            self.width() - self.PADDING - 20,
            10,
            20,
            20
        )
        
        # 收藏星星
        star_font = QFont()
        star_font.setPointSize(14)
        painter.setFont(star_font)
        
        if self.is_favorite:
            painter.setPen(QColor("#fbbf24"))  # 金黄色
            painter.drawText(star_rect, Qt.AlignCenter, "★")
        else:
            painter.setPen(QColor("#9ca3af"))  # 灰色
            painter.drawText(star_rect, Qt.AlignCenter, "☆")
        
        # 保存收藏按钮区域用于点击检测
        self.favorite_rect = star_rect
    
    def _draw_description(self, painter):
        """绘制描述文本（多行，带省略号）"""
        desc_font = QFont()
        desc_font.setPointSize(9)
        painter.setFont(desc_font)
        painter.setPen(QColor("#6b7280"))
        
        # 描述文本区域 - 修正起始位置
        desc_start_y = 8 + self.TITLE_HEIGHT  # 32px
        desc_rect = QRect(
            self.PADDING,
            desc_start_y,
            self.width() - 2 * self.PADDING,
            self.DESC_HEIGHT
        )
        
        try:
            from utils.tool_localization import get_localized_tool_description
            description = get_localized_tool_description(self.tool_data)
        except Exception:
            description = ''
        if not description:
            description = self.tr('No detailed description')
            
        metrics = QFontMetrics(desc_font)
        
        # 使用文本高度而非行间距，避免过大的行距
        line_height = metrics.height() + 2  # 文本高度 + 2px行间距
        max_lines = 3  # 固定显示3行
        
        print(f"[调试] 文本渲染参数 - font_size: 9px, line_height: {line_height}, desc_height: {self.DESC_HEIGHT}")
        print(f"[调试] desc_rect: x={desc_rect.x()}, y={desc_rect.y()}, w={desc_rect.width()}, h={desc_rect.height()}")
        
        # 分词并构建行
        words = description.split()
        lines = []
        current_line = ""
        remaining_words = False
        
        for i, word in enumerate(words):
            test_line = current_line + " " + word if current_line else word
            if metrics.horizontalAdvance(test_line) <= desc_rect.width():
                current_line = test_line
            else:
                if current_line and len(lines) < max_lines:
                    lines.append(current_line)
                current_line = word
                
                # 如果已经有了最大行数，标记还有剩余文本
                if len(lines) >= max_lines:
                    remaining_words = True
                    break
        
        # 添加最后一行（如果还有空间）
        if current_line and len(lines) < max_lines:
            # 检查是否还有未处理的词
            if remaining_words or (len(lines) == max_lines - 1 and 
                                  len(' '.join(words)) > len(' '.join(lines + [current_line]).split())):
                # 需要添加省略号
                while metrics.horizontalAdvance(current_line + "...") > desc_rect.width() and len(current_line) > 0:
                    # 逐字符减少直到能容纳省略号
                    current_line = current_line.rsplit(' ', 1)[0] if ' ' in current_line else current_line[:-1]
                current_line = current_line + "..." if current_line else "..."
            lines.append(current_line)
        
        # 如果最后一行满了但还有文本，添加省略号
        elif len(lines) == max_lines and remaining_words:
            last_line = lines[-1]
            # 确保能容纳省略号
            while metrics.horizontalAdvance(last_line + "...") > desc_rect.width() and len(last_line) > 0:
                # 移除最后一个词或字符
                last_line = last_line.rsplit(' ', 1)[0] if ' ' in last_line else last_line[:-1]
            lines[-1] = last_line + "..." if last_line else "..."
        
        # 设置裁剪区域，确保文本不会超出边界
        painter.setClipRect(desc_rect)
        
        # 绘制每一行，确保在desc_rect范围内
        current_y = desc_start_y
        for i, line in enumerate(lines):
            if i >= max_lines:  # 确保不超过最大行数
                print(f"[调试] 达到最大行数限制: {i}")
                break
                
            # 确保不超出描述区域底部
            if current_y + line_height > desc_start_y + self.DESC_HEIGHT:
                print(f"[调试] 文本超出边界，停止绘制。current_y: {current_y}, max_y: {desc_start_y + self.DESC_HEIGHT}")
                break
                
            line_rect = QRect(
                self.PADDING,
                current_y,
                desc_rect.width(),
                line_height
            )
            
            print(f"[调试] 绘制第{i+1}行: '{line}' at y={current_y}")
            painter.drawText(line_rect, Qt.AlignLeft | Qt.AlignTop, line)
            current_y += line_height
        
        # 重置裁剪区域
        painter.setClipRect(self.rect())
        
        print(f"[调试] 文本绘制完成，共绘制 {min(len(lines), max_lines)} 行")
    
    def _draw_status_indicator(self, painter):
        """绘制状态指示器"""
        if self.tool_data['status'] == 'installed':
            # 已安装 - 绿色勾
            painter.setPen(QColor("#10b981"))
            painter.setFont(QFont("", 12))
            painter.drawText(
                QRect(self.PADDING, self.height() - 32, 20, 20),
                Qt.AlignCenter,
                "✓"
            )
            
            # 显示占用空间（如果有）
            if 'disk_usage' in self.tool_data:
                painter.setPen(QColor("#6b7280"))
                painter.setFont(QFont("", 8))
                painter.drawText(
                    QRect(self.PADDING + 25, self.height() - 32, 60, 20),
                    Qt.AlignLeft | Qt.AlignVCenter,
                    f"{self.tool_data['disk_usage']}"
                )
        else:
            # 未安装 - 灰色下载图标
            painter.setPen(QColor("#9ca3af"))
            painter.setFont(QFont("", 12))
            painter.drawText(
                QRect(self.PADDING, self.height() - 32, 20, 20),
                Qt.AlignCenter,
                "↓"
            )
    
    def mousePressEvent(self, event):
        """鼠标点击事件"""
        if event.button() == Qt.LeftButton:
            # 检查是否点击了收藏按钮
            if hasattr(self, 'favorite_rect') and self.favorite_rect.contains(event.pos()):
                self.is_favorite = not self.is_favorite
                self.favorite_toggled.emit(self.tool_data['name'], self.is_favorite)
                self.update()
            else:
                # 点击其他区域，发出卡片点击信号
                self.clicked.emit(self.tool_data)
        super().mousePressEvent(event)
    
    def mouseReleaseEvent(self, event):
        """鼠标释放事件"""
        super().mouseReleaseEvent(event)
    
    def enterEvent(self, event):
        """鼠标进入事件"""
        self.is_hovered = True
        self.update()
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        """鼠标离开事件"""
        self.is_hovered = False
        self.update()
        super().leaveEvent(event)
    
    def _on_detail_clicked(self):
        """详情按钮点击处理"""
        self.clicked.emit(self.tool_data)
    
    def set_selected(self, selected: bool):
        """设置选中状态 - 保持兼容性"""
        self.is_selected = selected
        self.update()
    
    def set_installing_state(self, is_installing: bool, progress: int = -1, status_text: str = ""):
        """设置安装状态 - 保持兼容性"""
        if hasattr(self, 'install_btn'):
            if is_installing:
                if progress >= 0:
                    self.install_btn.setText(self.tr("{0}%").format(progress))
                elif status_text:
                    display_text = status_text[:6] if len(status_text) > 6 else status_text
                    self.install_btn.setText(display_text)
                else:
                    self.install_btn.setText("...")
                self.install_btn.setEnabled(False)
            else:
                self.install_btn.setText(self.tr("Install"))
                self.install_btn.setEnabled(True)
    
    def set_favorite(self, is_favorite: bool):
        """设置收藏状态"""
        self.is_favorite = is_favorite
        self.update()

    def _connect_language_change(self):
        """Connect to language change signal"""
        try:
            from utils.translator import get_translator
            translator = get_translator()
            translator.languageChanged.connect(self.retranslateUi)
        except Exception as e:
            print(f"Warning: Could not connect language change signal in ToolCardV3: {e}")

    def retranslateUi(self):
        """Update all translatable text - called when language changes"""
        # Update button texts based on tool status
        if hasattr(self, 'launch_btn'):
            self.launch_btn.setText(self.tr("Launch"))
        if hasattr(self, 'install_btn'):
            self.install_btn.setText(self.tr("Install"))
        if hasattr(self, 'detail_btn'):
            self.detail_btn.setText(self.tr("Details"))
        # Redraw to refresh localized description text
        self.update()

        # Trigger repaint to update any painted text
        self.update()
