from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QLabel
from PyQt5.QtCore import Qt, pyqtSignal

from .card_grid_container import CardScrollArea


class ToolPickerDialog(QDialog):
    tool_selected = pyqtSignal(str)

    def __init__(self, config_manager, parent=None):
        super().__init__(parent)
        self.setWindowTitle(self.tr("选择工具"))
        self.resize(800, 520)
        self.config_manager = config_manager

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        # 顶部搜索
        top = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(self.tr("搜索工具..."))
        self.search_input.textChanged.connect(self._on_search)
        top.addWidget(self.search_input)
        layout.addLayout(top)

        # 卡片网格
        self.cards = CardScrollArea()
        layout.addWidget(self.cards)

        # 加载工具
        self._load_tools()
        # 进入添加模式
        self._enter_add_mode()

    def _load_tools(self):
        tools = self.config_manager.tools or []
        # 确保字段完整（卡片组件依赖）
        safe_tools = []
        for t in tools:
            td = dict(t)
            td.setdefault('description', '暂无详细介绍')
            td.setdefault('status', t.get('status', 'available'))
            td.setdefault('category', t.get('category', 'sequence'))
            safe_tools.append(td)
        self.cards.set_cards(safe_tools)

    def _enter_add_mode(self):
        # 将卡片底部按钮的行为改为“添加”
        gc = self.cards.grid_container
        for card in getattr(gc, 'cards', []):
            tool_name = card.tool_data.get('name')
            # 优先复用已有按钮，改文案并重连
            def connect_as_add(btn):
                try:
                    try:
                        btn.clicked.disconnect()
                    except Exception:
                        pass
                    btn.setText(self.tr("添加"))
                    btn.clicked.connect(lambda tn=tool_name: self._emit_selected(tn))
                    btn.setEnabled(True)
                except Exception:
                    pass

            if hasattr(card, 'launch_btn') and card.launch_btn:
                connect_as_add(card.launch_btn)
            if hasattr(card, 'install_btn') and card.install_btn:
                connect_as_add(card.install_btn)
            # 详情按钮保持不变

        # 替换容器层的信号（防止误触发启动/安装）
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

    def _emit_selected(self, tool_name: str):
        if tool_name:
            self.tool_selected.emit(tool_name)

    def _on_search(self, text: str):
        self.cards.filter_cards(text.lower().strip(), [], [])

