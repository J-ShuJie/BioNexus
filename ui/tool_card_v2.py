"""
改进版工具卡片组件
尺寸：70×113px (黄金比例)
底部显示状态信息，使用图标和颜色区分
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFrame, QGraphicsDropShadowEffect
)
from PyQt5.QtCore import Qt, pyqtSignal, QPropertyAnimation, QRect
from PyQt5.QtGui import QFont, QFontMetrics, QPalette, QColor

class ToolCardV2(QWidget):
    """
    改进版工具卡片组件
    """
    clicked = pyqtSignal(dict)  # 点击信号，传递工具数据
    install_clicked = pyqtSignal(str)
    launch_clicked = pyqtSignal(str)
    
    def __init__(self, tool_data: dict, parent=None):
        super().__init__(parent)
        self.tool_data = tool_data
        self.is_selected = False  # 选中状态
        self.setFixedSize(170, 113)  # 70×113px基础上适当放大
        self.setCursor(Qt.PointingHandCursor)
        self.init_ui()
        self.setup_styles()
        
    def init_ui(self):
        """初始化UI布局"""
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 8, 10, 8)
        main_layout.setSpacing(0)
        
        # 1. 标题区域（加粗，12px）
        self.title_label = QLabel(self.tool_data['name'])
        title_font = QFont()
        title_font.setPointSize(11)
        title_font.setBold(True)
        self.title_label.setFont(title_font)
        self.title_label.setFixedHeight(20)
        
        # 2. 描述区域（35px高度，使用省略号）
        self.desc_label = QLabel()
        desc_font = QFont()
        desc_font.setPointSize(9)
        self.desc_label.setFont(desc_font)
        self.desc_label.setWordWrap(True)
        self.desc_label.setFixedHeight(45)
        self.desc_label.setAlignment(Qt.AlignTop)
        
        # 设置描述文本（带省略号处理）
        self._set_description_text()
        
        # 3. 底部状态栏（15px高度）
        bottom_widget = QWidget()
        bottom_widget.setFixedHeight(28)
        bottom_layout = QHBoxLayout(bottom_widget)
        bottom_layout.setContentsMargins(0, 0, 0, 0)
        bottom_layout.setSpacing(4)
        
        # 根据安装状态显示不同内容
        if self.tool_data['status'] == 'installed':
            # 已安装：显示启动按钮和内存占用
            self.status_icon = QLabel("✓")
            self.status_icon.setStyleSheet("color: #10b981; font-size: 14px;")
            
            self.launch_btn = QPushButton("启动")
            self.launch_btn.setFixedSize(45, 22)
            self.launch_btn.clicked.connect(lambda: self.launch_clicked.emit(self.tool_data['name']))
            
            self.memory_label = QLabel(f"📊{self.tool_data.get('disk_usage', 'N/A')}")
            self.memory_label.setStyleSheet("color: #64748b; font-size: 9px;")
            
            bottom_layout.addWidget(self.status_icon)
            bottom_layout.addWidget(self.launch_btn)
            bottom_layout.addWidget(self.memory_label)
            bottom_layout.addStretch()
            
        else:
            # 未安装：显示安装按钮和详情
            self.status_icon = QLabel("⬇")
            self.status_icon.setStyleSheet("color: #94a3b8; font-size: 14px;")
            
            self.install_btn = QPushButton("安装")
            self.install_btn.setFixedSize(45, 22)
            self.install_btn.clicked.connect(lambda: self.install_clicked.emit(self.tool_data['name']))
            
            self.detail_btn = QPushButton("详情")
            self.detail_btn.setFixedSize(40, 22)
            self.detail_btn.clicked.connect(self._on_detail_clicked)
            
            bottom_layout.addWidget(self.status_icon)
            bottom_layout.addWidget(self.install_btn)
            bottom_layout.addWidget(self.detail_btn)
            bottom_layout.addStretch()
        
        # 添加到主布局
        main_layout.addWidget(self.title_label)
        main_layout.addWidget(self.desc_label)
        main_layout.addStretch()
        main_layout.addWidget(bottom_widget)
        
    def _set_description_text(self):
        """设置描述文本，使用省略号处理"""
        description = self.tool_data.get('description', '')
        
        # 使用QFontMetrics计算文本
        metrics = QFontMetrics(self.desc_label.font())
        available_width = self.width() - 20  # 减去边距
        
        # 计算两行能显示的文本
        words = description.split()
        lines = []
        current_line = ""
        
        for word in words:
            test_line = current_line + " " + word if current_line else word
            if metrics.horizontalAdvance(test_line) <= available_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
                if len(lines) >= 2:
                    break
        
        if current_line and len(lines) < 2:
            lines.append(current_line)
        
        # 如果超过两行，第二行加省略号
        if len(lines) >= 2 and len(words) > len(' '.join(lines[:2]).split()):
            # 确保第二行能容纳省略号
            second_line = lines[1]
            while metrics.horizontalAdvance(second_line + "...") > available_width and len(second_line) > 0:
                second_line = second_line[:-1]
            lines[1] = second_line + "..."
        
        self.desc_label.setText('\n'.join(lines[:2]))
        
    def setup_styles(self):
        """设置样式"""
        self.setStyleSheet("""
            ToolCardV2 {
                background-color: white;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
            }
            ToolCardV2:hover {
                border: 1px solid #cbd5e1;
                background-color: #f8fafc;
            }
            QPushButton {
                background-color: #3b82f6;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 9px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #2563eb;
            }
            QPushButton#install {
                background-color: #10b981;
            }
            QPushButton#install:hover {
                background-color: #059669;
            }
        """)
        
        # 添加阴影效果
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(8)
        shadow.setColor(QColor(0, 0, 0, 30))
        shadow.setOffset(0, 2)
        self.setGraphicsEffect(shadow)
        
    def _on_detail_clicked(self):
        """详情按钮点击处理"""
        self.clicked.emit(self.tool_data)
    
    def set_installing_state(self, is_installing: bool, progress: int = -1, status_text: str = ""):
        """设置安装状态（兼容性方法）"""
        if is_installing:
            if hasattr(self, 'install_btn'):
                if progress >= 0:
                    self.install_btn.setText(f"{progress}%")
                elif status_text:
                    # 限制文本长度以适应按钮
                    display_text = status_text[:6] if len(status_text) > 6 else status_text
                    self.install_btn.setText(display_text)
                else:
                    self.install_btn.setText("...")
                self.install_btn.setEnabled(False)
        else:
            # 恢复正常状态
            if hasattr(self, 'install_btn'):
                self.install_btn.setText("安装")
                self.install_btn.setEnabled(True)
        
    def mousePressEvent(self, event):
        """鼠标点击事件"""
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.tool_data)
        super().mousePressEvent(event)
        
    def enterEvent(self, event):
        """鼠标进入事件"""
        # 可以添加动画效果
        super().enterEvent(event)
        
    def leaveEvent(self, event):
        """鼠标离开事件"""
        # 可以添加动画效果
        super().leaveEvent(event)
    
    def set_selected(self, selected: bool):
        """设置选中状态"""
        self.is_selected = selected
        if selected:
            # 选中状态样式
            self.setStyleSheet("""
                QWidget {
                    border: 2px solid #3b82f6;
                    background-color: #eff6ff;
                }
            """)
        else:
            # 非选中状态样式
            self.setStyleSheet("""
                QWidget {
                    border: 1px solid #e2e8f0;
                    background-color: white;
                }
            """)