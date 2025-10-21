"""
工具卡片组件 v1.1.3
完全重构的固定尺寸卡片，使用绝对定位避免布局管理器干扰
严格控制50px×81px黄金比例尺寸，确保不被任何容器拉伸

⚠️  铁律：禁止使用 QLabel 和 QText 系列组件！
🚫 IRON RULE: NEVER USE QLabel, QTextEdit, QTextBrowser, QPlainTextEdit
✅ 替代方案: 使用 smart_text_module.py 中的智能文本组件
📋 原因: QLabel/QText 存在文字截断、字体渲染、DPI适配等问题
"""
from PyQt5.QtWidgets import QWidget, QLabel, QPushButton
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QFont, QPainter, QPen, QColor
from data.models import ToolStatus


class ToolCard(QWidget):
    """
    固定尺寸工具卡片
    严格的50px×81px黄金比例设计，使用绝对定位避免拉伸
    """
    
    # 信号定义
    install_clicked = pyqtSignal(str)
    launch_clicked = pyqtSignal(str)
    info_clicked = pyqtSignal(str)
    card_selected = pyqtSignal(str)
    
    # 固定尺寸常量
    CARD_WIDTH = 81      # 黄金比例宽度
    CARD_HEIGHT = 50     # 固定高度
    
    def __init__(self, tool_data: dict, parent=None):
        super().__init__(parent)
        self.tool_data = tool_data
        self.tool_name = tool_data['name']
        self.is_selected = False
        
        # 强制设定固定尺寸，不允许任何拉伸
        self.setFixedSize(self.CARD_WIDTH, self.CARD_HEIGHT)
        
        self.init_ui()
        self.setup_connections()
    
    def init_ui(self):
        """初始化UI，使用绝对定位"""
        self.setObjectName("ToolCard")
        self.setAttribute(Qt.WA_StyledBackground, True)
        
        # 工具名称 - 绝对定位
        self.name_label = QLabel(self.tool_name, self)
        self.name_label.setGeometry(4, 2, 73, 12)  # x, y, width, height
        self.name_label.setObjectName("ToolName")
        
        # 使用小字体适应紧凑布局
        name_font = QFont()
        name_font.setPointSize(8)
        name_font.setWeight(QFont.DemiBold)
        self.name_label.setFont(name_font)
        
        # 状态标签 - 右上角
        self.status_label = QLabel(self)
        self.status_label.setGeometry(60, 2, 17, 12)
        self._update_status_display()
        
        # 描述文本 - 中间区域，允许换行
        try:
            from utils.tool_localization import get_localized_tool_description
            base_desc = get_localized_tool_description(self.tool_data)
        except Exception:
            base_desc = self.tool_data.get('description', '')
        description = (base_desc[:40] + "...") if base_desc else ""
        self.description_label = QLabel(description, self)
        self.description_label.setGeometry(4, 16, 73, 20)
        self.description_label.setWordWrap(True)
        self.description_label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        
        desc_font = QFont()
        desc_font.setPointSize(7)
        self.description_label.setFont(desc_font)
        
        # 操作按钮 - 底部
        self._create_action_buttons()
    
    def _update_status_display(self):
        """更新状态显示"""
        status = self.tool_data['status']
        
        if status == ToolStatus.INSTALLED.value:
            self.status_label.setText("●")
            self.status_label.setStyleSheet("color: #10b981;")  # 绿色
        elif status == ToolStatus.AVAILABLE.value:
            self.status_label.setText("●")
            self.status_label.setStyleSheet("color: #6b7280;")  # 灰色
        elif status == ToolStatus.UPDATE.value:
            self.status_label.setText("●")
            self.status_label.setStyleSheet("color: #f59e0b;")  # 橙色
    
    def _create_action_buttons(self):
        """创建操作按钮，紧凑布局"""
        status = self.tool_data['status']
        
        if status == ToolStatus.INSTALLED.value:
            # 已安装：启动按钮 + 详情按钮
            self.launch_btn = QPushButton(self.tr("Launch"), self)
            self.launch_btn.setGeometry(4, 38, 30, 10)  # 紧凑按钮
            self.launch_btn.setObjectName("LaunchBtn")
            # 详情按钮
            self.info_btn = QPushButton(self.tr("Details"), self)
            self.info_btn.setGeometry(36, 38, 30, 10)
            self.info_btn.setObjectName("InfoBtn")
        
        elif status == ToolStatus.AVAILABLE.value:
            # 未安装：安装按钮 + 详情按钮
            self.install_btn = QPushButton(self.tr("Install"), self)
            self.install_btn.setGeometry(4, 38, 30, 10)
            self.install_btn.setObjectName("InstallBtn")
            # 详情按钮
            self.info_btn = QPushButton(self.tr("Details"), self)
            self.info_btn.setGeometry(36, 38, 30, 10)
            self.info_btn.setObjectName("InfoBtn")
        
        elif status == ToolStatus.UPDATE.value:
            # 需要更新：更新按钮 + 详情按钮
            self.update_btn = QPushButton(self.tr("Update"), self)
            self.update_btn.setGeometry(4, 38, 30, 10)
            self.update_btn.setObjectName("UpdateBtn")
            # 详情按钮
            self.info_btn = QPushButton(self.tr("Details"), self)
            self.info_btn.setGeometry(36, 38, 30, 10)
            self.info_btn.setObjectName("InfoBtn")
        
        # 设置按钮字体
        button_font = QFont()
        button_font.setPointSize(7)
        
        for child in self.findChildren(QPushButton):
            child.setFont(button_font)
    
    def setup_connections(self):
        """设置信号连接"""
        if hasattr(self, 'install_btn'):
            self.install_btn.clicked.connect(lambda: self.install_clicked.emit(self.tool_name))
        
        if hasattr(self, 'launch_btn'):
            self.launch_btn.clicked.connect(lambda: self.launch_clicked.emit(self.tool_name))
        
        if hasattr(self, 'update_btn'):
            self.update_btn.clicked.connect(lambda: self.install_clicked.emit(self.tool_name))
        
        if hasattr(self, 'info_btn'):
            self.info_btn.clicked.connect(lambda: self.info_clicked.emit(self.tool_name))
    
    def paintEvent(self, event):
        """自定义绘制 - 只绘制卡片本身，不清除容器背景"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 移除fillRect清除背景的代码，让容器背景显示
        
        # 只绘制卡片区域的背景和边框
        if self.is_selected:
            pen = QPen(QColor("#2563eb"), 2)
            painter.setPen(pen)
            painter.setBrush(QColor("white"))  # 只有卡片区域是白色
            painter.drawRoundedRect(1, 1, self.CARD_WIDTH-2, self.CARD_HEIGHT-2, 4, 4)
        else:
            pen = QPen(QColor("#e2e8f0"), 1)
            painter.setPen(pen)
            painter.setBrush(QColor("white"))  # 只有卡片区域是白色
            painter.drawRoundedRect(0, 0, self.CARD_WIDTH-1, self.CARD_HEIGHT-1, 3, 3)
    
    def mousePressEvent(self, event):
        """鼠标点击事件处理"""
        if event.button() == Qt.LeftButton:
            # 检查是否点击在按钮上
            for child in self.findChildren(QPushButton):
                if child.geometry().contains(event.pos()):
                    super().mousePressEvent(event)
                    return
            
            # 点击在卡片上，发出选中信号
            self.card_selected.emit(self.tool_name)
        
        super().mousePressEvent(event)
    
    def set_selected(self, selected: bool):
        """设置选中状态"""
        self.is_selected = selected
        self.update()  # 触发重绘
    
    def update_tool_status(self, new_status: str, **kwargs):
        """更新工具状态"""
        # 更新数据
        self.tool_data['status'] = new_status
        for key, value in kwargs.items():
            if key in self.tool_data:
                self.tool_data[key] = value
        
        # 更新显示
        self._update_status_display()
        
        # 重新创建按钮
        self._recreate_action_buttons()
    
    def _recreate_action_buttons(self):
        """重新创建操作按钮"""
        # 删除现有按钮
        for child in self.findChildren(QPushButton):
            child.deleteLater()
        
        # 重新创建按钮
        self._create_action_buttons()
        self.setup_connections()
    
    def set_installing_state(self, is_installing: bool, progress: int = -1, status_text: str = ""):
        """设置安装状态"""
        if is_installing:
            if hasattr(self, 'install_btn'):
                if progress >= 0:
                    self.install_btn.setText(f"{progress}%")
                elif status_text:
                    self.install_btn.setText(status_text[:4])  # 限制字符数
                else:
                    self.install_btn.setText("...")
                self.install_btn.setEnabled(False)
        else:
            # 恢复正常状态
            if hasattr(self, 'install_btn'):
                self.install_btn.setText(self.tr("Install"))
                self.install_btn.setEnabled(True)
    
    def get_tool_name(self) -> str:
        """获取工具名称"""
        return self.tool_name
    
    def get_tool_data(self) -> dict:
        """获取工具数据"""
        return self.tool_data.copy()
    
    def matches_filter(self, search_term: str = "", categories: list = None, statuses: list = None) -> bool:
        """检查是否匹配筛选条件"""
        # 搜索匹配检查
        if search_term:
            search_term = search_term.lower()
            if (search_term not in self.tool_name.lower() and 
                search_term not in self.tool_data['description'].lower()):
                return False
        
        # 分类筛选检查
        if categories and self.tool_data['category'] not in categories:
            return False
        
        # 状态筛选检查
        if statuses and self.tool_data['status'] not in statuses:
            return False
        
        return True
