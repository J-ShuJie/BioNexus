from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPainter, QFont, QPen, QColor
from .card_grid_container import CardScrollArea
from .workflow_card_v3 import WorkflowToolItemCardV3, NewWorkflowPlusCardV3
from .tool_card_v3 import ToolCardV3


class ToolEntryCard(QWidget):
    remove_clicked = pyqtSignal(int)   # index
    move_up_clicked = pyqtSignal(int)
    move_down_clicked = pyqtSignal(int)

    def __init__(self, index: int, tool_name: str, edit_mode: bool = False, parent=None):
        super().__init__(parent)
        self.index = index
        self.tool_name = tool_name
        self.edit_mode = edit_mode
        # 使用工具卡尺寸
        self.CARD_WIDTH = 170
        self.CARD_HEIGHT = 113
        self.BORDER_RADIUS = 8
        self.setFixedSize(self.CARD_WIDTH, self.CARD_HEIGHT)
        self.setStyleSheet("""
            QWidget { background: transparent; }
            QPushButton#Remove { background: #fee2e2; color: #b91c1c; border: 1px solid #fecaca; border-radius: 4px; padding: 2px 6px; }
            QPushButton#Arrow { background: #f3f4f6; color: #374151; border: 1px solid #d1d5db; border-radius: 4px; padding: 2px 6px; }
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(6)
        # 文本由 paintEvent 绘制
        layout.addStretch()
        row = QHBoxLayout()
        rm = QPushButton("移除")
        rm.setObjectName("Remove")
        rm.clicked.connect(lambda: self.remove_clicked.emit(self.index))
        row.addWidget(rm)
        row.addStretch()
        if self.edit_mode:
            up = QPushButton("↑")
            up.setObjectName("Arrow")
            up.clicked.connect(lambda: self.move_up_clicked.emit(self.index))
            down = QPushButton("↓")
            down.setObjectName("Arrow")
            down.clicked.connect(lambda: self.move_down_clicked.emit(self.index))
            row.addWidget(up)
            row.addWidget(down)
        layout.addLayout(row)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        # 背景与边框
        from PyQt5.QtGui import QPainterPath
        path = QPainterPath()
        rect = self.rect().adjusted(1, 1, -1, -1)
        path.addRoundedRect(rect, self.BORDER_RADIUS, self.BORDER_RADIUS)
        painter.fillPath(path, QColor("#ffffff"))
        pen = QPen(QColor("#e5e7eb")); pen.setWidth(1)
        painter.setPen(pen)
        painter.drawPath(path)
        font = QFont(); font.setPointSize(13); font.setBold(True)
        painter.setFont(font)
        painter.setPen(QPen(QColor("#111827")))
        painter.drawText(12, 24, self.tool_name)


class AddToolCard(QWidget):
    add_requested = pyqtSignal()
    def __init__(self, parent=None):
        super().__init__(parent)
        # 使用工具卡尺寸
        self.CARD_WIDTH = 170
        self.CARD_HEIGHT = 113
        self.BORDER_RADIUS = 8
        self.setFixedSize(self.CARD_WIDTH, self.CARD_HEIGHT)
        self.setMouseTracking(True)
        self._hover = False
        self.setStyleSheet("""
            QWidget { background: transparent; }
            QPushButton { background: transparent; color: #2563eb; border: none; font-size: 14px; }
            QPushButton:hover { color: #1d4ed8; }
        """)
        from PyQt5.QtGui import QFont
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(6)
        layout.addStretch()
        btn = QPushButton("添加工具")
        btn.clicked.connect(self.add_requested.emit)
        layout.addWidget(btn, alignment=Qt.AlignCenter)
        layout.addStretch()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        # 背景与边框
        from PyQt5.QtGui import QPainterPath
        path = QPainterPath()
        rect = self.rect().adjusted(1, 1, -1, -1)
        path.addRoundedRect(rect, self.BORDER_RADIUS, self.BORDER_RADIUS)
        from PyQt5.QtCore import Qt
        painter.fillPath(path, QColor("#f8fafc") if self._hover else QColor("#ffffff"))
        pen = QPen(QColor("#e5e7eb")); pen.setWidth(1)
        painter.setPen(pen)
        painter.drawPath(path)
        # 画“＋”线段
        center = self.rect().center()
        size = 36
        plus_pen = QPen(QColor("#2563eb")); plus_pen.setWidth(4)
        painter.setPen(plus_pen)
        painter.drawLine(center.x() - size//2, center.y(), center.x() + size//2, center.y())
        painter.drawLine(center.x(), center.y() - size//2, center.x(), center.y() + size//2)

    def enterEvent(self, e):
        self._hover = True
        self.update()

    def leaveEvent(self, e):
        self._hover = False
        self.update()

class TitleText(QWidget):
    # 保留占位（当前不使用本地顶部栏）
    def __init__(self, text: str = "", parent=None):
        super().__init__(parent)
        self.setFixedHeight(0)
    def set_text(self, text: str):
        pass
    def paintEvent(self, event):
        pass


class WorkflowsDetailView(QWidget):
    back_requested = pyqtSignal()
    add_tool_requested = pyqtSignal()
    remove_tool_requested = pyqtSignal(int)
    move_up_requested = pyqtSignal(int)
    move_down_requested = pyqtSignal(int)
    tool_detail_requested = pyqtSignal(str)  # 打开工具详情（工具名）

    def __init__(self, parent=None):
        super().__init__(parent)
        self.workflow_id = None
        self.workflow_name = ""
        self.tools: list = []
        self.edit_mode = False  # 工具管理模式（开启后默认点击=删除）

        outer = QVBoxLayout(self)
        # 与“全部工具/工作流列表”统一：外层边距与间距为0，避免出现白色边框感
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # 本地顶部栏已移除，统一使用全局ModernToolbar承载返回与动作

        # 卡片区域：与“全部工具”一致的网格
        self.cards = CardScrollArea()
        outer.addWidget(self.cards)

    def set_workflow(self, workflow_id: str, name: str, tools: list):
        self.workflow_id = workflow_id
        self.workflow_name = name
        self.tools = tools[:]  # list of ToolRef-like dicts or objects
        # 标题由全局工具栏负责
        self.refresh()

    def _on_edit_toggled(self, checked: bool):
        self.set_edit_mode(checked)

    def set_edit_mode(self, checked: bool):
        self.edit_mode = bool(checked)
        self.refresh()

    def refresh(self):
        gc = self.cards.grid_container
        for card in getattr(gc, 'cards', [])[:]:
            card.deleteLater()
        gc.cards = []

        # 工具卡（先放工具，再把“添加工具(＋)”放到最后）
        for idx, t in enumerate(self.tools):
            tool_name = t.tool_name if hasattr(t, 'tool_name') else t.get('tool_name')
            # 获取 tool_data（优先从 ToolManager，保证状态准确；大小写不敏感匹配）
            tool_data = None
            try:
                from PyQt5.QtWidgets import QApplication
                mw = QApplication.instance().activeWindow()
                if mw and hasattr(mw, 'tool_manager') and mw.tool_manager:
                    td = mw.tool_manager.get_tool_info(tool_name)
                    if not td:
                        # 尝试大小写不敏感匹配
                        all_td = mw.tool_manager.get_all_tools_data()
                        for it in all_td:
                            if it.get('name','').lower() == (tool_name or '').lower():
                                td = it
                                break
                    if td:
                        tool_data = dict(td)
                # 回退到 config_manager.tools（不可靠，仅作为兜底）
                if (tool_data is None) and hasattr(mw, 'config_manager'):
                    for td in mw.config_manager.tools:
                        if td.get('name','').lower() == (tool_name or '').lower():
                            tool_data = dict(td)
                            break
            except Exception:
                tool_data = None
            if tool_data is None:
                tool_data = {'name': tool_name, 'description': '', 'status': 'available', 'category': 'sequence'}
            # 不再二次覆盖status，保持与tool_manager.get_tool_info一致（与“全部工具”完全同步）

            if self.edit_mode:
                # 管理模式：使用带删除/排序的工作流卡片
                card = WorkflowToolItemCardV3(tool_data, idx, edit_mode=True, parent=gc)
                card.remove_clicked.connect(self.remove_tool_requested.emit)
                card.move_up_clicked.connect(self.move_up_requested.emit)
                card.move_down_clicked.connect(self.move_down_requested.emit)
                try:
                    card.clicked.connect(lambda td, i=idx: self.remove_tool_requested.emit(i))
                except Exception:
                    pass
            else:
                # 非管理模式：使用标准工具卡片，行为与“全部工具”一致
                card = ToolCardV3(tool_data, gc)
                # 向上转发安装/启动/点击事件，交由主窗口统一处理
                try:
                    card.install_clicked.connect(self.cards.card_install_clicked.emit)
                except Exception:
                    pass
                try:
                    card.launch_clicked.connect(self.cards.card_launch_clicked.emit)
                except Exception:
                    pass
                try:
                    card.clicked.connect(lambda td, tn=tool_name: self.tool_detail_requested.emit(tn))
                except Exception:
                    pass
                # 非管理模式：保留与“全部工具”一致的按钮（安装/启动/详情）
            gc.cards.append(card)
            card.show()

        # 添加“＋”卡（排在末尾）
        plus = NewWorkflowPlusCardV3(gc)
        plus.create_requested.connect(self.add_tool_requested.emit)
        gc.cards.append(plus)
        plus.show()

        gc._relayout_cards()
