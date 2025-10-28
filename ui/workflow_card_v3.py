from PyQt5.QtWidgets import QWidget, QPushButton
from PyQt5.QtCore import Qt, pyqtSignal, QRect
from PyQt5.QtGui import QPainter, QPen, QColor, QFont

from .tool_card_v3 import ToolCardV3


class WorkflowCardV3(ToolCardV3):
    """复用 ToolCardV3 的外观，用于展示工作流卡片。
    - 顶部标题 = 工作流名称（无收藏星标）
    - 描述 = “X 个工具”
    - 底部按钮：打开、菜单（…）
    """
    open_requested = pyqtSignal(str)     # workflow_id
    rename_requested = pyqtSignal(str)
    duplicate_requested = pyqtSignal(str)
    delete_requested = pyqtSignal(str)

    def __init__(self, workflow: dict, parent=None):
        self.workflow = workflow
        # 构造伪 tool_data，保证基类正常工作（绘制背景、布局等）
        tool_data = {
            'name': workflow.get('name', '未命名工作流'),
            'description': f"{len(workflow.get('tools', []))} 个工具",
            'status': 'installed',
            'category': 'workflow',
            'install_source': 'none',
        }
        super().__init__(tool_data, parent)
        # 替换底部按钮
        self._replace_buttons()

    # 禁用收藏星标绘制：重写标题栏绘制，仅绘制标题文本
    def _draw_title_bar(self, painter):
        title_font = QFont(); title_font.setPointSize(11); title_font.setBold(True)
        painter.setFont(title_font)
        painter.setPen(QColor("#1f2937"))
        title_rect = QRect(self.PADDING, 8, self.width() - 2 * self.PADDING, self.TITLE_HEIGHT)
        from PyQt5.QtGui import QFontMetrics
        metrics = QFontMetrics(title_font)
        elided = metrics.elidedText(self.tool_data['name'], Qt.ElideRight, title_rect.width())
        painter.drawText(title_rect, Qt.AlignLeft | Qt.AlignVCenter, elided)

    # 描述改为一行“X 个工具”
    def _draw_description(self, painter):
        desc_font = QFont(); desc_font.setPointSize(9)
        painter.setFont(desc_font)
        painter.setPen(QColor("#6b7280"))
        y = 8 + self.TITLE_HEIGHT + 4
        painter.drawText(QRect(self.PADDING, y, self.width() - 2 * self.PADDING, 18),
                         Qt.AlignLeft | Qt.AlignVCenter,
                         self.tool_data.get('description', ''))

    # 底部状态指示不需要
    def _draw_status_indicator(self, painter):
        return

    def _replace_buttons(self):
        # 隐藏基类按钮
        for name in ('launch_btn', 'install_btn', 'detail_btn'):
            btn = getattr(self, name, None)
            if btn:
                btn.hide(); btn.setParent(None); del btn
                setattr(self, name, None)
        # 放置“打开”和“⋯”按钮
        button_y = self.CARD_HEIGHT - self.BUTTON_HEIGHT - 8
        button_spacing = 5
        total_width = self.CARD_WIDTH - 2 * self.PADDING
        button_width = (total_width - button_spacing) // 2

        self.open_btn = QPushButton(self.tr("打开"), self)
        self.open_btn.setGeometry(self.PADDING, button_y, button_width, self.BUTTON_HEIGHT)
        self._style_button(self.open_btn, "primary")
        self.open_btn.clicked.connect(lambda: self.open_requested.emit(self.workflow['id']))

        self.menu_btn = QPushButton("⋯", self)
        self.menu_btn.setGeometry(self.PADDING + button_width + button_spacing, button_y, button_width, self.BUTTON_HEIGHT)
        self._style_button(self.menu_btn, "secondary")
        self.menu_btn.clicked.connect(self._show_menu)

    def _show_menu(self):
        from PyQt5.QtWidgets import QMenu
        m = QMenu(self)
        a1 = m.addAction(self.tr("重命名"))
        a2 = m.addAction(self.tr("复制"))
        a3 = m.addAction(self.tr("删除"))
        act = m.exec(self.menu_btn.mapToGlobal(self.menu_btn.rect().bottomLeft()))
        if act == a1:
            self.rename_requested.emit(self.workflow['id'])
        elif act == a2:
            self.duplicate_requested.emit(self.workflow['id'])
        elif act == a3:
            self.delete_requested.emit(self.workflow['id'])

    def mousePressEvent(self, e):
        # 整卡可点击打开详情
        if e.button() == Qt.LeftButton:
            try:
                self.open_requested.emit(self.workflow['id'])
            except Exception:
                pass
        super().mousePressEvent(e)


class NewWorkflowPlusCardV3(ToolCardV3):
    create_requested = pyqtSignal()

    def __init__(self, parent=None):
        tool_data = {
            'name': '',
            'description': '',
            'status': 'installed',
            'category': 'workflow',
            'install_source': 'none',
        }
        super().__init__(tool_data, parent)
        # 去除底部按钮
        for name in ('launch_btn', 'install_btn', 'detail_btn'):
            btn = getattr(self, name, None)
            if btn:
                btn.hide(); btn.setParent(None); del btn
                setattr(self, name, None)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        # 只绘制背景与加号
        self._draw_background(painter)
        # 加号
        center = self.rect().center()
        size = 36
        plus_pen = QPen(QColor("#2563eb")); plus_pen.setWidth(4)
        painter.setPen(plus_pen)
        painter.drawLine(center.x() - size//2, center.y(), center.x() + size//2, center.y())
        painter.drawLine(center.x(), center.y() - size//2, center.x(), center.y() + size//2)

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self.create_requested.emit()
        super().mousePressEvent(e)


class WorkflowToolItemCardV3(ToolCardV3):
    remove_clicked = pyqtSignal(int)
    move_up_clicked = pyqtSignal(int)
    move_down_clicked = pyqtSignal(int)

    def __init__(self, tool_data: dict, index: int, edit_mode: bool = False, parent=None):
        # 直接使用真实工具数据，保持外观一致
        super().__init__(tool_data, parent)
        self.index = index
        self.edit_mode = edit_mode
        self._replace_buttons()

    def _replace_buttons(self):
        # 替换底部按钮为“移除/详情”，并在编辑模式下显示↑↓
        for name in ('launch_btn', 'install_btn'):
            btn = getattr(self, name, None)
            if btn:
                btn.hide(); btn.setParent(None); del btn
                setattr(self, name, None)

        # 移除按钮（危险色）
        self.remove_btn = QPushButton(self.tr("移除"), self)
        button_y = self.CARD_HEIGHT - self.BUTTON_HEIGHT - 8
        button_spacing = 5
        total_width = self.CARD_WIDTH - 2 * self.PADDING
        button_width = (total_width - button_spacing) // 2
        self.remove_btn.setGeometry(self.PADDING, button_y, button_width, self.BUTTON_HEIGHT)
        self.remove_btn.setStyleSheet("""
            QPushButton { background-color: #fee2e2; color: #b91c1c; border: 1px solid #fecaca; border-radius: 4px; font-size: 11px; font-weight: 500; }
            QPushButton:hover { background-color: #fecaca; }
            QPushButton:pressed { background-color: #fca5a5; }
        """)
        self.remove_btn.clicked.connect(lambda: self.remove_clicked.emit(self.index))

        # 详情按钮保留
        if hasattr(self, 'detail_btn') and self.detail_btn:
            self.detail_btn.setGeometry(self.PADDING + button_width + button_spacing, button_y, button_width, self.BUTTON_HEIGHT)

        if self.edit_mode:
            # 在右上角放置小型箭头按钮
            self.up_btn = QPushButton("↑", self)
            self.up_btn.setGeometry(self.width() - 42, 6, 18, 18)
            self.up_btn.setStyleSheet("QPushButton{background:#f3f4f6;border:1px solid #d1d5db;border-radius:3px;font-size:10px;}")
            self.up_btn.clicked.connect(lambda: self.move_up_clicked.emit(self.index))
            self.down_btn = QPushButton("↓", self)
            self.down_btn.setGeometry(self.width() - 22, 6, 18, 18)
            self.down_btn.setStyleSheet("QPushButton{background:#f3f4f6;border:1px solid #d1d5db;border-radius:3px;font-size:10px;}")
            self.down_btn.clicked.connect(lambda: self.move_down_clicked.emit(self.index))
