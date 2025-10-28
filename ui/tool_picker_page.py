from PyQt5.QtWidgets import QWidget, QVBoxLayout
from PyQt5.QtCore import pyqtSignal

from .card_grid_container import CardScrollArea


class ToolPickerPage(QWidget):
    """
    内嵌的工具选择页（替代对话框），复用工具卡网格与搜索。
    - 进入“添加模式”，将卡片底部按钮与启动/安装行为重定向为“添加”。
    - 外部通过 tool_selected 信号接收选择结果。
    - 支持过滤（通过 filter_cards 暴露调用）。
    """
    tool_selected = pyqtSignal(str)
    detail_requested = pyqtSignal(str)

    def __init__(self, config_manager, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 卡片网格
        self.cards = CardScrollArea()
        layout.addWidget(self.cards)

        # 加载数据并进入添加模式
        self._load_tools()
        self._enter_add_mode()

    def _load_tools(self):
        tools = self.config_manager.tools or []
        safe_tools = []
        for t in tools:
            td = dict(t)
            td.setdefault('description', '暂无详细介绍')
            td.setdefault('status', t.get('status', 'available'))
            td.setdefault('category', t.get('category', 'sequence'))
            safe_tools.append(td)
        self.cards.set_cards(safe_tools)

    def _enter_add_mode(self):
        # 将卡片底部按钮改为“添加”；点击卡片主按钮即选择
        gc = self.cards.grid_container
        for card in getattr(gc, 'cards', []):
            tool_name = card.tool_data.get('name')

            def connect_as_add(btn):
                try:
                    try:
                        btn.clicked.disconnect()
                    except Exception:
                        pass
                    btn.setText(self.tr("添加"))
                    btn.clicked.connect(lambda _, tn=tool_name: self._emit_selected(tn))
                    btn.setEnabled(True)
                except Exception:
                    pass

            if hasattr(card, 'launch_btn') and card.launch_btn:
                connect_as_add(card.launch_btn)
            if hasattr(card, 'install_btn') and card.install_btn:
                connect_as_add(card.install_btn)

        # 覆盖容器层的信号
        try:
            self.cards.card_launch_clicked.disconnect()
        except Exception:
            pass
        self.cards.card_launch_clicked.connect(self._emit_selected)
        try:
            self.cards.card_install_clicked.disconnect()
        except Exception:
            pass
        self.cards.card_install_clicked.connect(self._emit_selected)
        # 卡片点击（或“详情”按钮）→ 请求详情
        try:
            self.cards.card_selected.disconnect()
        except Exception:
            pass
        self.cards.card_selected.connect(self._on_card_selected)

    def _emit_selected(self, tool_name: str):
        if tool_name:
            self.tool_selected.emit(tool_name)

    def filter_cards(self, search_term: str = "", categories=None, statuses=None):
        self.cards.filter_cards(search_term, categories or [], statuses or [])

    def _on_card_selected(self, tool_name: str):
        if tool_name:
            self.detail_requested.emit(tool_name)
